import json
import sqlite3
import time
from pathlib import Path


class Store:
    def __init__(self, root):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.database = self.root / "jobs.sqlite"
        with self.connect() as db:
            db.execute("PRAGMA journal_mode=WAL")
            db.execute("""CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY, owner TEXT NOT NULL, filename TEXT NOT NULL,
                state TEXT NOT NULL, created REAL NOT NULL, updated REAL NOT NULL,
                error TEXT, meta TEXT NOT NULL DEFAULT '{}')""")

    def connect(self):
        db = sqlite3.connect(self.database, timeout=10)
        db.row_factory = sqlite3.Row
        return db

    def create(self, identity, owner, filename, meta):
        now = time.time()
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            count = db.execute(
                "SELECT COUNT(*) FROM jobs WHERE state IN ('queued','running')"
            ).fetchone()[0]
            if count >= 3:
                raise ValueError(
                    "The analysis queue is full. Please try again after a job finishes."
                )
            db.execute(
                "INSERT INTO jobs (id,owner,filename,state,created,updated,meta) VALUES (?,?,?,'queued',?,?,?)",
                (identity, owner, filename, now, now, json.dumps(meta)),
            )

    def reserve(self, identity, owner, filename, size):
        """Open a chunked upload. Uploads count toward the queue limit, so a full queue
        is reported before the pieces are sent, not after."""
        now = time.time()
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            count = db.execute(
                "SELECT COUNT(*) FROM jobs WHERE state IN ('uploading','queued','running')"
            ).fetchone()[0]
            if count >= 3:
                raise ValueError(
                    "The analysis queue is full. Please try again after a job finishes."
                )
            db.execute(
                "INSERT INTO jobs (id,owner,filename,state,created,updated,meta) VALUES (?,?,?,'uploading',?,?,?)",
                (identity, owner, filename, now, now, json.dumps({"size": size})),
            )

    def reserved_bytes(self):
        with self.connect() as db:
            rows = db.execute("SELECT meta FROM jobs WHERE state='uploading'").fetchall()
        return sum(json.loads(row["meta"]).get("size", 0) for row in rows)

    def touch(self, identity):
        with self.connect() as db:
            db.execute("UPDATE jobs SET updated=? WHERE id=?", (time.time(), identity))

    def queue(self, identity, meta):
        with self.connect() as db:
            db.execute(
                "UPDATE jobs SET state='queued',meta=?,updated=? WHERE id=? AND state='uploading'",
                (json.dumps(meta), time.time(), identity),
            )

    def get(self, identity):
        with self.connect() as db:
            row = db.execute("SELECT * FROM jobs WHERE id=?", (identity,)).fetchone()
            return dict(row) if row else None

    def next(self):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT * FROM jobs WHERE state='queued' ORDER BY created LIMIT 1"
            ).fetchone()
            if row:
                db.execute(
                    "UPDATE jobs SET state='running',updated=? WHERE id=? AND state='queued'",
                    (time.time(), row["id"]),
                )
                return dict(row)
        return None

    def update(self, identity, state, error=None):
        with self.connect() as db:
            db.execute(
                "UPDATE jobs SET state=?,error=?,updated=? WHERE id=?",
                (state, error, time.time(), identity),
            )

    def recover(self):
        with self.connect() as db:
            db.execute(
                "UPDATE jobs SET state='failed',error='The server restarted during analysis. Please resubmit.',updated=? WHERE state='running'",
                (time.time(),),
            )

    def expire(self):
        """Jobs older than a day, and uploads that received nothing for an hour."""
        now = time.time()
        with self.connect() as db:
            rows = db.execute(
                "SELECT id FROM jobs WHERE (created<? AND state NOT IN ('uploading','queued','running')) "
                "OR (state='uploading' AND updated<?)",
                (now - 86400, now - 3600),
            ).fetchall()
            db.executemany("DELETE FROM jobs WHERE id=?", [(r["id"],) for r in rows])
        return [row["id"] for row in rows]
