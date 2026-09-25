import cv2
import numpy as np
import pytest
from vision.risk import RiskEstimator
from vision.types import Observation


def test_wrapper_is_causal_resettable_and_never_opens_video(monkeypatch):
    class Detector:
        def __init__(self, *args):
            pass

        def step(self, frame):
            offset = float(frame[0, 0, 0]) / 1000
            return [
                Observation(1, "car", 0.9, (0.1 + offset, 0.2, 0.2 + offset, 0.4)),
                Observation(2, "car", 0.9, (0.7 - offset, 0.2, 0.8 - offset, 0.4)),
            ]

    class Scene:
        def __init__(self, *args):
            pass

        def align(self, frame):
            pass

        def on_road(self, point):
            return True

    def forbidden(*args, **kwargs):
        raise AssertionError("Part B opened a video")

    monkeypatch.setattr("vision.detector.Detector", Detector)
    monkeypatch.setattr("vision.scene.Scene", Scene)
    monkeypatch.setattr(cv2, "VideoCapture", forbidden)
    estimator = RiskEstimator()
    meta = {"fps": 8, "duration": 8, "n_frames": 64, "width": 2, "height": 2}

    def run(values):
        estimator.reset(meta)
        return [
            estimator.step(np.full((2, 2, 3), value, np.uint8), i / 8)
            for i, value in enumerate(values)
        ]

    prefix = list(range(0, 200, 5))
    first = run(prefix + [0] * 24)
    second = run(prefix + [255] * 24)
    assert first[: len(prefix)] == second[: len(prefix)]
    assert first == run(prefix + [0] * 24)
    assert all(isinstance(value, float) and 0 <= value <= 1 for value in first)
    with pytest.raises(ValueError):
        estimator.step(np.zeros((2, 2, 3), np.uint8), 0)
