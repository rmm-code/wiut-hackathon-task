import math
import cv2
from ..geometry import crossed, inside, line_side
from ..types import Flag, VEHICLES


def signal_color(frame, roi=None, min_saturation=130, min_value=120):
    if roi is not None:
        h, w = frame.shape[:2]
        x1, y1, x2, y2 = roi
        frame = frame[
            max(0, int(y1 * h)) : min(h, int(y2 * h)),
            max(0, int(x1 * w)) : min(w, int(x2 * w)),
        ]
    if frame.size < 9:
        return "unknown"
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    valid = (hsv[:, :, 1] > min_saturation) & (hsv[:, :, 2] > min_value)
    hue = hsv[:, :, 0]
    red = int((((hue < 12) | (hue > 165)) & valid).sum())
    green = int(((hue > 35) & (hue < 95) & valid).sum())
    if max(red, green) < max(3, frame.shape[0] * frame.shape[1] * 0.01):
        return "unknown"
    return "red" if red > green * 1.5 else "green" if green > red * 1.5 else "unknown"


class Lamp:
    """Debounced lamp state.

    `unknown` readings (amber, glare, occlusion) keep the last state. A change needs
    `hold` readings of the new colour, or one reading left uncontradicted for 1 s,
    so a single misread frame between readings of the current colour is ignored.
    """

    def __init__(self, hold=3):
        self.state, self.since, self.hold = None, None, hold
        self.candidate, self.count, self.first = None, 0, None

    def update(self, color, t):
        if color == self.state:
            self.candidate = None
        elif color in ("red", "green"):
            if color != self.candidate:
                self.candidate, self.count, self.first = color, 0, t
            self.count += 1
        if self.candidate and (
            self.state is None or self.count >= self.hold or t - self.first >= 1.0
        ):
            # Confirmed by repeated readings, or uncontradicted while the head is occluded.
            self.state, self.since, self.candidate = self.candidate, self.first, None
        return self.state

    def red_for(self, t):
        return t - self.since if self.state == "red" else -1.0


class SignalRules:
    """Red-light running and stop-line violations for verified signal mappings.

    A red-light event needs the vehicle front to cross the stop line after the lamp has
    been red for `min_red` s and then enter the junction; it is confirmed only if the
    lamp is still red `confirm` s after the crossing, which excludes amber clearance and
    anticipatory starts on red+amber. It starts at the crossing and ends when the
    vehicle leaves the junction. A vehicle that creeps over the line and stops is a
    stop-line case instead. A stop-line
    event needs a stationary vehicle whose front is at least `overshoot` box heights
    past the line during red; it starts when the vehicle stops and ends on green.
    """

    def __init__(self, scene):
        self.scene = scene
        self.lamps = {}
        self.previous = {}
        self.pending = {}
        self.running = {}
        self.stopped = {}

    def front(self, signal, box):
        fx, fy = signal.get("front", [0.5, 1.0])
        x1, y1, x2, y2 = box
        return self.scene.point((x1 + (x2 - x1) * fx, y1 + (y2 - y1) * fy))

    def overshoot(self, signal, box):
        """Signed distance of the front past the stop line, in box heights."""
        x1, y1, x2, y2 = box
        bottom = self.scene.point(((x1 + x2) / 2, y2))
        top = self.scene.point(((x1 + x2) / 2, y1))
        a, b = signal["stop_line"]
        side = line_side(bottom, signal["stop_line"]) * signal.get("entry_side", 1)
        return side / max(math.dist(a, b), 1e-9) / max(math.dist(bottom, top), 1e-9)

    def step(self, tracks, t, frame=None):
        if frame is None:
            return []
        flags = []
        for signal in self.scene.config.get("signals", []):
            if signal.get("verified"):
                flags.extend(self._signal(signal, tracks, t, frame))
        for key, (_, last) in list(self.previous.items()):
            if t - last > 2:
                self.previous.pop(key)
        return flags

    def _signal(self, signal, tracks, t, frame):
        sid = signal["id"]
        lamp = self.lamps.setdefault(sid, Lamp())
        color = signal_color(
            self.scene.crop(frame, signal["roi"]),
            min_saturation=signal.get("min_saturation", 130),
            min_value=signal.get("min_value", 120),
        )
        state = lamp.update(color, t)
        min_red, confirm = signal.get("min_red", 1.0), signal.get("confirm", 1.5)
        flags = []
        seen = set()
        for track in tracks:
            obs = track.observation
            if obs.kind not in VEHICLES or obs.kind == "bicycle":
                continue
            key = (sid, obs.id)
            seen.add(key)
            point = self.front(signal, obs.box)
            prior = self.previous.get(key)
            self.previous[key] = (point, t)
            if (
                prior
                and t - prior[1] < 0.6
                and key not in self.running
                and lamp.red_for(t) >= min_red
                and crossed(prior[0], point, signal["stop_line"])
                and line_side(point, signal["stop_line"]) * signal.get("entry_side", 1) > 0
            ):
                self.pending[key] = {"start": prior[1], "confirm": t + confirm, "score": obs.score}
            if key in self.pending and inside(point, signal["intersection"]):
                self.pending[key]["entered"] = True
            if (
                key in self.pending
                and t >= self.pending[key]["confirm"]
                and self.pending[key].get("entered")
            ):
                self.running[key] = self.pending.pop(key)
            if key in self.running:
                state_ = self.running[key]
                state_["last"] = t
                outside = not inside(point, signal["intersection"]) and not inside(
                    point, signal["beyond_line"]
                )
                flags.append(
                    Flag(
                        "red_light",
                        str(key),
                        state_["start"],
                        state_["score"],
                        sid,
                        "Front crossed the stop line after the lamp had been red; the lamp stayed red afterwards.",
                        end=t if outside else None,
                    )
                )
                if outside:
                    self.running.pop(key)
            if (
                state == "red"
                and track.stopped_since is not None
                and key not in self.stopped
                and inside(point, signal["beyond_line"])
                and self.overshoot(signal, obs.box) >= signal.get("overshoot", 0.35)
            ):
                self.stopped[key] = {
                    "start": max(track.stopped_since, lamp.since),
                    "score": obs.score,
                }
        if "green" in (state, color):
            # Amber clearance or an anticipatory start: never confirmed.
            for key in [k for k in self.pending if k[0] == sid]:
                self.pending.pop(key)
        for key, pending in list(self.pending.items()):
            # Unseen for long, or never entered the junction: a stop-line case, not a red-light run.
            if key[0] == sid and (
                (key not in seen and t - pending["start"] > 2)
                or (not pending.get("entered") and t - pending["start"] > 6)
            ):
                self.pending.pop(key)
        for key, running in list(self.running.items()):
            if key[0] == sid and key not in seen and t - running["last"] > 1:
                flags.append(
                    Flag("red_light", str(key), running["start"], running["score"], sid, end=running["last"])
                )
                self.running.pop(key)
        for key, stopped in list(self.stopped.items()):
            if key[0] != sid:
                continue
            flags.append(
                Flag(
                    "stop_line",
                    str(key),
                    stopped["start"],
                    stopped["score"],
                    sid,
                    "Stopped with its front past the stop line during red; ends on green.",
                    end=lamp.since if state == "green" else None,
                )
            )
            if state == "green":
                self.stopped.pop(key)
        return flags
