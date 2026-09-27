import cv2
import numpy as np
from vision.scene import Scene
from vision.settings import Settings
from vision.coverage import coverage


def test_camera_recognition_and_unrelated_frame_rejection():
    scene = Scene(Settings.load().camera())
    image = cv2.imread("web/public/images/camera.webp")
    assert scene.align(cv2.resize(image, (1920, 1080)))
    other = Scene(Settings.load().camera())
    assert not other.align(np.zeros((720, 1280, 3), np.uint8))
    assert not any(item["enabled"] for item in coverage(other, ["car", "person"]))


def test_islands_are_excluded_from_roadway():
    scene = Scene(Settings.load().camera())
    scene.matched = True
    assert not scene.on_road((0.15, 0.835))
    assert not scene.on_road((0.43, 0.80))


def test_class_coverage_follows_verified_scene_facts():
    scene = Scene(Settings.load().camera())
    scene.matched = True
    result = {item["label"]: item for item in coverage(scene, ["car", "person", "dog"])}
    assert result["jaywalking"]["enabled"]
    assert result["red_light"]["enabled"]
    # Enabled only through verified camera facts (clause 56 lanes, clause 62 crossings).
    assert result["illegal_turn"]["enabled"]
    assert result["illegal_u_turn"]["enabled"]
    assert not result["accident"]["enabled"]
    assert not result["fire_smoke"]["enabled"]


def test_c3902_aligns_without_weakening_camera_gate():
    scene = Scene(Settings.load().camera())
    frame = cv2.imread("tests/fixtures/c3902.png")
    # This dim frame sits on the inlier-fraction gate at 960x540: the first scale fails on
    # macOS and passes on Linux. Either way alignment must succeed, via the native-scale retry
    # if needed, and land on the same view.
    assert scene.align(frame)
    # The same fixed camera should map landmarks close to their original positions.
    assert np.allclose(scene.point((0.5, 0.5)), (0.5, 0.5), atol=0.035)
    assert not scene.align(np.zeros_like(frame))
    assert scene.matrix is None
    assert not any(item["enabled"] for item in coverage(scene, ["car", "person"]))


class FirstFramesHidden:
    """Stands in for Scene: frames darker than `threshold` fail to match."""

    def __init__(self, threshold):
        self.threshold, self.matched, self.tried = threshold, False, []

    def align(self, frame):
        self.tried.append(int(frame[0, 0, 0]))
        self.matched = frame[0, 0, 0] >= self.threshold
        return self.matched


def test_part_a_aligns_on_a_later_frame_when_the_first_is_hidden(tmp_path):
    from vision.pipeline import align

    path = tmp_path / "clip.mp4"
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 10, (64, 64))
    for position in range(50):
        writer.write(np.full((64, 64, 3), 5 * position, np.uint8))
    writer.release()
    scene = FirstFramesHidden(75)
    align(scene, np.zeros((64, 64, 3), np.uint8), path, 10)
    # The first frame, then one frame per second until one matches: 2 s in, value about 100.
    assert scene.matched and len(scene.tried) == 3 and abs(scene.tried[-1] - 100) <= 10
    unmatched = FirstFramesHidden(256)
    unmatched.align = lambda frame: unmatched.tried.append(1) or False
    align(unmatched, np.zeros((64, 64, 3), np.uint8), path, 10)
    assert len(unmatched.tried) == 5  # frames 0, 10, 20, 30, 40: the clip ends first


def test_part_b_retries_alignment_about_once_a_second(monkeypatch):
    from types import SimpleNamespace
    from vision.risk import RiskEstimator

    scene = FirstFramesHidden(15)
    monkeypatch.setattr("vision.scene.Scene", lambda *args: scene)
    monkeypatch.setattr(
        "vision.detector.Detector", lambda *args: SimpleNamespace(step=lambda frame: [])
    )
    estimator = RiskEstimator()
    estimator.reset({"fps": 8.0, "width": 2, "height": 2, "n_frames": 400})
    for index in range(400):
        # Pixel value = seconds x 10, so the scene matches from 1.5 s on.
        estimator.step(np.full((2, 2, 3), min(255, index * 10 // 8), np.uint8), index / 8)
    assert scene.matched and scene.tried == [0, 10, 20]
