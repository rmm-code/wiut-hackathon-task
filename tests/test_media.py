import cv2
import numpy as np
from vision.media import FrameReader


def video(tmp_path, frames=12):
    path = tmp_path / "clip.mp4"
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 10, (32, 32))
    for value in range(frames):
        writer.write(np.full((32, 32, 3), (value * 20) % 256, np.uint8))
    writer.release()
    return path


def test_reader_yields_every_index_in_order_and_skips_conversion(tmp_path):
    path = video(tmp_path)
    reader = FrameReader(path, lambda i: i % 4 == 0)
    try:
        items = list(reader)
    finally:
        reader.close()
    assert [i for i, _ in items] == list(range(12))
    assert [i for i, frame in items if frame is not None] == [0, 4, 8]
    # Kept frames are the same pixels a plain read loop returns.
    capture = cv2.VideoCapture(str(path))
    plain = [capture.read()[1] for _ in range(12)]
    capture.release()
    for index, frame in items:
        if frame is not None:
            assert np.array_equal(frame, plain[index])


def test_reader_closes_early_without_hanging(tmp_path):
    reader = FrameReader(video(tmp_path, 40), lambda i: True, depth=2)
    first = next(iter(reader))
    reader.close()
    assert first[0] == 0 and not reader.thread.is_alive()


def test_missing_file_ends_the_stream(tmp_path):
    reader = FrameReader(tmp_path / "missing.mp4", lambda i: True)
    try:
        assert list(reader) == []
    finally:
        reader.close()
