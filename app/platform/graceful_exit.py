from __future__ import annotations

import logging

from PySide6.QtCore import QObject, QTimer, Slot


class GracefulExitController(QObject):
    """Runs application cleanup once, then terminates the Qt event loop."""

    def __init__(self, application):
        super().__init__(application)
        self.application = application
        self._cleanup_callbacks = []
        self._requested = False
        self._cleaned = False

    def add_cleanup(self, callback) -> None:
        if self._cleaned:
            callback()
            return
        self._cleanup_callbacks.append(callback)

    @property
    def requested(self) -> bool:
        return self._requested

    @Slot()
    def request_exit(self) -> None:
        if self._requested:
            return
        self._requested = True
        self.cleanup()
        QTimer.singleShot(0, self.application.quit)

    @Slot()
    def cleanup(self) -> None:
        if self._cleaned:
            return
        self._cleaned = True
        for callback in self._cleanup_callbacks:
            try:
                callback()
            except Exception:
                logging.exception("Graceful exit cleanup failed")
