import math
from ..geometry import inside, iou
from ..types import Flag, VEHICLES


def is_rider(person, tracks):
    p = person.observation
    for track in tracks:
        vehicle = track.observation
        if vehicle.kind not in {"bicycle", "motorcycle"}:
            continue
        if (
            iou(p.box, vehicle.box) > 0.12
            and p.box[3] < vehicle.box[3] - vehicle.height * 0.12
        ):
            return True
    return False


def occluded(person, tracks):
    """A pedestrian whose feet are hidden behind a vehicle has an unreliable ground point."""
    x1, y1, x2, y2 = person.observation.box
    foot = ((x1 + x2) / 2, y2)
    for track in tracks:
        vx1, vy1, vx2, vy2 = track.observation.box
        if (
            track.observation.kind in VEHICLES
            and vx1 <= foot[0] <= vx2
            and vy1 <= foot[1] <= vy2 + (vy2 - vy1) * 0.05
        ):
            return True
    return False


def ground_ends(track):
    obs = track.observation
    x1, y1, x2, y2 = obs.box
    sign = 1 if track.velocity[0] >= 0 else -1
    cx = (x1 + x2) / 2
    near = y2
    far = y1 + (y2 - y1) * 0.65
    front_y, rear_y = (near, far) if track.velocity[1] >= 0 else (far, near)
    return (cx + sign * (x2 - x1) * 0.2, front_y), (cx - sign * (x2 - x1) * 0.2, rear_y)


def axis(polygon):
    """Walking axis of a four-sided crossing: between the midpoints of its short sides."""
    sides = [(polygon[i], polygon[(i + 1) % 4]) for i in range(4)]
    lengths = [math.dist(a, b) for a, b in sides]
    short = (0, 2) if lengths[0] + lengths[2] < lengths[1] + lengths[3] else (1, 3)
    ends = [((a[0] + b[0]) / 2, (a[1] + b[1]) / 2) for a, b in (sides[i] for i in short)]
    return ends


def along(point, ends):
    (ax, ay), (bx, by) = ends
    dx, dy = bx - ax, by - ay
    return ((point[0] - ax) * dx + (point[1] - ay) * dy) / max(dx * dx + dy * dy, 1e-12)


class CrossingRules:
    """Failure to yield: a vehicle moving across a crossing while a walking pedestrian is
    on the carriageway part of the same crossing, within about one vehicle size of the
    vehicle. Pedestrians waiting at the kerb or island ends of the crossing and vehicles
    standing in a queue are excluded. The interval covers the vehicle's traversal.
    """

    end_margin, reach = 0.06, 1.0

    def __init__(self, scene):
        self.scene = scene
        self.entries = {}
        self.axes = {
            item["id"]: axis(item["polygon"])
            for item in scene.config.get("crossings", [])
            if len(item["polygon"]) == 4
        }

    def walkers(self, people, t):
        found = {}
        for person in people:
            obs = person.observation
            crossing = self.scene.crossing(obs.foot)
            if crossing not in self.axes or t - person.first < 0.5:
                continue
            position = along(self.scene.point(obs.foot), self.axes[crossing])
            walking = person.speed / obs.height > 0.3
            if walking and self.end_margin < position < 1 - self.end_margin:
                found.setdefault(crossing, []).append(obs)
        return found

    def step(self, tracks, people, t):
        walkers = self.walkers(people, t)
        flags = []
        for track in tracks:
            obs = track.observation
            if obs.kind not in VEHICLES or obs.kind == "bicycle" or not self.scene.on_road(obs.foot):
                continue
            front, rear = ground_ends(track)
            crossing = self.scene.crossing(front)
            if crossing:
                key = (obs.id, crossing)
                state = self.entries.setdefault(
                    key, {"start": t, "last": t, "triggered": False, "score": obs.score}
                )
                if track.speed / obs.height > 0.15:
                    x1, y1, x2, y2 = obs.box
                    for person in walkers.get(crossing, []):
                        px, py = person.foot
                        gap = math.hypot(max(x1 - px, 0, px - x2), max(y1 - py, 0, py - y2))
                        state["triggered"] |= gap <= self.reach * obs.height
            for key, state in list(self.entries.items()):
                if key[0] != obs.id:
                    continue
                state["last"] = t
                clear = key[1] not in {
                    self.scene.crossing(front),
                    self.scene.crossing(rear),
                }
                if state["triggered"]:
                    flags.append(
                        Flag(
                            "failure_to_yield",
                            str(key),
                            state["start"],
                            state["score"],
                            key[1],
                            "Vehicle moved across the crossing next to a pedestrian walking on it; interval covers the traversal.",
                            end=t if clear else None,
                        )
                    )
                if clear:
                    self.entries.pop(key)
        for key, state in list(self.entries.items()):
            if t - state["last"] > 1:
                if state["triggered"]:
                    flags.append(
                        Flag(
                            "failure_to_yield",
                            str(key),
                            state["start"],
                            state["score"],
                            key[1],
                            end=state["last"],
                        )
                    )
                self.entries.pop(key)
        return flags
