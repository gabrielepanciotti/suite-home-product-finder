"""Shared test setup: backend on the pythonpath + throwaway sqlite DB.

The node's real DB is Postgres (:11120) but tests must run anywhere: we point
``DATABASE_URL`` at a file-based sqlite (aiosqlite) so the additive DB layer
is exercised for real (choice_log persistence) while ``information_schema``
queries — Postgres-only — degrade gracefully, which is itself part of the
/api/overview contract under test.
"""
from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# The FastAPI package lives in backend/ (not on the pythonpath by default).
sys.path.insert(0, str(ROOT / "backend"))

# One shared sqlite file for the whole test process (db.session_factory caches
# the engine globally, so every module must agree on the DSN).
_DB_FILE = Path(tempfile.gettempdir()) / f"hpf_test_{os.getpid()}.sqlite"
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_DB_FILE.as_posix()}"
