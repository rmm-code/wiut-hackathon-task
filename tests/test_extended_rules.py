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


def test_near_miss_requires_evasion_and_separation_without_overlap():
    for brake, overlap, expected in [
        (True, False, True),
        (False, False, False),
        (True, True, False),
    ]:
        rules = ConflictRules(scene({"near_miss": {"enabled": True}}))
        a, b = track(0.45, 0.6, (0.06, 0)), track(0.57, 0.6, (-0.06, 0), 2)
        assert rules.step([a, b], 1) == []
        a, b = (
            track(0.46, 0.6, (0 if brake else 0.06, 0)),
            track(0.56, 0.6, (0 if brake else -0.06, 0), 2),
        )
        if brake:
            a.history = track(0.46, 0.6, (0.06, 0)).history
            b.history = track(0.56, 0.6, (-0.06, 0), 2).history
        if overlap:
            b.observation.box = a.observation.box
        assert rules.step([a, b], 1.3) == []
        flags = rules.step(
            [track(0.43, 0.6, (-0.1, 0)), track(0.65, 0.6, (0.1, 0), 2)], 1.6
        )
        assert bool(flags) == expected
        if expected:
            assert (flags[0].label, flags[0].start, flags[0].end) == (
                "near_miss",
                1.3,
                1.6,
            )


def test_wrong_way_continues_when_stopped_and_closes_at_lane_exit():
    lane = {"id": "lane", "verified": True, "vector": [1, 0]}
    view = scene({})
    view.lane = lambda p: lane if p[0] < 0.8 else None
    rules = DirectionRules(view)
    flags = rules.step([track(0.5, 0.6, (-0.1, 0))], 2)
    assert flags[0].label == "wrong_way"
    flags = rules.step([track(0.5, 0.6, (0, 0))], 3)
    assert flags[0].start == 2 and flags[0].end is None
    assert rules.step([track(0.9, 0.6, (0.1, 0))], 4)[0].end == 4


def test_congestion_requires_every_mapped_lane_and_complete_visibility():
    config = {
        "directions": [
            {
                "id": "east",
                "lanes": ["a", "b"],
                "verified": True,
                "all_lanes_visible": True,
            }
        ]
    }
    view = scene(config)
    view.lane = lambda p: {"id": "a" if p[0] < 0.5 else "b", "verified": False}
    rules = DirectionRules(view)
    cars = [track(x, 0.6, (0, 0), i) for i, x in enumerate([0.2, 0.3, 0.7, 0.8])]
    assert [f.label for f in rules.step(cars, 2)] == ["congestion"]
    assert not rules.step(cars[:3], 3)
    config["directions"][0]["all_lanes_visible"] = False
    assert not rules.step(cars, 4)


def test_prohibited_turn_and_u_turn_have_observed_boundaries():
    for uturn in [False, True]:
        rule = {"id": "turn", "verified": True}
        if uturn:
            rule["polygon"] = [[0, 0], [1, 0], [1, 1], [0, 1]]
            config = {"prohibited_u_turns": [rule]}
        else:
            rule.update(
                {
                    "from": [[0, 0], [0.5, 0], [0.5, 0.5], [0, 0.5]],
                    "prohibited_exit": [[0.6, 0.6], [1, 0.6], [1, 1], [0.6, 1]],
                    "exit_vector": [0, 1],
                }
            )
            config = {"turn_rules": [rule]}
        rules = TurnRules(scene(config))
        assert not rules.step([track(0.3, 0.3)], 0)
        assert not rules.step([track(0.55, 0.5, (0.05, 0.07))], 1)
        flags = rules.step([track(0.7, 0.7, (-0.1, 0) if uturn else (0, 0.1))], 2)
        assert (flags[0].label, flags[0].start, flags[0].end) == (
            "illegal_u_turn" if uturn else "illegal_turn",
            1,
            2,
        )
        rule["verified"] = False
        assert not TurnRules(scene(config)).step([track(0.3, 0.3)], 0)


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
