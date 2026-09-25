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


class SignalRules:
    def __init__(self, scene):
        self.scene = scene
        self.colors = {}
        self.previous = {}
        self.crossings = {}
        self.running = {}
        self.stopped = {}

    def step(self, tracks, t, frame=None):
        if frame is None:
            return []
        flags = []
        for signal in self.scene.config.get("signals", []):
            if not signal.get("verified"):
                continue
            sid = signal["id"]
            color = signal_color(
                self.scene.crop(frame, signal["roi"]),
                min_saturation=signal.get("min_saturation", 130),
                min_value=signal.get("min_value", 120),
            )
            before, since = self.colors.get(sid, (color, t))
            if color != before:
                since = t
            self.colors[sid] = (color, since)
            for key, state in list(self.stopped.items()):
                if key[0] != sid:
                    continue
                flags.append(
                    Flag(
                        "stop_line",
                        str(key),
                        state["start"],
                        state["score"],
                        sid,
                        "Stopped beyond the verified stop line; ends on the governing green.",
                        end=t if color == "green" else None,
                    )
                )
                if color == "green":
                    self.stopped.pop(key)
                    self.crossings.pop(key, None)
            for track in tracks:
                obs = track.observation
                if obs.kind not in VEHICLES:
                    continue
                key = (sid, obs.id)
                fx, fy = signal.get("front", [0.5, 1.0])
                x1, y1, x2, y2 = obs.box
                point = self.scene.point((x1 + (x2 - x1) * fx, y1 + (y2 - y1) * fy))
                prior = self.previous.get(key)
                self.previous[key] = (point, t)
                governed = (
                    key in self.running
                    or inside(point, signal["approach"])
                    or inside(point, signal["beyond_line"])
                    or inside(point, signal["intersection"])
                )
                if not governed:
                    continue
                if prior and t - prior[1] < 0.6 and color == "red" and t - since >= 0.2:
                    if (
                        crossed(prior[0], point, signal["stop_line"])
                        and line_side(point, signal["stop_line"])
                        * signal.get("entry_side", 1)
                        > 0
                    ):
                        self.crossings[key] = {
                            "start": prior[1],
                            "last": t,
                            "score": obs.score,
                        }
                if key in self.crossings:
                    self.crossings[key]["last"] = t
                    if inside(point, signal["intersection"]):
                        self.running.setdefault(key, self.crossings[key])
                    elif (
                        color == "red"
                        and track.stopped_since is not None
                        and inside(point, signal["beyond_line"])
                    ):
                        self.stopped.setdefault(
                            key, {"start": track.stopped_since, "score": obs.score}
                        )
                if (
                    color == "red"
                    and t - since >= 0.2
                    and track.stopped_since is not None
                    and inside(point, signal["beyond_line"])
                    and not inside(point, signal["intersection"])
                    and key not in self.stopped
                ):
                    self.stopped[key] = {
                        "start": track.stopped_since,
                        "score": obs.score,
                    }
                    flags.append(
                        Flag("stop_line", str(key), track.stopped_since, obs.score, sid)
                    )
                if key in self.running:
                    state = self.running[key]
                    state["last"] = t
                    outside = not inside(point, signal["intersection"]) and not inside(
                        point, signal["beyond_line"]
                    )
                    flags.append(
                        Flag(
                            "red_light",
                            str(key),
                            state["start"],
                            obs.score,
                            sid,
                            "Front crossed the governing red stop line and continued into the intersection.",
                            end=t if outside else None,
                        )
                    )
                    if outside:
                        self.running.pop(key)
                        self.crossings.pop(key, None)
            for key, state in list(self.running.items()):
                if key[0] == sid and t - state["last"] > 1:
                    flags.append(
                        Flag(
                            "red_light",
                            str(key),
                            state["start"],
                            state["score"],
                            sid,
                            end=state["last"],
                        )
                    )
                    self.running.pop(key)
                    self.crossings.pop(key, None)
        for key, (_, last) in list(self.previous.items()):
            if t - last > 2:
                self.previous.pop(key)
                if key not in self.running:
                    self.crossings.pop(key, None)
        return flags
