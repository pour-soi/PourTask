from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path

SCHEMA_VERSION = 1


def migrate(connection: sqlite3.Connection) -> None:
    schema = Path(__file__).with_name("schema.sql").read_text(encoding="utf-8")
    with connection:
        connection.executescript(schema)
        current = connection.execute("SELECT COALESCE(MAX(version), 0) FROM schema_version").fetchone()[0]
        if current < SCHEMA_VERSION:
            connection.execute(
                "INSERT INTO schema_version(version, applied_at) VALUES (?, ?)",
                (SCHEMA_VERSION, datetime.now(timezone.utc).isoformat()),
            )
