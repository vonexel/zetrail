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