from vision.rules.crossing import CrossingRules, is_rider
from vision.types import Observation, Track


class Scene:
    config = {"crossings": [{"id": "A", "polygon": [[0.4, 0.0], [0.6, 0.0], [0.6, 1.0], [0.4, 1.0]]}]}

    def on_road(self, point):
        return True

    def point(self, point):
        return point

    def crossing(self, point):
        return "A" if 0.4 <= point[0] <= 0.6 else None


def vehicle(x):
    tr = Track(Observation(1, "car", 0.9, (x - 0.05, 0.4, x + 0.05, 0.6)), 0, 0)
    tr.speed = 0.1
    tr.velocity = (0.1, 0)
    return tr


def pedestrian(y, speed=0.2):
    tr = Track(Observation(2, "person", 0.9, (0.46, y - 0.2, 0.54, y)), -1, 0)
    tr.speed = speed
    return tr


def test_yield_event_continues_until_vehicle_clears_after_pedestrian_leaves():
    rules = CrossingRules(Scene())
    person = pedestrian(0.5)
    assert rules.step([vehicle(0.45), person], [person], 0)[0].start == 0
    assert rules.step([vehicle(0.55)], [], 1)[0].end is None
    assert rules.step([vehicle(0.7)], [], 2)[0].end == 2


def test_waiting_or_standing_pedestrians_do_not_trigger_a_yield_event():
    for person in [pedestrian(0.02), pedestrian(0.5, speed=0.01)]:
        rules = CrossingRules(Scene())
        assert rules.step([vehicle(0.45), person], [person], 0) == []
        assert rules.step([vehicle(0.7)], [], 1) == []


def test_cyclist_body_is_not_automatically_a_walking_pedestrian():
    person = Track(Observation(1, "person", 0.9, (0.4, 0.2, 0.55, 0.55)), 0, 0)
    bike = Track(Observation(2, "bicycle", 0.9, (0.38, 0.4, 0.58, 0.8)), 0, 0)
    assert is_rider(person, [person, bike])
