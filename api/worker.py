import json
import subprocess
import sys
import threading
import time
import shutil
from vision.settings import ROOT


class Worker:
    def __init__(self, store):
        self.store = store
        self.stop = threading.Event()
        self.thread = threading.Thread(
            target=self.run, name="analysis-worker", daemon=True
        )
        self.process = None

    def start(self):
        self.store.recover()
        self.thread.start()

    def close(self):
        self.stop.set()
        if self.process and self.process.poll() is None:
            self.process.terminate()
        self.thread.join(timeout=8)

    def run(self):
        last_cleanup = 0
        while not self.stop.is_set():
            if time.monotonic() - last_cleanup > 60:
                for identity in self.store.expire():
                    shutil.rmtree(self.store.root / identity, ignore_errors=True)
                last_cleanup = time.monotonic()
            job = self.store.next()
            if not job:
                self.stop.wait(0.5)
                continue
            folder = self.store.root / job["id"]
            started = time.monotonic()
            try:
                with (folder / "worker.log").open("wb") as log:
                    self.process = subprocess.Popen(
                        [
                            sys.executable,
                            "-m",
                            "vision.cli",
                            str(folder / "input.mp4"),
                            "--output",
                            str(folder),
                        ],
                        cwd=ROOT,
                        stdout=log,
                        stderr=log,
                    )
                    while self.process.poll() is None:
                        current = self.store.get(job["id"])
                        if (
                            self.stop.is_set()
                            or current["state"] == "cancelled"
                            or time.monotonic() - started > 2700
                        ):
                            self.process.terminate()
                            try:
                                self.process.wait(timeout=5)
                            except subprocess.TimeoutExpired:
                                self.process.kill()
                                self.process.wait()
                            if current["state"] != "cancelled":
                                self.store.update(
                                    job["id"],
                                    "failed",
                                    "Analysis stopped or exceeded the 45-minute limit.",
                                )
                            break
                        self.stop.wait(0.4)
                    current = self.store.get(job["id"])
                    if current["state"] == "running":
                        if (
                            self.process.returncode == 0
                            and (folder / "analysis.json").is_file()
                        ):
                            json.loads((folder / "analysis.json").read_text())
                            self.store.update(job["id"], "complete")
                        else:
                            self.store.update(
                                job["id"],
                                "failed",
                                "The analysis process failed. Check the local job log for details.",
                            )
            except Exception:
                self.store.update(
                    job["id"],
                    "failed",
                    "The analysis worker could not finish this video.",
                )
            finally:
                self.process = None
                # An uploaded original can be gigabytes; the results and the review copy
                # stay. Sample jobs hard-link the organizer video and reuse it, so they keep it.
                source = folder / "input.mp4"
                if source.is_file() and source.stat().st_nlink == 1:
                    source.unlink()
