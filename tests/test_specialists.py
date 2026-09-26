from types import SimpleNamespace
import numpy as np
from vision.specialists import Specialists
from vision.types import Observation, Track


class Box:
    cls = [0]
    xyxy = [[10, 20, 40, 50]]
    conf = [0.9]


class Boxes(list):
    def cpu(self):
        return self

    def numpy(self):
        return self


class Model:
    def __init__(self, name):
        self.names = {0: name}
        self.present = True

    def predict(self, *args, **kwargs):
        return [SimpleNamespace(boxes=Boxes([Box()] if self.present else []))]


def system(label):
    instance = Specialists.__new__(Specialists)
    instance.scene = SimpleNamespace(matched=True, on_road=lambda point: True)
    instance.device = "cpu"
    model = Model(label)
    instance.models = [({"confidence": 0.5, "classes": {label: label}}, model)]
    instance.active, instance.completed, instance.resolved = [], [], []
    instance.next_time = 0
    return instance, model, np.zeros((100, 100, 3), np.uint8)


def test_single_fire_hit_is_not_an_event():
    detector, model, frame = system("fire_smoke")
    detector.step(frame, [], 0)
    model.present = False
    detector.step(frame, [], 3)
    assert detector.finish(4) == []


def test_confirmed_fire_ends_at_last_observation():
    detector, model, frame = system("fire_smoke")
    detector.step(frame, [], 0)
    detector.step(frame, [], 1)
    model.present = False
    detector.step(frame, [], 4)
    assert [event.tuple() for event in detector.finish(5)] == [[0, 1, "fire_smoke"]]


def test_accident_is_not_repeated_while_wreck_is_visible():
    detector, model, frame = system("accident")
    participant = Track(Observation(1, "car", 0.9, (0.1, 0.2, 0.4, 0.5)), 0, 0)
    for t in range(6):
        if t >= 2:
            participant.stopped_since = 2
        detector.step(frame, [participant], t)
    assert [event.tuple() for event in detector.finish(6)] == [[0, 2, "accident"]]


def test_accident_candidate_whose_vehicles_drive_on_is_dropped():
    detector, model, frame = system("accident")
    participant = Track(Observation(1, "car", 0.9, (0.1, 0.2, 0.4, 0.5)), 0, 0)
    for t in range(4):
        detector.step(frame, [participant], t)
    model.present = False
    detector.step(frame, [participant], 7)
    assert detector.finish(8) == []
