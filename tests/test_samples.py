import json
from concurrent.futures import ThreadPoolExecutor
from fastapi.testclient import TestClient
from api.main import create_app
from test_api import clip


def setup_sample(tmp_path, monkeypatch):
    samples = tmp_path / "samples"
    samples.mkdir()
    (samples / "C3905.MP4").write_bytes(clip(tmp_path))
    (samples / "C3905.MP4.ready").write_text("{}")
    monkeypatch.setattr("api.main.ROOT", tmp_path)
    return create_app(tmp_path / "jobs", start_worker=False)


def complete(app, identity):
    folder = app.state.store.root / identity
    (folder / "analysis.json").write_text(
        json.dumps({"events": [], "risk": [], "meta": {"duration": 2}})
    )
    (folder / "annotated.mp4").write_bytes(b"video")
    (folder / "progress.json").write_text(
        json.dumps(
            {
                "progress": 0.99,
                "stage": "Finalizing video",
                "processed_frames": 20,
                "total_frames": 20,
            }
        )
    )
    app.state.store.update(identity, "complete")


def test_sample_reuses_complete_results_and_requires_explicit_rerun(
    tmp_path, monkeypatch
):
    app = setup_sample(tmp_path, monkeypatch)
    with TestClient(app) as client:
        first = client.post("/api/samples/c3905/jobs").json()["id"]
        assert client.post("/api/samples/c3905/jobs").json()["id"] == first
        complete(app, first)
        response = client.post("/api/samples/c3905/jobs")
        assert response.status_code == 200
        assert response.json() == {"id": first, "state": "complete", "reused": True}
        assert client.get(f"/api/jobs/{first}").json()["progress"] == 1
        assert client.get(f"/api/jobs/{first}/results").json()["sample_id"] == "c3905"
        assert client.get("/api/samples").json()[-1]["state"] == "complete"
        second = client.post("/api/samples/c3905/jobs?force=true").json()["id"]
        assert first != second
        assert client.post("/api/samples/c3905/jobs?force=true").json()["id"] == second
        assert client.post("/api/samples/c3905/jobs").json()["id"] == first
        client.delete(f"/api/jobs/{second}")
        assert client.get(f"/api/jobs/{first}").json()["state"] == "complete"


def test_cache_is_owner_scoped_and_not_based_on_uploaded_filename(
    tmp_path, monkeypatch
):
    app = setup_sample(tmp_path, monkeypatch)
    with TestClient(app) as client:
        uploaded = client.post(
            "/api/jobs", files={"file": ("C3905.MP4", clip(tmp_path), "video/mp4")}
        ).json()["id"]
        complete(app, uploaded)
        assert client.get(f"/api/jobs/{uploaded}/results").json()["sample_id"] is None
        first = client.post("/api/samples/c3905/jobs").json()["id"]
        assert first != uploaded
        complete(app, first)
        with TestClient(app) as other:
            second = other.post("/api/samples/c3905/jobs").json()["id"]
            assert first != second
            assert other.get(f"/api/jobs/{first}/results").status_code == 404


def test_concurrent_clicks_create_one_job_and_missing_artifacts_rerun(
    tmp_path, monkeypatch
):
    app = setup_sample(tmp_path, monkeypatch)
    with TestClient(app) as client:
        # Establish the same owner before simultaneous requests.
        first = client.post("/api/samples/c3905/jobs").json()["id"]
        complete(app, first)
        with ThreadPoolExecutor(max_workers=2) as pool:
            ids = list(
                pool.map(
                    lambda _: client.post("/api/samples/c3905/jobs?force=true").json()[
                        "id"
                    ],
                    range(2),
                )
            )
        assert ids[0] == ids[1]
        app.state.store.update(ids[0], "cancelled")
        (app.state.store.root / first / "analysis.json").unlink()
        assert client.post("/api/samples/c3905/jobs").json()["id"] != first
