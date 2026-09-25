import math
from itertools import combinations
from ..geometry import cosine, distance, dot, iou
from ..types import Flag, VEHICLES


def evasive(track, t):
    past = [p for p in track.history if 0.3 <= t - p[0] <= 1.1]
    if len(past) < 2 or past[-1][0] - past[0][0] < 0.2:
        return False
    dt = past[-1][0] - past[0][0]
    prior = ((past[-1][1] - past[0][1]) / dt, (past[-1][2] - past[0][2]) / dt)
    speed = math.hypot(*prior)
    if speed < track.observation.height * 0.2:
        return False
    return track.speed < speed * 0.45 or (
        track.speed > speed * 0.5 and cosine(prior, track.velocity) < 0.75
    )


class ConflictRules:
    """Near misses require approach, evasive motion, no observed overlap, then separation."""

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
            if t - tr.first >= 1 and self.scene.on_road(tr.observation.foot)
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
            miss = math.hypot(
                position[0] + velocity[0] * ttc, position[1] + velocity[1] * ttc
            )
            approaching = 0 < ttc < 3 and miss < scale * 0.4
            state = self.states.get(key)
            if approaching and state is None:
                state = {
                    "hazard": t,
                    "start": None,
                    "last": t,
                    "blocked": False,
                    "score": min(x.score, y.score),
                }
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
            ):
                if evasive(a, t) or evasive(b, t):
                    state["start"] = t
            separated = gap > scale * 1.5 and dot(position, velocity) > 0
            if separated or t - state["hazard"] > 5:
                if (
                    separated
                    and not state["blocked"]
                    and state["start"] is not None
                    and t - state["start"] >= 0.2
                ):
                    flags.append(
                        Flag(
                            "near_miss",
                            str(key),
                            state["start"],
                            state["score"] * 0.7,
                            None,
                            "Approaching trajectories, observed braking/swerving, no box-overlap evidence, then separation; image-space candidate.",
                            end=t,
                        )
                    )
                self.states.pop(key)
        for key, state in list(self.states.items()):
            if key not in seen and t - state["last"] > 1:
                self.states.pop(key)
        return flags
