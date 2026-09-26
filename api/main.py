import hashlib
import json
import os
import re
import secrets
import shutil
import subprocess
import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, HTTPException, Request, Response, UploadFile
from fastapi.responses import FileResponse
from starlette.concurrency import run_in_threadpool
from vision.media import validate_upload
from vision.settings import ROOT, Settings
from .store import Store
from .worker import Worker
from .review import register_review
from .limits import BodyLimit
from .samples import register_samples, sample_id
from .gallery import Gallery, register_gallery
from .about import register_about


def create_app(storage=None, start_worker=True):
    store = Store(storage or os.getenv("CROSSING_STORAGE", ROOT / "storage"))
    worker = Worker(store)
    settings = Settings.load()
    allowed = {
        "http://127.0.0.1:5173",
        "http://localhost:5173",
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    }
    allowed.update(filter(None, os.getenv("CROSSING_ORIGINS", "").split(",")))

    @asynccontextmanager
    async def lifespan(app):
        for identity in store.expire():
            shutil.rmtree(store.root / identity, ignore_errors=True)
        if start_worker:
            worker.start()
        yield
        if start_worker:
            worker.close()

    app = FastAPI(title="Crossing API", lifespan=lifespan)
    app.state.store = store

    @app.middleware("http")
    async def protect(request: Request, call_next):
        if request.method in {"POST", "PUT", "DELETE"}:
            origin = request.headers.get("origin")
            if origin and origin not in allowed:
                from fastapi.responses import JSONResponse

                return JSONResponse(
                    {"detail": "This origin is not allowed."}, status_code=403
                )
            try:
                length = int(request.headers.get("content-length", "0"))
            except ValueError:
                length = settings.max_bytes + 1
            if length > settings.max_bytes + 1024 * 1024:
                from fastapi.responses import JSONResponse

                return JSONResponse(
                    {"detail": f"The upload exceeds {settings.max_bytes // 2**20} MB."}, status_code=413
                )
        response = await call_next(request)
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    def owner(request, response=None):
        token = request.cookies.get("crossing_owner")
        if not token and response is not None:
            token = secrets.token_urlsafe(32)
            response.set_cookie(
                "crossing_owner",
                token,
                httponly=True,
                samesite="strict",
                max_age=86400,
                path="/api",
            )
        return hashlib.sha256(token.encode()).hexdigest() if token else None

    def authorized(identity, request):
        if not re.fullmatch(r"[a-f0-9]{32}", identity):
            raise HTTPException(404, "Job not found.")
        job = store.get(identity)
        if not job or job["owner"] != owner(request):
            raise HTTPException(404, "Job not found.")
        return job

    @app.get("/api/health")
    def health():
        return {
            "ready": settings.weights.is_file() and bool(shutil.which("ffmpeg")),
            "model": settings.weights.name,
            "mode": "local-baseline",
            "calibration": "provisional",
        }

    register_review(app, store, authorized)

    @app.post("/api/jobs", status_code=202)
    async def submit(
        request: Request, response: Response, file: UploadFile = File(...)
    ):
        filename = (
            (file.filename or "video.mp4").replace("\\", "/").split("/")[-1][:180]
        )
        if not filename.lower().endswith(".mp4"):
            raise HTTPException(400, "Please upload an MP4 video.")
        if not settings.weights.is_file() or not shutil.which("ffmpeg"):
            raise HTTPException(
                503,
                "Model weights or ffmpeg are missing. Complete backend setup first.",
            )
        identity = uuid.uuid4().hex
        folder = store.root / identity
        folder.mkdir()
        try:
            total = 0
            with (folder / "input.mp4").open("wb") as dest:
                while chunk := await file.read(1024 * 1024):
                    total += len(chunk)
                    if total > settings.max_bytes:
                        raise HTTPException(
                            413, f"The upload exceeds {settings.max_bytes // 2**20} MB."
                        )
                    dest.write(chunk)
            meta = await run_in_threadpool(validate_upload, folder / "input.mp4")
            store.create(identity, owner(request, response), filename, meta)
            return {"id": identity, "state": "queued", "meta": meta}
        except HTTPException:
            shutil.rmtree(folder, ignore_errors=True)
            raise
        except (ValueError, TimeoutError, subprocess.TimeoutExpired) as error:
            shutil.rmtree(folder, ignore_errors=True)
            raise HTTPException(400, str(error)) from error
        except Exception:
            shutil.rmtree(folder, ignore_errors=True)
            raise
        finally:
            await file.close()

    @app.get("/api/jobs/{identity}")
    def status(identity: str, request: Request):
        job = authorized(identity, request)
        result = {
            "id": identity,
            "state": job["state"],
            "filename": job["filename"],
            "progress": 0,
            "stage": "Queued",
            "error": job["error"],
            "elapsed_sec": round(time.time() - job["created"], 1),
        }
        progress_file = store.root / identity / "progress.json"
        if progress_file.is_file():
            result.update(json.loads(progress_file.read_text()))
        if job["state"] == "complete":
            result.update(progress=1, stage="Analysis complete")
        elif job["state"] in {"failed", "cancelled"}:
            result["stage"] = job["state"].capitalize()
        return result

    @app.get("/api/jobs/{identity}/results")
    def results(identity: str, request: Request):
        job = authorized(identity, request)
        if job["state"] != "complete":
            raise HTTPException(409, "Results are not ready.")
        analysis = json.loads((store.root / identity / "analysis.json").read_text())
        return {
            "team": "wiut",
            "videos": {
                job["filename"]: {
                    "events": analysis["events"],
                    "risk": analysis["risk"],
                }
            },
            "analysis": {
                k: v for k, v in analysis.items() if k not in {"events", "risk"}
            },
            "video_url": f"/api/jobs/{identity}/video",
            "sample_id": sample_id(store, ROOT, job),
        }

    @app.get("/api/jobs/{identity}/video")
    def video(identity: str, request: Request):
        job = authorized(identity, request)
        if job["state"] != "complete":
            raise HTTPException(409, "Video is not ready.")
        return FileResponse(
            store.root / identity / "annotated.mp4",
            media_type="video/mp4",
            headers={"Cache-Control": "private, max-age=3600"},
        )

    @app.delete("/api/jobs/{identity}")
    def cancel(identity: str, request: Request):
        job = authorized(identity, request)
        if job["state"] in {"queued", "running"}:
            store.update(identity, "cancelled")
        return {"state": store.get(identity)["state"]}

    gallery = Gallery(ROOT)
    register_gallery(app, ROOT, gallery)
    register_about(app, ROOT, gallery)
    register_samples(app, store, ROOT, owner, gallery)

    app.add_middleware(BodyLimit, max_bytes=settings.max_bytes)
    return app


app = create_app()
