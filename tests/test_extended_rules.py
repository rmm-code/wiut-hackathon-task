from collections import deque
from types import SimpleNamespace
from vision.rules.conflicts import ConflictRules
from vision.rules.direction import DirectionRules
from vision.rules.turns import TurnRules
from vision.types import Observation, Track


def track(x, y, velocity=(0.1, 0), identity=1):
    item = Track(
        Observation(identity, "car", 0.9, (x - 0.02, y - 0.1, x + 0.02, y)), 0, 0
    )
    item.velocity = velocity
    item.speed = sum(v * v for v in velocity) ** 0.5
    item.history = deque(
        (t, x - velocity[0] * (1 - t), y - velocity[1] * (1 - t)) for t in [0, 0.4, 0.8]
    )
    return item


def scene(config):
    return SimpleNamespace(config=config, point=lambda p: p, on_road=lambda p: True)


def head_on(positions, t, identity):
    """Track at the last of `positions` [(time, x)], moving along y = 0.6."""
    x = positions[-1][1]
    item = track(x, 0.6, (0, 0), identity)
    item.first = positions[0][0]
    item.history = deque((pt, px, 0.6) for pt, px in positions)
    dt = positions[-1][0] - positions[-2][0]
    vx = (positions[-1][1] - positions[-2][1]) / dt
    item.velocity, item.speed = (vx, 0.0), abs(vx)
    return item


def test_near_miss_needs_collision_course_hard_braking_and_separation():
    for brake, expected in [(True, [("near_miss", 0.8, 1.7)]), (False, [])]:
        rules = ConflictRules(scene({"near_miss": {"enabled": True}}))
        a, b, flags = [], [], []
        for step in range(0, 21):
            t = step / 10
            if t <= 1.0:
                xa, xb = 0.2 + 0.2 * t, 0.8 - 0.2 * t
            elif brake:
                # Both brake hard, then b backs off: no contact, then separation.
                xa = 0.4 + 0.02 * (t - 1.0)
                xb = 0.6 - 0.02 * (t - 1.0) if t < 1.6 else 0.588 + 0.1 * (t - 1.6)
            else:
                xa, xb = 0.4 - 0.2 * (t - 1.0), 0.6 + 0.2 * (t - 1.0)
            a.append((t, xa))
            b.append((t, xb))
            if len(a) >= 2:
                flags += rules.step([head_on(a, t, 1), head_on(b, t, 2)], t)
        assert [(f.label, round(f.start, 2), round(f.end, 2)) for f in flags] == expected


def moving(x, y, t, velocity, identity=1):
    """A track at (x, y) at time t that has moved with `velocity` for the past 2.4 s."""
    item = track(x, y, velocity, identity)
    item.history = deque(
        (t - dt, x - velocity[0] * dt, y - velocity[1] * dt) for dt in [2.4, 1.6, 0.8, 0]
    )
    return item


def test_wrong_way_needs_sustained_travel_inside_one_carriageway():
    lane = {"id": "lane", "verified": True, "vector": [1, 0], "polygon": [[0, 0], [0.8, 0], [0.8, 1], [0, 1]]}
    view = scene({"lanes": [lane]})
    rules = DirectionRules(view)
    assert rules.step([moving(0.5, 0.6, 3, (-0.1, 0))], 3) == []
    flags = rules.step([moving(0.45, 0.6, 3.5, (-0.1, 0))], 3.5)
    assert flags[0].label == "wrong_way" and flags[0].start == 1.4 and flags[0].end is None
    assert rules.step([track(0.9, 0.6, (-0.1, 0))], 4)[0].end == 4
    # Jitter: a short backwards step is not wrong-way driving.
    assert DirectionRules(view).step([moving(0.5, 0.6, 3, (-0.02, 0))], 3) == []
    # A U-turn entering from another carriageway is excluded.
    turn = moving(0.1, 0.6, 3, (-0.1, 0))
    turn.history[0] = (0.6, 0.9, 0.6)
    assert DirectionRules(view).step([turn], 3) == []


def test_congestion_needs_a_standstill_on_green_for_fifteen_seconds():
    config = {
        "lanes": [{"id": "a", "verified": True, "wrong_way": False, "vector": [1, 0], "polygon": [[0, 0], [1, 0], [1, 1], [0, 1]]}],
        "directions": [{"id": "east", "lanes": ["a"], "verified": True, "all_lanes_visible": True}],
    }
    rules = DirectionRules(scene(config))
    cars = [track(x, 0.6, (0, 0), i) for i, x in enumerate([0.2, 0.4, 0.6, 0.8])]
    flags = []
    for t in range(0, 17):
        flags = rules.step(cars, t)
    assert [f.label for f in flags] == ["congestion"] and flags[0].start == 0
    assert not DirectionRules(scene(config)).step(cars[:3], 0)
    for t in range(17, 22):
        flags = rules.step([], t)
    assert flags == [] or flags[0].end == 16


def test_prohibited_turn_has_observed_boundaries():
    rule = {
        "id": "turn",
        "verified": True,
        "from": [[0, 0], [0.5, 0], [0.5, 0.5], [0, 0.5]],
        "prohibited_exit": [[0.6, 0.6], [1, 0.6], [1, 1], [0.6, 1]],
        "exit_vector": [0, 1],
    }
    config = {"turn_rules": [rule]}
    rules = TurnRules(scene(config))
    assert not rules.step([track(0.3, 0.3)], 0)
    assert not rules.step([track(0.55, 0.5, (0.05, 0.07))], 1)
    flags = rules.step([track(0.7, 0.7, (0, 0.1))], 2)
    assert (flags[0].label, flags[0].start, flags[0].end) == ("illegal_turn", 1, 2)
    # A vehicle that never entered the prohibited lanes may use the same exit.
    assert not TurnRules(scene(config)).step([track(0.7, 0.7, (0, 0.1))], 2)
    rule["verified"] = False
    assert not TurnRules(scene(config)).step([track(0.3, 0.3)], 0)


def test_u_turn_needs_progressive_reversal_and_continuous_track():
    rule = {
        "id": "nose",
        "verified": True,
        "progressive": True,
        "from": [[0, 0], [0.5, 0], [0.5, 1], [0, 1]],
        "from_vector": [1, 0],
        "prohibited_exit": [[0, 0], [1, 0], [1, 0.3], [0, 0.3]],
        "exit_vector": [-1, 0],
    }
    rules = TurnRules(scene({"prohibited_u_turns": [rule]}))
    path = [((0.30, 0.60), (0.1, 0)), ((0.45, 0.58), (0.07, -0.06)), ((0.52, 0.48), (0, -0.1)),
            ((0.50, 0.38), (-0.06, -0.08)), ((0.45, 0.28), (-0.1, 0))]
    flags = []
    for t, (point, velocity) in enumerate(path):
        flags += rules.step([track(*point, velocity)], t)
    assert [(f.label, f.start, f.end) for f in flags] == [("illegal_u_turn", 1, 4)]
    # An identity switch to an opposing vehicle jumps position: no U-turn.
    switch = TurnRules(scene({"prohibited_u_turns": [rule]}))
    assert not switch.step([track(0.30, 0.60, (0.1, 0))], 0)
    assert not switch.step([track(0.45, 0.25, (-0.1, 0))], 0.15)
    # Reversing without passing through a sideways heading is not a turn.
    flip = TurnRules(scene({"prohibited_u_turns": [rule]}))
    flip.step([track(0.30, 0.30, (0.1, 0))], 0)
    assert not flip.step([track(0.29, 0.29, (-0.1, 0))], 1)


def test_solid_line_is_a_finite_segment_not_an_infinite_extension():
    config = {
        "solid_lines": [
            {"id": "line", "verified": True, "points": [[0.5, 0.2], [0.5, 0.8]]}
        ]
    }
    for y, expected in [(0.5, True), (0.95, False)]:
        rules = TurnRules(scene(config))
        assert not rules.step([track(0.45, y)], 0)
        assert not rules.step([track(0.5, y)], 1)
        flags = rules.step([track(0.55, y)], 2)
        assert bool(flags) == expected
        if flags:
            assert flags[0].label == "solid_line_crossing"
