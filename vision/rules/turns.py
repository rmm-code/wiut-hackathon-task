import math
from ..geometry import cosine, inside, line_side
from ..types import Flag, VEHICLES


class TurnRules:
    def __init__(self, scene):
        self.scene = scene
        self.turns = {}
        self.lines = {}
        self.done = set()

    def step(self, tracks, t, frame=None):
        flags = []
        ids = {track.observation.id for track in tracks}
        for track in tracks:
            obs = track.observation
            if obs.kind not in VEHICLES or len(track.history) < 3:
                continue
            point = self.scene.point(obs.foot)
            past = self.scene.point(
                (obs.foot[0] - track.velocity[0], obs.foot[1] - track.velocity[1])
            )
            velocity = (point[0] - past[0], point[1] - past[1])
            moving = math.hypot(*velocity) > obs.height * 0.1
            for rule in self.scene.config.get("turn_rules", []) + self.scene.config.get(
                "prohibited_u_turns", []
            ):
                if not rule.get("verified"):
                    continue
                key = (obs.id, rule["id"])
                uturn = "polygon" in rule
                entry = rule["polygon"] if uturn else rule["from"]
                if key in self.done:
                    continue
                if key not in self.turns and moving and inside(point, entry):
                    self.turns[key] = {"heading": velocity, "start": None}
                state = self.turns.get(key)
                if not state or not moving:
                    continue
                direction = cosine(state["heading"], velocity)
                if direction < 0.85 and state["start"] is None:
                    state["start"] = t
                completed = (
                    direction < -0.8
                    if uturn
                    else inside(point, rule["prohibited_exit"])
                    and cosine(velocity, rule["exit_vector"]) > 0.9
                )
                if completed and state["start"] is not None:
                    flags.append(
                        Flag(
                            "illegal_u_turn" if uturn else "illegal_turn",
                            str(key),
                            state["start"],
                            obs.score,
                            rule["id"],
                            "Verified prohibited manoeuvre; start is the first observed heading change and end is completion.",
                            end=t,
                        )
                    )
                    self.done.add(key)
            for line in self.scene.config.get("solid_lines", []):
                if not line.get("verified"):
                    continue
                a, b = line["points"]
                delta = (b[0] - a[0], b[1] - a[1])
                norm = delta[0] ** 2 + delta[1] ** 2
                fraction = (
                    (point[0] - a[0]) * delta[0] + (point[1] - a[1]) * delta[1]
                ) / max(norm, 1e-9)
                if not -0.05 <= fraction <= 1.05:
                    self.lines.pop((obs.id, line["id"]), None)
                    continue
                key = (obs.id, line["id"])
                if key in self.done:
                    continue
                x1, _, x2, y2 = obs.box
                sides = [
                    line_side(self.scene.point((x, y2)), line["points"])
                    for x in [x1 + (x2 - x1) * 0.2, x1 + (x2 - x1) * 0.8]
                ]
                side = 1 if min(sides) > 0 else -1 if max(sides) < 0 else 0
                state = self.lines.setdefault(key, {"side": side, "start": None})
                if state["side"] == 0:
                    state["side"] = side
                if side == 0 and state["side"] and state["start"] is None:
                    state["start"] = t
                if side and state["start"] is not None:
                    if side != state["side"]:
                        flags.append(
                            Flag(
                                "solid_line_crossing",
                                str(key),
                                state["start"],
                                obs.score,
                                line["id"],
                                "Ground-footprint proxy straddles and then clears a verified solid marking.",
                                end=t,
                            )
                        )
                        self.done.add(key)
                    else:
                        state["start"] = None
        for cache in (self.turns, self.lines):
            for key in list(cache):
                if key[0] not in ids:
                    cache.pop(key)
        self.done = {key for key in self.done if key[0] in ids}
        return flags
