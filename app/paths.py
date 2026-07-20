from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppPaths:
    root: Path

    @classmethod
    def default(cls) -> "AppPaths":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        return cls(base / "PourTask")

    @property
    def data(self) -> Path: return self.root / "data"
    @property
    def database(self) -> Path: return self.data / "pourtask.db"
    @property
    def backups(self) -> Path: return self.root / "backups"
    @property
    def logs(self) -> Path: return self.root / "logs"
    @property
    def settings(self) -> Path: return self.root / "settings.json"

    def ensure(self) -> None:
        for path in (self.data, self.backups, self.logs):
            path.mkdir(parents=True, exist_ok=True)
