import json
import os
from pathlib import Path
from fastapi import HTTPException
from fastapi.responses import FileResponse
from .samples import SAMPLE_IDS


class Gallery:
    def __init__(self, root):
        self.root = Path(os.getenv("CROSSING_ARCHIVE", root / "artifacts"))

    def folder(self, identity):
        if identity not in SAMPLE_IDS:
            raise HTTPException(404, "Unknown sample.")
        return self.root / identity

    def available(self, identity):
        folder = self.folder(identity)
        return all(
            (folder / name).is_file()
            for name in ["analysis.json", "annotated.mp4", "record.json"]
        )

    def analysis(self, identity):
        if not self.available(identity):
            raise HTTPException(404, "This sample has not been archived yet.")
        return json.loads((self.folder(identity) / "analysis.json").read_text())


def register_gallery(app, root, gallery):
    @app.get("/api/samples/{identity}/status")
    def status(identity: str):
        analysis = gallery.analysis(identity)
        return {
            "id": "sample-" + identity,
            "state": "complete",
            "progress": 1,
            "stage": "Saved sample analysis",
            "filename": SAMPLE_IDS[identity],
            "processed_frames": analysis["meta"]["decoded_frames"],
            "total_frames": analysis["meta"]["n_frames"],
        }

    @app.get("/api/samples/{identity}/results")
    def results(identity: str):
        analysis = gallery.analysis(identity)
        return {
            "team": "pitstop",
            "sample_id": identity,
            "permanent": True,
            "can_reanalyze": (root / "samples" / SAMPLE_IDS[identity]).is_file(),
            "videos": {
                SAMPLE_IDS[identity]: {
                    "events": analysis["events"],
                    "risk": analysis["risk"],
                }
            },
            "analysis": {
                k: v for k, v in analysis.items() if k not in {"events", "risk"}
            },
            "video_url": f"/api/samples/{identity}/video",
        }

    @app.get("/api/samples/{identity}/video")
    def video(identity: str):
        gallery.analysis(identity)
        return FileResponse(
            gallery.folder(identity) / "annotated.mp4", media_type="video/mp4"
        )

    @app.get("/api/samples/{identity}/eda/{kind}")
    def eda(identity: str, kind: str):
        if kind not in {"occupancy", "motion", "trajectories", "poster"}:
            raise HTTPException(404, "Unknown map.")
        path = gallery.folder(identity) / (kind + ".jpg")
        if not path.is_file():
            raise HTTPException(404, "Map unavailable.")
        return FileResponse(path, media_type="image/jpeg")

    @app.get("/api/downloads/predictions.json")
    def predictions():
        videos = {}
        for identity, name in SAMPLE_IDS.items():
            if gallery.available(identity):
                analysis = gallery.analysis(identity)
                videos[name] = {k: analysis[k] for k in ["events", "risk"]}
        if not videos:
            raise HTTPException(404, "No archived predictions available.")
        from fastapi.responses import JSONResponse

        return JSONResponse(
            {"team": "pitstop", "videos": videos},
            headers={
                "Content-Disposition": 'attachment; filename="predictions_samples.json"'
            },
        )

    @app.get("/api/downloads/weights.json")
    def weights():
        return FileResponse(
            root / "weights/manifest.json",
            filename="weights.json",
            media_type="application/json",
        )
