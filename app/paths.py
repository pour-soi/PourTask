from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class AppPaths:
    root: Path

    @classmethod
    def default(cls) -> "AppPaths":
        installed_test_marker = (Path(sys.executable).resolve().parent / ".pourtask-phase4-installed").is_file()
        if os.environ.get("POURTASK_PHASE4_TEST") == "1" or "--pourupgrade-phase4-test" in sys.argv or installed_test_marker:
            profile = Path(os.environ.get("USERPROFILE", Path.home()))
            root = os.environ.get("POURTASK_PHASE4_DATA_ROOT") or str(profile / "AppData" / "Local" / "PourTask-Phase4")
            return cls(Path(root).resolve())
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
