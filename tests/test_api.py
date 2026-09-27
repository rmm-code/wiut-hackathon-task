import shutil
import cv2
import numpy as np
import pytest
from fastapi.testclient import TestClient
from api.main import create_app
from vision.settings import Settings

# The website's upload endpoint needs ffmpeg/ffprobe and the downloaded weights; the
# offline submission needs neither ffmpeg nor this endpoint.
uploads = pytest.mark.skipif(
    not (shutil.which("ffmpeg") and shutil.which("ffprobe") and Settings.load().weights.is_file()),
    reason="upload endpoint needs ffmpeg, ffprobe and downloaded weights",
)


def clip(tmp_path):
    path = tmp_path / "clip.mp4"
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 10, (64, 64))
    for _ in range(20):
        writer.write(np.zeros((64, 64, 3), np.uint8))
    writer.release()
    return path.read_bytes()


@uploads
def test_upload_is_queued_owned_and_cancellable(tmp_path):
    app = create_app(tmp_path / "jobs", start_worker=False)
    with TestClient(app) as client:
        response = client.post(
            "/api/jobs", files={"file": ("clip.mp4", clip(tmp_path), "video/mp4")}
        )
        assert response.status_code == 202, response.text
        identity = response.json()["id"]
        assert client.get(f"/api/jobs/{identity}").json()["state"] == "queued"
        assert client.get(f"/api/jobs/{identity}/results").status_code == 409
        with TestClient(app) as other:
            assert other.get(f"/api/jobs/{identity}").status_code == 404
        assert client.delete(f"/api/jobs/{identity}").json()["state"] == "cancelled"


@uploads
def test_invalid_files_and_cross_origin_posts_are_rejected(tmp_path):
    with TestClient(create_app(tmp_path / "jobs", start_worker=False)) as client:
        assert (
            client.post(
                "/api/jobs", files={"file": ("bad.mp4", b"not a video", "video/mp4")}
            ).status_code
            == 400
        )
        assert (
            client.post("/api/jobs", files={"file": ("bad.exe", b"x")}).status_code
            == 400
        )
        assert (
            client.post(
                "/api/jobs",
                headers={"Origin": "https://untrusted.example"},
                files={"file": ("x.mp4", b"x")},
            ).status_code
            == 403
        )
        assert not list((tmp_path / "jobs").glob("*/input.mp4"))


@uploads
def test_large_upload_arrives_in_pieces_resumes_and_is_cancellable(tmp_path):
    data = clip(tmp_path)
    half = len(data) // 2
    with TestClient(create_app(tmp_path / "jobs", start_worker=False)) as client:
        begin = client.post("/api/uploads", json={"filename": "big.mp4", "size": len(data)})
        assert begin.status_code == 201, begin.text
        identity = begin.json()["id"]
        assert client.get(f"/api/jobs/{identity}").json()["state"] == "uploading"
        piece = lambda offset, body: client.post(
            f"/api/uploads/{identity}?offset={offset}",
            content=body,
            headers={"Content-Type": "application/octet-stream"},
        )
        assert client.post(f"/api/uploads/{identity}/complete").status_code == 409
        assert piece(0, data[:half]).json() == {"received": half}
        # A retried piece is acknowledged without being written twice; a gap is refused.
        assert piece(0, data[:half]).json() == {"received": half}
        assert piece(half + 1, data[half + 1 :]).status_code == 409
        with TestClient(client.app) as other:
            assert other.post(f"/api/uploads/{identity}?offset={half}", content=b"x").status_code == 404
        assert piece(half, data[half:]).json() == {"received": len(data)}
        done = client.post(f"/api/uploads/{identity}/complete")
        assert done.status_code == 202, done.text
        assert client.get(f"/api/jobs/{identity}").json()["state"] == "queued"
        assert (tmp_path / "jobs" / identity / "input.mp4").read_bytes() == data

        second = client.post("/api/uploads", json={"filename": "b.mp4", "size": len(data)}).json()["id"]
        assert client.delete(f"/api/jobs/{second}").json()["state"] == "cancelled"
        assert not (tmp_path / "jobs" / second / "input.part").exists()


@uploads
def test_large_uploads_are_bounded_and_checked(tmp_path):
    with TestClient(create_app(tmp_path / "jobs", start_worker=False)) as client:
        too_big = Settings.load().max_upload_bytes + 1
        assert client.post("/api/uploads", json={"filename": "a.mp4", "size": too_big}).status_code == 413
        assert client.post("/api/uploads", json={"filename": "a.exe", "size": 10}).status_code == 400
        assert (
            client.post(
                "/api/uploads",
                headers={"Origin": "https://untrusted.example"},
                json={"filename": "a.mp4", "size": 10},
            ).status_code
            == 403
        )
        identity = client.post("/api/uploads", json={"filename": "a.mp4", "size": 11}).json()["id"]
        assert client.post(
            f"/api/uploads/{identity}?offset=0", content=b"not a video"
        ).json() == {"received": 11}
        failed = client.post(f"/api/uploads/{identity}/complete")
        assert failed.status_code == 400
        assert client.get(f"/api/jobs/{identity}").json()["state"] == "failed"
        assert not list((tmp_path / "jobs").glob("*/input.*"))
        # The queue limit is reported before any piece is sent.
        for _ in range(3):
            assert client.post("/api/uploads", json={"filename": "a.mp4", "size": 10}).status_code == 201
        assert client.post("/api/uploads", json={"filename": "a.mp4", "size": 10}).status_code == 429
