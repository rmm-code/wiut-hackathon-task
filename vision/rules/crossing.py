from ..geometry import iou
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


def ground_ends(track):
    obs = track.observation
    x1, y1, x2, y2 = obs.box
    sign = 1 if track.velocity[0] >= 0 else -1
    cx = (x1 + x2) / 2
    near = y2
    far = y1 + (y2 - y1) * 0.65
    front_y, rear_y = (near, far) if track.velocity[1] >= 0 else (far, near)
    return (cx + sign * (x2 - x1) * 0.2, front_y), (cx - sign * (x2 - x1) * 0.2, rear_y)


class CrossingRules:
    def __init__(self, scene):
        self.scene = scene
        self.entries = {}

    def step(self, tracks, people, t):
        occupied = {self.scene.crossing(person.observation.foot) for person in people}
        occupied.discard(None)
        flags = []
        for track in tracks:
            obs = track.observation
            if obs.kind not in VEHICLES or not self.scene.on_road(obs.foot):
                continue
            front, rear = ground_ends(track)
            crossing = self.scene.crossing(front)
            if crossing:
                key = (obs.id, crossing)
                state = self.entries.setdefault(
                    key, {"start": t, "last": t, "triggered": False, "score": obs.score}
                )
                state["triggered"] |= (
                    crossing in occupied and track.speed > obs.height * 0.07
                )
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
                            "Vehicle crossing occupancy overlaps a walking pedestrian; interval covers the vehicle traversal.",
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
