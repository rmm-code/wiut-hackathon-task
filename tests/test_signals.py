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


def run(path, lamp):
    rules, segments = SignalRules(Scene()), Segments()
    for t, y in path:
        segments.update(rules.step([track(y, t)] if y else [], t, frame(lamp(t))), t)
    return [e.tuple() for e in segments.finish(6)]


RED, GREEN = (0, 0, 255), (0, 255, 0)
CROSSING = [(0.0, None), (1.0, 0.3), (1.2, 0.4), (1.4, 0.55), (1.8, 0.7), (2.4, 0.8), (3.0, 0.9), (3.6, 0.99)]


def test_red_light_starts_at_crossing_and_ends_at_intersection_exit():
    assert run(CROSSING, lambda t: RED) == [[1.2, 3.6, "red_light"]]


def test_amber_clearance_and_anticipatory_starts_are_not_violations():
    # Crossing 0.3 s after the lamp turned red: amber clearance.
    assert run(CROSSING, lambda t: GREEN if t < 1.1 else RED) == []
    # Lamp turns green within the confirmation window: anticipatory start.
    assert run(CROSSING, lambda t: GREEN if t >= 2.4 else RED) == []


def test_vehicle_stopped_at_the_paint_is_not_a_stop_line_violation():
    rules, segments = SignalRules(Scene()), Segments()
    for t in [0, 0.2, 0.4]:
        # Front 0.02 past the line with a 0.1-high box: 0.2 box heights.
        segments.update(rules.step([track(0.52, t, 0)], t, frame(RED)), t)
    segments.update(rules.step([], 1.0, frame(GREEN)), 1.0)
    assert segments.finish(2) == []


def test_green_crossing_is_not_a_red_light_violation():
    rules = SignalRules(Scene())
    for t, y in [(0, 0.4), (0.2, 0.55), (0.4, 0.8)]:
        assert rules.step([track(y, t)], t, frame((0, 255, 0))) == []


def test_real_camera_lamps_use_measured_region_thresholds():
    import cv2
    from vision.rules.signals import signal_color

    for color in ["red", "green"]:
        image = cv2.imread(f"tests/fixtures/signal-{color}.png")
        assert signal_color(image, min_saturation=100, min_value=50) == color
