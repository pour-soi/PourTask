from __future__ import annotations

import shutil
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

from app.database import Database


class BackupError(RuntimeError):
    pass


class BackupService:
    def __init__(self, database: Database, backup_folder: Path):
        self.database = database
        self.backup_folder = Path(backup_folder)

    @staticmethod
    def _validate(path: Path) -> None:
        try:
            with closing(sqlite3.connect(f"file:{path}?mode=ro", uri=True)) as connection:
                result = connection.execute("PRAGMA integrity_check").fetchone()[0]
                columns = {row[1] for row in connection.execute("PRAGMA table_info(tasks)")}
                version = connection.execute("SELECT MAX(version) FROM schema_version").fetchone()[0]
        except sqlite3.Error as exc:
            raise BackupError("The selected backup is not a readable PourTask database.") from exc
        required = {"id", "title", "notes", "scheduled_date", "due_date", "assigned_month", "completed"}
        if result != "ok" or not required.issubset(columns) or version != 1:
            raise BackupError("The selected backup failed validation.")

    def export(self, destination: Path | None = None) -> Path:
        self.backup_folder.mkdir(parents=True, exist_ok=True)
        destination = destination or self.backup_folder / f"PourTask-backup-{datetime.now():%Y%m%d-%H%M%S}.db"
        with closing(self.database.connect()) as source, closing(sqlite3.connect(destination)) as target:
            source.backup(target); target.commit()
        self._validate(destination)
        return destination

    def replace(self, imported: Path) -> Path:
        imported = Path(imported)
        self._validate(imported)
        safety = self.export()
        temporary = self.database.path.with_suffix(".importing")
        shutil.copy2(imported, temporary)
        self._validate(temporary)
        temporary.replace(self.database.path)
        return safety
