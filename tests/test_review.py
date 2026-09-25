import json
import pytest
from fastapi.testclient import TestClient
from api.main import create_app
from api.review import validate_labels
from test_api import clip


def test_labels_reject_invalid_or_overlapping_intervals():
    for events in [
        [[True, 2, "accident"]],
        [[0, float("nan"), "accident"]],
        [[0, 4, []]],
        [[0, 11, "accident"]],
        [[1, 4, "accident"], [3, 5, "accident"]],
    ]:
        with pytest.raises(ValueError):
            validate_labels({"events": events}, 10)
    assert validate_labels({"events": [[1, 4, "accident"], [3, 5, "fire_smoke"]]}, 10)[
        "events"
    ]


def test_draft_cannot_be_exported_and_review_is_owned(tmp_path):
    app = create_app(tmp_path / "jobs", start_worker=False)
    with TestClient(app) as client:
        identity = client.post(
            "/api/jobs", files={"file": ("clip.mp4", clip(tmp_path), "video/mp4")}
        ).json()["id"]
        folder = tmp_path / "jobs" / identity
        (folder / "analysis.json").write_text(
            json.dumps({"meta": {"duration": 2, "fps": 10}})
        )
        app.state.store.update(identity, "complete")
        endpoint = f"/api/jobs/{identity}/labels"
        assert client.get(endpoint).json()["complete"] is False
        assert (
            client.put(endpoint, json={"events": [], "complete": True}).status_code
            == 400
        )
        assert (
            client.put(endpoint, json={"events": [[0, 1, "accident"]]}).status_code
            == 200
        )
        assert client.get(endpoint + "/export").status_code == 409
        body = {
            "events": [[0, 1, "accident"]],
            "complete": True,
            "reviewer": "Test reviewer",
            "reviewed_entire_video": True,
        }
        assert client.put(endpoint, json=body).status_code == 200
        assert client.get(endpoint + "/export").json()["clip.mp4"]["events"] == [
            [0, 1, "accident"]
        ]
        assert (
            client.put(
                endpoint, json=body, headers={"Origin": "https://evil.invalid"}
            ).status_code
            == 403
        )
        with TestClient(app) as other:
            assert other.get(endpoint).status_code == 404
            assert other.put(endpoint, json=body).status_code == 404
            assert other.get(f"/api/jobs/{identity}/source").status_code == 404


def test_chunked_body_is_limited_before_parser(tmp_path):
    app = create_app(tmp_path / "jobs", start_worker=False)
    with TestClient(app) as client:
        chunks = (b"x" * 300000 for _ in range(5))
        response = client.put("/api/jobs/" + "a" * 32 + "/labels", content=chunks)
        # Ownership is checked before reading for this invalid ID. Exercise body consumption directly below.
        assert response.status_code == 404
    import asyncio
    from api.limits import BodyLimit

    seen = []

    async def consume(scope, receive, send):
        while (await receive())["type"] != "http.disconnect":
            pass

    messages = iter(
        [{"type": "http.request", "body": b"x" * 600000, "more_body": True}] * 2
    )

    async def receive():
        return next(messages)

    async def send(message):
        seen.append(message)

    asyncio.run(
        BodyLimit(consume, 100)(
            {"type": "http", "method": "PUT", "headers": []}, receive, send
        )
    )
    assert [m["status"] for m in seen if m["type"] == "http.response.start"] == [413]
