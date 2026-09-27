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
