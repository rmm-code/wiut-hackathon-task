from vision.rules.road import RoadRules
from vision.tracks import Tracks
from vision.types import Observation
from vision.geometry import inside


class Scene:
    matched = True
    config = {"lanes": []}

    def point(self, point):
        return point

    def on_road(self, point, margin=0):
        return margin < point[0] < 1 - margin and margin < point[1] < 1 - margin

    def crossing(self, point):
        return "crossing" if 0.4 <= point[0] <= 0.6 else None

    def near_crossing(self, point, margin):
        return 0.4 - margin <= point[0] <= 0.6 + margin

    def lane(self, point):
        return None

    def queue_zone(self, point):
        return point[0] < 0.4


def observation(identity=1, kind="car", x=0.7):
    return Observation(identity, kind, 0.9, (x - 0.05, 0.4, x + 0.05, 0.6))


def test_stop_requires_ten_seconds_and_excludes_queue():
    for x, should_detect in [(0.7, True), (0.2, False)]:
        tracks, rules = Tracks(), RoadRules(Scene())
        found = []
        for index in range(97):
            t = index / 8
            flags = rules.step(tracks.update([observation(x=x)], t), t)
            if t < 10:
                assert not flags
            found.extend(flags)
        assert bool(found) is should_detect
        if found:
            assert found[0].start < 1


def test_marked_crossing_is_not_jaywalking():
    rules = RoadRules(Scene())
    tracks = Tracks()
    assert rules.step(tracks.update([observation(kind="person", x=0.5)], 0), 0) == []
    flags = rules.step(tracks.update([observation(kind="person", x=0.8)], 1), 1)
    assert [flag.label for flag in flags] == ["jaywalking"]


def test_geometry_includes_boundary_but_excludes_outside():
    polygon = [(0, 0), (1, 0), (1, 1), (0, 1)]
    assert inside((0, 0.5), polygon)
    assert not inside((1.1, 0.5), polygon)
