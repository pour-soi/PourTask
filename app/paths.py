from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path


def phase4_local_appdata() -> Path:
    return Path(os.environ.get("USERPROFILE", Path.home())) / "AppData" / "Local"


def stage43_stable_fixture_mode() -> bool:
    marker = Path(sys.executable).resolve().parent / ".pourtask-stage43-stable-fixture"
    return "--stage43-stable-fixture" in sys.argv or marker.is_file()


def phase4_test_mode() -> bool:
    marker = Path(sys.executable).resolve().parent / ".pourtask-phase4-installed"
    return os.environ.get("POURTASK_PHASE4_TEST") == "1" or "--pourupgrade-phase4-test" in sys.argv or marker.is_file()


@dataclass(frozen=True)
class AppPaths:
    root: Path

    @classmethod
    def default(cls) -> "AppPaths":
        if stage43_stable_fixture_mode():
            root = os.environ.get("POURTASK_STAGE43_STABLE_DATA_ROOT") or str(
                phase4_local_appdata() / "PourTask-Stage43-StableFixture"
            )
            return cls(Path(root).resolve())
        if phase4_test_mode():
            root = os.environ.get("POURTASK_PHASE4_DATA_ROOT") or str(phase4_local_appdata() / "PourTask-Phase4")
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
