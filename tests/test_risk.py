from copy import deepcopy
from vision.risk import RiskModel
from vision.types import Track, Observation


class Scene:
    def on_road(self, point):
        return True


def pair(t):
    a = Track(Observation(1, "car", 0.95, (0.3, 0.3, 0.4, 0.5)), 0, t)
    b = Track(Observation(2, "car", 0.95, (0.4, 0.3, 0.5, 0.5)), 0, t)
    a.velocity = (0.04, 0)
    b.velocity = (-0.04, 0)
    return [a, b]


def test_risk_is_bounded_and_causal_for_identical_prefixes():
    first, second = RiskModel(), RiskModel()
    prefix = [pair(t / 8) for t in range(24)]
    scores1 = [first.step(tracks, t / 8, Scene()) for t, tracks in enumerate(prefix)]
    scores2 = [
        second.step(deepcopy(tracks), t / 8, Scene()) for t, tracks in enumerate(prefix)
    ]
    assert scores1 == scores2
    assert all(0 <= value <= 1 for value in scores1)
    assert max(scores1) > 0.5
    first.step([], 5, Scene())
    assert scores1 == scores2


def test_safe_parallel_motion_does_not_raise_risk():
    tracks = pair(2)
    tracks[1].velocity = tracks[0].velocity
    assert RiskModel().step(tracks, 2, Scene()) == 0


def test_no_risk_leaks_between_instances():
    RiskModel().step(pair(2), 2, Scene())
    assert RiskModel().step([], 0, Scene()) == 0
