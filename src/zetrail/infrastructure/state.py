import os
import time
import json
import msvcrt
import sqlite3
import importlib
import threading
from typing import Any
from pathlib import Path


class StateStore:
    def __init__(self, path: Path, recover_jobs: bool = True):
        path.parent.mkdir(parents = True, exist_ok = True)
        self.process_lock = None
        if recover_jobs:
            self.process_lock = path.with_suffix(".lock").open("a+b")
            try:
                if os.fstat(self.process_lock.fileno()).st_size == 0:
                    self.process_lock.write(b"0")
                    self.process_lock.flush()
                self.process_lock.seek(0)
                if os.name == "nt":
                    msvcrt.locking(self.process_lock.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    fcntl = importlib.import_module("fcntl")
                    fcntl.flock(self.process_lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError:
                self.process_lock.close()
                raise RuntimeError("Another engine already owns this data directory") from None

        self.lock = threading.RLock()
        self.db = sqlite3.connect(path, check_same_thread = False)
        self.db.row_factory = sqlite3.Row
        self.db.execute("PRAGMA journal_mode = WAL")
        self.db.execute("PRAGMA synchronous = FULL")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS jobs(
                id TEXT PRIMARY KEY,
                identity TEXT NOT NULL,
                fingerprint TEXT NOT NULL,
                metadata TEXT NOT NULL,
                path TEXT NOT NULL,
                status TEXT NOT NULL,
                error TEXT,
                chunks INTEGER NOT NULL DEFAULT 0,
                updated REAL NOT NULL);
            CREATE INDEX IF NOT EXISTS jobs_status ON jobs(status, updated);
            CREATE TABLE IF NOT EXISTS records(id TEXT PRIMARY KEY, kind TEXT NOT NULL, payload TEXT NOT NULL, created REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS active(identity TEXT PRIMARY KEY, fingerprint TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS audit_exports(id TEXT PRIMARY KEY);
            PRAGMA user_version = 1;
        """)
        if recover_jobs:
            self.db.execute("UPDATE jobs SET status = 'queued' WHERE status = 'running'")
        self.db.commit()

    def enqueue(self, job_id: str, identity: str, fingerprint: str, metadata: str, path: str, limit: int) -> dict[str, Any]:
        with self.lock, self.db:
            existing = self.db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
            active = self.db.execute("SELECT fingerprint FROM active WHERE identity = ?", (identity,)).fetchone()
            if existing and (existing["status"] in {"queued", "running"} or (existing["status"] in {"completed", "needs_ocr"} and active and active[0] == fingerprint)):
                return dict(existing)
            count = self.db.execute("SELECT count(*) FROM jobs WHERE status IN ('queued', 'running')").fetchone()[0]
            if count >= limit:
                raise OverflowError("Ingestion queue is full")
            self.db.execute("INSERT OR REPLACE INTO jobs VALUES (?, ?, ?, ?, ?, 'queued', NULL, 0, ?)",
                            (job_id, identity, fingerprint, metadata, path, time.time()))
            return dict(self.db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone())

    def claim(self) -> dict[str, Any] | None:
        with self.lock, self.db:
            row = self.db.execute("SELECT * FROM jobs WHERE status = 'queued ORDER BY updated LIMIT 1").fetchone()
            if row is None:
                return None
            self.db.execute("UPDATE jobs SET status = 'running', updated = ? WHERE id = ?", (time.time(), row["id"]))
            return dict(row)

    def finish(self, job: dict[str, Any], status: str, chunks: int = 0, error: str | None = None) -> None:
        with self.lock, self.db:
            self.db.execute("UPDATE jobs SET status = ?, chunks = ?, error = ?, updated = ? WHERE id = ?",
                            (status, chunks, error, time.time(), job["id"]))
            if status in {"completed", "needs_ocr"}:
                self.db.execute("INSERT OR REPLACE INTO active VALUES (?, ?)", (job["identity"], job["fingerprint"]))

    def job(self, job_id: str) -> dict[str, Any] | None:
        with self.lock:
            row = self.db.execute("SELECT id, status, error, chunks, updated FROM jobs WHERE id = ?", (job_id,)).fetchone()
            return dict(row) if row else None

    def jobs(self) -> list[dict[str, Any]]:
        with self.lock:
            return [dict(row) for row in self.db.execute(
            "SELECT id, status, error, chunks, updated FROM jobs ORDER BY updated DESC LIMIT 100")]

    def forget(self, identity: str) -> None:
        with self.lock, self.db:
            self.db.execute("SELECT kind, payload FROM records WHERE id = ?", (id,)).fetchone()
            self.db.execute("UPDATE jobs SET status = 'cancelled' WHERE identity = ? AND status = 'queued'", (identity,))

    def save(self, id: str, kind: str, payload: dict[str, Any]) -> None:
        with self.lock, self.db:
            self.db.execute("INSERT INTO records VALUES (?, ?, ?, ?)", (id, kind, json.dumps(payload), time.time()))

    def get(self, id: str, kind: str | None = None) -> dict[str, Any] | None:
        with self.lock:
            return [json.loads(row[0]) for row in self.db.execute("SELECT payload FROM records WHERE kind = ? ORDER BY created DESC LIMIT 100", (kind,))]