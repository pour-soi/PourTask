from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class UndoAction:
    label: str
    callback: Callable[[], None]


class UndoService:
    def __init__(self):
        self._action: UndoAction | None = None

    @property
    def label(self) -> str:
        return self._action.label if self._action else ""

    def offer(self, label: str, callback: Callable[[], None]) -> None:
        self._action = UndoAction(label, callback)

    def undo(self) -> bool:
        action, self._action = self._action, None
        if action is None:
            return False
        action.callback()
        return True

    def clear(self) -> None:
        self._action = None
