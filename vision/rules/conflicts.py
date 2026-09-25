from itertools import combinations
from ..geometry import distance, iou
from ..types import Flag, VEHICLES


class ConflictRules:
    def __init__(self, scene):
        self.scene = scene
        self.contacts = {}

    def step(self, tracks, t, frame=None):
        if not self.scene.config.get("experimental_conflicts", False):
            return []
        flags = []
        for a, b in combinations(tracks, 2):
            x, y = a.observation, b.observation
            if x.kind not in VEHICLES and y.kind not in VEHICLES:
                continue
            if (
                t - min(a.first, b.first) < 1
                or not self.scene.on_road(x.foot)
                or not self.scene.on_road(y.foot)
            ):
                continue
            scale = (x.height + y.height) / 2
            close = distance(x.foot, y.foot) < scale * 0.65
            braking = (
                max(a.previous_speed - a.speed, b.previous_speed - b.speed)
                > scale * 0.08
            )
            overlap = iou(x.box, y.box)
            key = f"{min(x.id, y.id)}:{max(x.id, y.id)}"
            if close and braking and overlap > 0.2:
                self.contacts.setdefault(key, t)
            if (
                key in self.contacts
                and close
                and overlap > 0.2
                and t - self.contacts[key] >= 0.35
            ):
                flags.append(
                    Flag(
                        "accident",
                        key,
                        self.contacts[key],
                        min(x.score, y.score) * 0.7,
                        None,
                        "Experimental contact candidate: overlap, proximity, abrupt braking, and persistence. Requires visual verification.",
                    )
                )
            elif close and braking and overlap < 0.03:
                flags.append(
                    Flag(
                        "near_miss",
                        key,
                        t,
                        min(x.score, y.score) * 0.7,
                        None,
                        "Experimental close conflict with evasive braking and no box overlap.",
                    )
                )
            elif not close:
                self.contacts.pop(key, None)
        return flags
