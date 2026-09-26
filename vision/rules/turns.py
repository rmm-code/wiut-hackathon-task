import math
from ..geometry import cosine, crossed, inside, line_side
from ..types import Flag, VEHICLES


class TurnRules:
    """Prohibited turns, U-turns and solid-marking crossings from verified scene facts.

    A rule fires when a continuously tracked vehicle seen moving inside its `from`
    region (along `from_vector`, if given) later travels along `exit_vector` inside
    `prohibited_exit`. U-turn rules set `progressive`: the heading must pass through
    a perpendicular direction, which separates a real reversal from an identity
    switch between opposing vehicles. With `start_line` the manoeuvre starts when the
    vehicle crosses that line (for example a stop line) instead of at a heading change.
    """

    def __init__(self, scene):
        self.scene = scene
        self.turns = {}
        self.lines = {}
        self.done = set()

    def step(self, tracks, t, frame=None):
        flags = []
        ids = {track.observation.id for track in tracks}
        rules = [
            (rule, "illegal_turn") for rule in self.scene.config.get("turn_rules", [])
        ] + [
            (rule, "illegal_u_turn")
            for rule in self.scene.config.get("prohibited_u_turns", [])
        ]
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
            for rule, label in rules:
                flag = self._turn(rule, label, obs, point, velocity, moving, t)
                flags.extend([flag] if flag else [])
            flags.extend(self._lines(obs, point, t))
        for cache in (self.turns, self.lines):
            for key in list(cache):
                if key[0] not in ids:
                    cache.pop(key)
        self.done = {key for key in self.done if key[0] in ids}
        return flags

    def _turn(self, rule, label, obs, point, velocity, moving, t):
        key = (obs.id, rule["id"])
        if not rule.get("verified") or key in self.done:
            return None
        state = self.turns.get(key)
        # A box jump between samples is an identity switch, not a manoeuvre.
        allowed = max(0.03, obs.height * 1.2) * max(1.0, (t - state["t"]) / 0.25) if state else 0
        if state and math.dist(point, state["last"]) > allowed:
            self.turns.pop(key)
            state = None
        if state is None:
            if not (moving and inside(point, rule["from"])):
                return None
            if cosine(velocity, rule.get("from_vector", velocity)) < 0.7:
                return None
            state = self.turns[key] = {"heading": velocity, "start": None, "side": False, "last": point, "t": t}
        previous = state["last"]
        state["last"], state["t"] = point, t
        line = rule.get("start_line")
        if line and state["start"] is None and crossed(previous, point, line):
            # The manoeuvre starts where the vehicle leaves its approach lane.
            state["start"] = t
            state["side"] = True
        if not moving:
            return None
        if (
            state["start"] is None
            and inside(point, rule["from"])
            and cosine(velocity, rule.get("from_vector", state["heading"])) > 0.9
        ):
            # Measure the turn from the last straight travel inside the approach.
            state["heading"] = velocity
        direction = cosine(state["heading"], velocity)
        if direction < 0.85 and state["start"] is None and not line:
            state["start"] = t
        if state["start"] is not None and abs(direction) < 0.5:
            state["side"] = True
        completed = (
            inside(point, rule["prohibited_exit"])
            and cosine(velocity, rule["exit_vector"]) > rule.get("exit_cosine", 0.9)
            and (state["side"] or not rule.get("progressive"))
        )
        if not (completed and state["start"] is not None):
            return None
        self.done.add(key)
        return Flag(
            label,
            str(key),
            state["start"],
            obs.score,
            rule["id"],
            rule.get("summary", "Verified prohibited manoeuvre")
            + "; start is the first heading change and end is completion.",
            end=t,
        )

    def _lines(self, obs, point, t):
        flags = []
        for line in self.scene.config.get("solid_lines", []):
            if not line.get("verified"):
                continue
            a, b = line["points"]
            delta = (b[0] - a[0], b[1] - a[1])
            norm = delta[0] ** 2 + delta[1] ** 2
            fraction = (
                (point[0] - a[0]) * delta[0] + (point[1] - a[1]) * delta[1]
            ) / max(norm, 1e-9)
            key = (obs.id, line["id"])
            if not -0.05 <= fraction <= 1.05:
                self.lines.pop(key, None)
                continue
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
        return flags
