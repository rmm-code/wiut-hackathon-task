from vision.segments import Segments
from vision.types import Flag


def test_stopped_event_backdates_to_original_stop():
    segments = Segments()
    segments.update([Flag("stopped_vehicle", "1", 1)], 11)
    segments.update([Flag("stopped_vehicle", "1", 1)], 12)
    assert segments.finish(12.1)[0].tuple() == [1, 12.1, "stopped_vehicle"]


def test_union_same_class_keeps_different_class_overlap():
    segments = Segments()
    for t in [1, 2, 3, 4]:
        flags = [Flag("near_miss", "a", 1)] if t <= 3 else []
        if t >= 2:
            flags += [Flag("near_miss", "b", 2), Flag("jaywalking", "person", 2)]
        segments.update(flags, t)
    result = [event.tuple() for event in segments.finish(4.1)]
    assert [1, 4.1, "near_miss"] in result
    assert [2, 4.1, "jaywalking"] in result
    assert len(result) == 2


def test_short_unconfirmed_blip_is_not_an_event():
    segments = Segments()
    segments.update([Flag("jaywalking", "1", 0)], 0)
    segments.update([], 1)
    assert segments.finish(2) == []
