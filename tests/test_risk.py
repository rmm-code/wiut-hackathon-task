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


def test_calibration_is_monotonic_and_moves_the_alarm_threshold():
    from vision.risk import ALARM_RAW, calibrate

    values = [i / 100 for i in range(101)]
    mapped = [calibrate(v) for v in values]
    assert mapped == sorted(mapped) and calibrate(0) == 0 and calibrate(1) == 1
    assert abs(calibrate(ALARM_RAW) - 0.5) < 1e-9 and calibrate(0.5) < 0.5


def test_budget_guard_stops_part_b_only_when_the_total_would_run_over(monkeypatch):
    from types import SimpleNamespace

    import numpy as np
    import pytest
    from vision import budget, risk

    clock = {"now": 1000.0}
    monkeypatch.setattr(budget, "_started", {})
    monkeypatch.setattr(risk.time, "perf_counter", lambda: clock["now"])
    monkeypatch.setattr(budget.time, "perf_counter", lambda: clock["now"])
    frame = np.zeros((8, 8, 3), np.uint8)
    meta = {"video_id": "clip.mp4", "fps": 10.0, "width": 8, "height": 8, "n_frames": 1000}

    def run(part_a_seconds, seconds_per_frame):
        clock["now"] = 1000.0
        budget.part_a_started("/data/clip.mp4")
        clock["now"] += part_a_seconds
        estimator = risk.RiskEstimator()
        estimator.reset(meta)
        estimator.stride = 10**9  # only the clock matters here: no model, one empty detection
        estimator.initialized = True
        estimator.detector = SimpleNamespace(step=lambda frame: [])
        for index in range(1000):
            estimator.step(frame, index / 10)
            clock["now"] += seconds_per_frame

    # 100 s video, 300 s budget: 100 s of Part A plus 0.15 s/frame finishes at 250 s.
    run(100, 0.15)
    # 0.25 s/frame would finish at 350 s: Part B must stop, well before the harness would.
    with pytest.raises(TimeoutError):
        run(100, 0.25)
    # Part A alone used 97% of the budget: stop at the first frame, before any detection.
    with pytest.raises(TimeoutError):
        run(291, 0.0)
    # Outside a harness run (Part A never ran here) there is no deadline at all.
    budget._started.clear()
    estimator = risk.RiskEstimator()
    estimator.reset(meta)
    assert estimator.deadline == float("inf")
