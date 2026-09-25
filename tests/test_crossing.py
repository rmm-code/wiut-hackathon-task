from vision.rules.crossing import CrossingRules, is_rider
from vision.types import Observation, Track


class Scene:
    def on_road(self, point):
        return True

    def crossing(self, point):
        return "A" if 0.4 <= point[0] <= 0.6 else None


def vehicle(x):
    tr = Track(Observation(1, "car", 0.9, (x - 0.05, 0.4, x + 0.05, 0.6)), 0, 0)
    tr.speed = 0.1
    tr.velocity = (0.1, 0)
    return tr


def test_yield_event_continues_until_vehicle_clears_after_pedestrian_leaves():
    rules = CrossingRules(Scene())
    person = Track(Observation(2, "person", 0.9, (0.46, 0.3, 0.54, 0.5)), 0, 0)
    assert rules.step([vehicle(0.45), person], [person], 0)[0].start == 0
    assert rules.step([vehicle(0.55)], [], 1)[0].end is None
    assert rules.step([vehicle(0.7)], [], 2)[0].end == 2


def test_cyclist_body_is_not_automatically_a_walking_pedestrian():
    person = Track(Observation(1, "person", 0.9, (0.4, 0.2, 0.55, 0.55)), 0, 0)
    bike = Track(Observation(2, "bicycle", 0.9, (0.38, 0.4, 0.58, 0.8)), 0, 0)
    assert is_rider(person, [person, bike])
