import asyncio
import os
import shutil
import uuid
from fastapi import HTTPException, Request, Response
from starlette.concurrency import run_in_threadpool
from vision.media import metadata

SAMPLE_IDS = {
    "c3896": "C3896.MP4",
    "c3897": "C3897.MP4",
    "c3902": "C3902.MP4",
    "c3905": "C3905.MP4",
}


def sample_id(store, root, job):
    path = store.root / job["id"] / "input.mp4"
    for identity, name in SAMPLE_IDS.items():
        source = root / "samples" / name
        if path.is_file() and source.is_file() and path.samefile(source):
            return identity
    return None


def register_samples(app, store, root, owner, gallery=None):
    lock = asyncio.Lock()

    def existing(owner_id, name, source, force=False):
        if not owner_id:
            return None
        with store.connect() as db:
            rows = db.execute(
                "SELECT * FROM jobs WHERE owner=? AND filename=? "
                "AND state IN ('complete','running','queued') "
                "ORDER BY CASE state WHEN 'complete' THEN 0 ELSE 1 END, created DESC",
                (owner_id, name),
            ).fetchall()
        for row in rows:
            job = dict(row)
            folder = store.root / job["id"]
            path = folder / "input.mp4"
            if not path.is_file() or not path.samefile(source):
                continue
            if job["state"] == "complete":
                if force or not all(
                    (folder / file).is_file()
                    for file in ["analysis.json", "annotated.mp4"]
                ):
                    continue
            return job
        return None

    @app.get("/api/samples")
    def samples(request: Request):
        result = []
        for identity, name in SAMPLE_IDS.items():
            source = root / "samples" / name
            available = (
                source.is_file() and (root / "samples" / (name + ".ready")).is_file()
            )
            archived = bool(gallery and gallery.available(identity))
            job = existing(owner(request), name, source) if available else None
            result.append(
                {
                    "id": identity,
                    "name": name,
                    "available": available or archived,
                    "archived": archived,
                    "state": "complete" if archived else job["state"] if job else None,
                }
            )
        return result

    @app.post("/api/samples/{identity}/jobs", status_code=202)
    async def open_sample(
        identity: str, request: Request, response: Response, force: bool = False
    ):
        name = SAMPLE_IDS.get(identity)
        if name and not force and gallery and gallery.available(identity):
            response.status_code = 200
            return {"id": "sample-" + identity, "state": "complete", "reused": True}
        source = root / "samples" / (name or "")
        if (
            not name
            or not source.is_file()
            or not (root / "samples" / (name + ".ready")).is_file()
        ):
            raise HTTPException(
                404,
                "This sample has not been downloaded to the server yet. Use its original link or upload a short clip.",
            )
        async with lock:
            owner_id = owner(request, response)
            job = existing(owner_id, name, source, force)
            if job:
                response.status_code = 200
                return {"id": job["id"], "state": job["state"], "reused": True}
            job_id = uuid.uuid4().hex
            folder = store.root / job_id
            folder.mkdir()
            try:
                os.link(source, folder / "input.mp4")
                meta = await run_in_threadpool(metadata, source)
                store.create(job_id, owner_id, name, meta)
            except Exception as error:
                shutil.rmtree(folder, ignore_errors=True)
                raise HTTPException(400, str(error)) from error
            return {"id": job_id, "state": "queued", "meta": meta, "reused": False}
