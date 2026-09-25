import json
import math
import time
from fastapi import HTTPException, Request
from fastapi.responses import FileResponse
from vision.pipeline import write_json
from vision.types import CLASSES


def validate_labels(body, duration):
    if (
        not isinstance(body, dict)
        or not isinstance(body.get("events"), list)
        or len(body["events"]) > 10000
    ):
        raise ValueError("Provide an events list with at most 10,000 entries.")
    result = []
    for row in body["events"]:
        if not isinstance(row, list) or len(row) != 3:
            raise ValueError("Each event must contain start, end, and class.")
        start, end, label = row
        if (
            isinstance(start, bool)
            or isinstance(end, bool)
            or not isinstance(start, (int, float))
            or not isinstance(end, (int, float))
        ):
            raise ValueError("Event timestamps must be numeric.")
        if (
            not math.isfinite(start)
            or not math.isfinite(end)
            or not 0 <= start < end <= duration
        ):
            raise ValueError("Event timestamps must fall within the video.")
        if not isinstance(label, str) or label not in CLASSES:
            raise ValueError("Unknown event class.")
        result.append([float(start), float(end), label])
    last = {}
    for start, end, label in sorted(result, key=lambda row: (row[2], row[0])):
        if start < last.get(label, -1):
            raise ValueError(
                "Events of the same class cannot overlap; combine their intervals."
            )
        last[label] = end
    reviewer = str(body.get("reviewer", "")).strip()[:120]
    complete = body.get("complete") is True
    if complete and (not reviewer or body.get("reviewed_entire_video") is not True):
        raise ValueError(
            "Finalization requires your name and confirmation that you reviewed the entire video."
        )
    return {
        "events": sorted(result),
        "reviewer": reviewer,
        "complete": complete,
        "reviewed_entire_video": body.get("reviewed_entire_video") is True,
        "notes": str(body.get("notes", ""))[:4000],
        "updated": time.time(),
        "source": "manual_review",
    }


def register_review(app, store, authorized):
    @app.get("/api/jobs/{identity}/source")
    def source(identity: str, request: Request):
        job = authorized(identity, request)
        path = store.root / identity / "source.mp4"
        if job["state"] != "complete" or not path.is_file():
            raise HTTPException(
                409,
                "Re-run this video with the current engine to create a clean review copy.",
            )
        return FileResponse(
            path,
            media_type="video/mp4",
            headers={"Cache-Control": "private, max-age=3600"},
        )

    @app.get("/api/jobs/{identity}/eda/{kind}")
    def eda(identity: str, kind: str, request: Request):
        job = authorized(identity, request)
        if (
            kind not in {"occupancy", "motion", "trajectories"}
            or job["state"] != "complete"
        ):
            raise HTTPException(404, "Artifact not found.")
        path = store.root / identity / (kind + ".jpg")
        if not path.is_file():
            raise HTTPException(404, "Artifact not available for this run.")
        return FileResponse(path, media_type="image/jpeg")

    @app.get("/api/jobs/{identity}/labels")
    def labels(identity: str, request: Request):
        authorized(identity, request)
        path = store.root / identity / "labels.json"
        return (
            json.loads(path.read_text())
            if path.exists()
            else {
                "events": [],
                "complete": False,
                "reviewer": "",
                "notes": "",
                "reviewed_entire_video": False,
            }
        )

    @app.put("/api/jobs/{identity}/labels")
    async def save_labels(identity: str, request: Request):
        job = authorized(identity, request)
        if job["state"] != "complete":
            raise HTTPException(409, "Analysis is not complete.")
        analysis = json.loads((store.root / identity / "analysis.json").read_text())
        try:
            review = validate_labels(await request.json(), analysis["meta"]["duration"])
        except (ValueError, TypeError) as error:
            raise HTTPException(400, str(error)) from error
        review.update(
            filename=job["filename"],
            duration=analysis["meta"]["duration"],
            fps=analysis["meta"]["fps"],
        )
        write_json(store.root / identity / "labels.json", review)
        return review

    @app.get("/api/jobs/{identity}/labels/export")
    def export(identity: str, request: Request):
        job = authorized(identity, request)
        path = store.root / identity / "labels.json"
        if not path.is_file():
            raise HTTPException(409, "No labels have been saved.")
        review = json.loads(path.read_text())
        if not review["complete"]:
            raise HTTPException(
                409,
                "Draft labels cannot be exported as ground truth. Finish the review first.",
            )
        return {
            job["filename"]: {
                "duration": review["duration"],
                "fps": review["fps"],
                "events": review["events"],
            }
        }
