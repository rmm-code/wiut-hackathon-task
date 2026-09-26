import math
from itertools import combinations
from ..geometry import cosine, distance, dot, iou
from ..types import Flag, VEHICLES

EDGE = 0.01


def clipped(box):
    """Boxes cut by the frame edge change size as objects leave, which mimics braking."""
    x1, y1, x2, y2 = box
    return x1 < EDGE or y1 < EDGE or x2 > 1 - EDGE or y2 > 1 - EDGE


def speed_at(track, t, span=0.4):
    points = [p for p in track.history if t - span - 1e-6 <= p[0] <= t + 1e-6]
    if len(points) < 2 or points[-1][0] - points[0][0] < span * 0.6:
        return None
    dt = points[-1][0] - points[0][0]
    return ((points[-1][1] - points[0][1]) / dt, (points[-1][2] - points[0][2]) / dt)


def evasive(track, t):
    """Hard braking (speed falls below 40%) or a sharp swerve (30 degrees) within 1 s."""
    before, now = speed_at(track, t - 1.0), speed_at(track, t)
    if before is None or now is None:
        return False
    height = track.observation.height
    old, new = math.hypot(*before), math.hypot(*now)
    if old < height * 0.5:
        return False
    return new < old * 0.4 or (new > old * 0.6 and cosine(before, now) < math.cos(math.radians(30)))


class ConflictRules:
    """Near misses need two moving road users on a collision course (time to closest
    approach under 1.5 s, predicted miss under a third of their size), a hard brake or
    swerve by one of them, no box overlap, and separation afterwards. Edge-clipped
    boxes and pedestrians on marked crossings are excluded: the first mimic braking,
    the second are yield situations handled by failure_to_yield.
    """

    def __init__(self, scene):
        self.scene = scene
        self.states = {}

    def step(self, tracks, t, frame=None):
        if not self.scene.config.get("near_miss", {}).get("enabled", False):
            return []
        flags, seen = [], set()
        eligible = [
            tr
            for tr in tracks
            if t - tr.first >= 1
            and self.scene.on_road(tr.observation.foot)
            and not clipped(tr.observation.box)
            and not (
                tr.observation.kind == "person"
                and self.scene.crossing(tr.observation.foot)
            )
        ]
        for a, b in combinations(eligible, 2):
            x, y = a.observation, b.observation
            if x.kind not in VEHICLES and y.kind not in VEHICLES:
                continue
            scale = (x.height + y.height) / 2
            gap = distance(x.foot, y.foot)
            key = tuple(sorted((x.id, y.id)))
            if gap > scale * 4 and key not in self.states:
                continue
            seen.add(key)
            position = (y.foot[0] - x.foot[0], y.foot[1] - x.foot[1])
            velocity = (b.velocity[0] - a.velocity[0], b.velocity[1] - a.velocity[1])
            speed2 = dot(velocity, velocity)
            ttc = -dot(position, velocity) / speed2 if speed2 > 1e-8 else -1
            miss = math.hypot(position[0] + velocity[0] * ttc, position[1] + velocity[1] * ttc)
            both_moving = min(a.speed / x.height, b.speed / y.height) > 0.3
            approaching = both_moving and 0 < ttc < 1.5 and miss < scale * 0.33
            state = self.states.get(key)
            if approaching and state is None:
                state = {"hazard": t, "start": None, "last": t, "blocked": False, "score": min(x.score, y.score)}
                self.states[key] = state
            if state is None:
                continue
            state["last"] = t
            if iou(x.box, y.box) > 0.12:
                state["blocked"] = True
            if approaching:
                state["hazard"] = t
            if (
                state["start"] is None
                and not state["blocked"]
                and t - state["hazard"] < 1.5
                and gap < scale * 2
                and (evasive(a, t) or evasive(b, t))
            ):
                state["start"] = t - 0.5
            separated = gap > scale * 1.5 and dot(position, velocity) > 0
            if separated or t - state["hazard"] > 5:
                if separated and not state["blocked"] and state["start"] is not None and t - state["start"] >= 0.5:
                    flags.append(
                        Flag(
                            "near_miss",
                            str(key),
                            state["start"],
                            state["score"] * 0.7,
                            None,
                            "Collision course, hard braking or swerving, no box overlap, then separation; image-space candidate.",
                            end=t,
                        )
                    )
                self.states.pop(key)
        for key, state in list(self.states.items()):
            if key not in seen and t - state["last"] > 1:
                self.states.pop(key)
        return flags
