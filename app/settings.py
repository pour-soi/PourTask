from __future__ import annotations

import json
from pathlib import Path

DEFAULTS = {
    "close_behavior": "exit",
    "launch_at_startup": False,
    "widget_enabled": False,
    "window_geometry": None,
    "window_maximized": False,
    "main_splitters": None,
    "editor_collapsed": False,
    "widget_geometry": None,
    "widget_compact": False,
    "widget_expanded_size": {"width": 260, "height": 180},
    "widget_always_on_top": False,
    "widget_lock_position": False,
}


class Settings:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.values = dict(DEFAULTS)
        self.load()

    def load(self) -> None:
        try:
            loaded = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                self.values.update({key: loaded[key] for key in DEFAULTS if key in loaded})
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            pass

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(self.values, indent=2), encoding="utf-8")
        temporary.replace(self.path)
