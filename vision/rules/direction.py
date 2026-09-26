import math
from ..geometry import cosine, inside
from ..types import Flag
from .signals import Lamp, signal_color


class DirectionRules:
    """Wrong-way driving and congestion on verified carriageways.

    Wrong way: during the last `window` s the vehicle stayed inside one carriageway and
    travelled at least `distance` box heights against its direction, so tracker jitter,
    queue creep and U-turns through the junction mouth do not count. The interval runs
    until the vehicle leaves that carriageway.

    Congestion: a verified direction group holds at least four vehicles, 85% of them
    stationary or crawling, for `min_seconds`, while its governing lamp (if any) is
    green, which excludes ordinary red-phase queues. It ends when the queue clears.
    """

    window, distance, min_seconds = 2.0, 1.5, 15.0

    def __init__(self, scene):
        self.scene = scene
        self.wrong = {}
        self.jams = {}
        self.lamps = {}

    def step(self, vehicles, t, frame=None):
        flags, members = [], {}
        lanes = self.scene.config.get("lanes", [])
        for track in vehicles:
            obs = track.observation
            point = self.scene.point(obs.foot)
            lane = next((item for item in lanes if inside(point, item["polygon"])), None)
            track.lane = lane["id"] if lane else None
            if lane:
                members.setdefault(lane["id"], []).append(track)
            flag = self._wrong_way(track, lane, point, t)
            flags.extend([flag] if flag else [])
        for identity, state in list(self.wrong.items()):
            if t - state["last"] > 1:
                flags.append(
                    Flag("wrong_way", str(identity), state["start"], state["score"], state["lane"], end=state["last"])
                )
                self.wrong.pop(identity)
        flags.extend(self._congestion(members, t, frame))
        return flags

    def _wrong_way(self, track, lane, point, t):
        obs = track.observation
        state = self.wrong.get(obs.id)
        if state:
            if lane and lane["id"] == state["lane"]:
                state["last"] = t
                return Flag(
                    "wrong_way",
                    str(obs.id),
                    state["start"],
                    state["score"],
                    state["lane"],
                    "Travelled against the verified carriageway direction; the interval lasts while it stays in that carriageway.",
                )
            self.wrong.pop(obs.id)
            return Flag("wrong_way", str(obs.id), state["start"], state["score"], state["lane"], end=t)
        if not lane or not lane.get("verified") or not lane.get("wrong_way", True):
            return None
        window = [p for p in track.history if t - p[0] <= self.window]
        if not window or t - window[0][0] < self.window * 0.8:
            return None
        points = [self.scene.point((x, y)) for _, x, y in window]
        if not all(inside(p, lane["polygon"]) for p in points):
            return None
        x1, y1, x2, y2 = obs.box
        height = math.dist(self.scene.point(((x1 + x2) / 2, y2)), self.scene.point(((x1 + x2) / 2, y1)))
        moved = (point[0] - points[0][0], point[1] - points[0][1])
        if math.hypot(*moved) < self.distance * height or cosine(moved, lane["vector"]) > -0.8:
            return None
        self.wrong[obs.id] = {"start": window[0][0], "last": t, "lane": lane["id"], "score": obs.score}
        return None

    def _lamp(self, signal_id, frame, t):
        signal = next(
            (item for item in self.scene.config.get("signals", []) if item["id"] == signal_id),
            None,
        )
        if signal is None or frame is None:
            return None
        color = signal_color(
            self.scene.crop(frame, signal["roi"]),
            min_saturation=signal.get("min_saturation", 130),
            min_value=signal.get("min_value", 120),
        )
        return self.lamps.setdefault(signal_id, Lamp()).update(color, t)

    def _congestion(self, members, t, frame):
        flags = []
        for group in self.scene.config.get("directions", []):
            if not group.get("verified") or not group.get("all_lanes_visible"):
                continue
            tracks = [track for lane in group["lanes"] for track in members.get(lane, [])]
            slow = [track.speed / track.observation.height < 0.09 for track in tracks]
            lamp = self._lamp(group["signal"], frame, t) if group.get("signal") else "green"
            jammed = len(tracks) >= 4 and sum(slow) >= 0.85 * len(tracks) and lamp == "green"
            state = self.jams.get(group["id"])
            if jammed:
                if state is None:
                    state = self.jams[group["id"]] = {"start": t, "last": t}
                state["last"] = t
            if state is None:
                continue
            closing = t - state["last"] > 3
            if state["last"] - state["start"] >= self.min_seconds:
                flags.append(
                    Flag(
                        "congestion",
                        group["id"],
                        state["start"],
                        0.65,
                        group["id"],
                        "Traffic at a standstill across the direction while its lamp is green or unsignalled.",
                        end=state["last"] if closing else None,
                    )
                )
            if closing:
                self.jams.pop(group["id"])
        return flags
