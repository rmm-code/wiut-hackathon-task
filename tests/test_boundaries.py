from vision.segments import Segments
from vision.types import Flag


def test_delayed_turn_confirmation_preserves_observed_start_and_end():
    segments = Segments()
    segments.update([Flag("illegal_turn", "car", 2.0, end=5.0)], 5.0)
    assert [e.tuple() for e in segments.finish(8)] == [[2.0, 5.0, "illegal_turn"]]
