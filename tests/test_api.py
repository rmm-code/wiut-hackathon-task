import cv2
import numpy as np
from fastapi.testclient import TestClient
from api.main import create_app


def clip(tmp_path):
    path = tmp_path / "clip.mp4"
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 10, (64, 64))
    for _ in range(20):
        writer.write(np.zeros((64, 64, 3), np.uint8))
    writer.release()
    return path.read_bytes()


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
