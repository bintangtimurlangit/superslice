"""Opt-in slicing history, persisted to SQLite.

Stores a record of each slice — the parameters and the resulting estimates —
never the uploaded model files. Disabled by default; enabled with
``HISTORY_ENABLED=true``. All functions are no-ops / empty when disabled.
"""
import sqlite3
import threading
from datetime import datetime, timezone
from typing import List, Optional

from ..config import HISTORY_DB_PATH, HISTORY_ENABLED

_conn: Optional[sqlite3.Connection] = None
_lock = threading.Lock()

_SCHEMA = """
CREATE TABLE IF NOT EXISTS slices (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at         TEXT    NOT NULL,
    filename           TEXT,
    layer_height       REAL    NOT NULL,
    infill_density     INTEGER NOT NULL,
    wall_count         INTEGER NOT NULL,
    filament_type      TEXT    NOT NULL,
    print_time_seconds INTEGER NOT NULL,
    filament_length_mm REAL    NOT NULL,
    filament_volume_cm3 REAL   NOT NULL,
    filament_weight_g  REAL    NOT NULL
)
"""


def init() -> None:
    """Open the database and ensure the schema exists. Idempotent."""
    global _conn
    if not HISTORY_ENABLED or _conn is not None:
        return
    HISTORY_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    _conn = sqlite3.connect(str(HISTORY_DB_PATH), check_same_thread=False)
    _conn.row_factory = sqlite3.Row
    with _lock:
        _conn.execute(_SCHEMA)
        _conn.commit()


def enabled() -> bool:
    return HISTORY_ENABLED and _conn is not None


def record(params, response, filename: Optional[str]) -> None:
    """Persist one slice. No-op when history is disabled."""
    if not enabled():
        return
    with _lock:
        _conn.execute(
            """INSERT INTO slices (
                created_at, filename, layer_height, infill_density, wall_count,
                filament_type, print_time_seconds, filament_length_mm,
                filament_volume_cm3, filament_weight_g
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                datetime.now(timezone.utc).isoformat(timespec="seconds"),
                filename,
                params.layer_height,
                params.infill_density,
                params.wall_count,
                response.filament_type,
                int(response.print_time_minutes * 60),
                response.filament_length_mm,
                response.filament_volume_cm3,
                response.filament_weight_g,
            ),
        )
        _conn.commit()


def list_records(limit: int = 50, offset: int = 0) -> List[dict]:
    if not enabled():
        return []
    with _lock:
        rows = _conn.execute(
            "SELECT * FROM slices ORDER BY id DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
    return [dict(r) for r in rows]


def get_record(record_id: int) -> Optional[dict]:
    if not enabled():
        return None
    with _lock:
        row = _conn.execute("SELECT * FROM slices WHERE id = ?", (record_id,)).fetchone()
    return dict(row) if row else None


def count() -> int:
    if not enabled():
        return 0
    with _lock:
        return _conn.execute("SELECT COUNT(*) AS n FROM slices").fetchone()["n"]


def _reset_for_tests() -> None:
    """Close the connection so tests can re-init against a fresh path."""
    global _conn
    if _conn is not None:
        _conn.close()
        _conn = None
