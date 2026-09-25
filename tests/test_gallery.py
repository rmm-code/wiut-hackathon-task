import json
from fastapi.testclient import TestClient
from api.main import create_app


def test_public_samples_survive_job_expiry_and_need_no_owner(tmp_path, monkeypatch):
    monkeypatch.setattr("api.main.ROOT", tmp_path)
    folder = tmp_path / "artifacts/c3896"
    folder.mkdir(parents=True)
    analysis = {
        "meta": {"n_frames": 20, "decoded_frames": 20},
        "events": [[0, 1, "accident"]],
        "risk": [[0, 0.1]],
    }
    (folder / "analysis.json").write_text(json.dumps(analysis))
    (folder / "record.json").write_text("{}")
    (folder / "annotated.mp4").write_bytes(b"0123456789")
    (folder / "motion.jpg").write_bytes(b"image")
    app = create_app(tmp_path / "jobs", start_worker=False)
    app.state.store.expire()
    with TestClient(app) as client:
        result = client.get("/api/samples/c3896/results")
        assert result.status_code == 200
        assert result.json()["permanent"] is True
        assert result.json()["can_reanalyze"] is False
        assert result.json()["videos"]["C3896.MP4"]["events"] == analysis["events"]
        assert client.get("/api/samples/c3896/status").json()["progress"] == 1
        assert (
            client.get(
                "/api/samples/c3896/video", headers={"Range": "bytes=0-3"}
            ).status_code
            == 206
        )
        assert client.get("/api/samples/c3896/eda/motion").status_code == 200
        assert client.get("/api/samples/c3896/eda/secret").status_code == 404
        assert client.get("/api/samples/c9999/results").status_code == 404
        assert client.post("/api/samples/c3896/jobs").json()["id"] == "sample-c3896"
        assert client.get("/api/samples").json()[0]["archived"] is True
        assert (
            client.get("/api/downloads/predictions.json").json()["videos"]["C3896.MP4"][
                "events"
            ]
            == analysis["events"]
        )
        assert client.get("/api/jobs/" + "a" * 32 + "/results").status_code == 404


def test_gallery_does_not_publish_private_uploads(tmp_path, monkeypatch):
    monkeypatch.setattr("api.main.ROOT", tmp_path)
    app = create_app(tmp_path / "jobs", start_worker=False)
    with TestClient(app) as client:
        assert client.get("/api/samples/c3896/results").status_code == 404
        assert client.get("/api/downloads/predictions.json").status_code == 404
