from collections import deque
import numpy as np
from vision.rules.signals import SignalRules
from vision.segments import Segments
from vision.types import Observation, Track


class Scene:
    config = {
        "signals": [
            {
                "id": "signal",
                "verified": True,
                "roi": [0, 0, 1, 1],
                "stop_line": [[0, 0.5], [1, 0.5]],
                "entry_side": 1,
                "approach": [[0, 0], [1, 0], [1, 0.5], [0, 0.5]],
                "beyond_line": [[0, 0.5], [1, 0.5], [1, 0.65], [0, 0.65]],
                "intersection": [[0, 0.65], [1, 0.65], [1, 0.95], [0, 0.95]],
            }
        ]
    }

    def crop(self, frame, roi):
        return frame

    def point(self, point):
        return point


def track(y, t, stopped=None):
    tr = Track(Observation(1, "car", 0.9, (0.4, y - 0.1, 0.6, y)), 0, t)
    tr.history = deque(
        [(max(0, t - 0.2), 0.5, y - 0.1), (t - 0.1, 0.5, y - 0.05), (t, 0.5, y)]
    )
    tr.stopped_since = stopped
    return tr


def frame(color):
    return np.full((10, 10, 3), color, np.uint8)


def test_stop_line_closes_exactly_on_green_even_if_vehicle_disappears():
    rules, segments = SignalRules(Scene()), Segments()
    for t in [0, 0.2, 0.4, 0.6, 0.8]:
        flags = rules.step([track(0.6, t, 0)] if t < 0.5 else [], t, frame((0, 0, 255)))
        segments.update(flags, t)
    segments.update(rules.step([], 1.0, frame((0, 255, 0))), 1.0)
    result = [e.tuple() for e in segments.finish(2)]
    assert result == [[0, 1.0, "stop_line"]]


def test_red_light_starts_at_crossing_and_ends_at_intersection_exit():
    rules, segments = SignalRules(Scene()), Segments()
    for t, y in [
        (0, 0.3),
        (0.2, 0.4),
        (0.4, 0.55),
        (0.6, 0.7),
        (0.8, 0.8),
        (1.0, 0.99),
    ]:
        segments.update(rules.step([track(y, t)], t, frame((0, 0, 255))), t)
    result = [e.tuple() for e in segments.finish(2)]
    assert result == [[0.2, 1.0, "red_light"]]


def test_green_crossing_is_not_a_red_light_violation():
    rules = SignalRules(Scene())
    for t, y in [(0, 0.4), (0.2, 0.55), (0.4, 0.8)]:
        assert rules.step([track(y, t)], t, frame((0, 255, 0))) == []
