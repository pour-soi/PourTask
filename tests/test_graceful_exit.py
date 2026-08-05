from __future__ import annotations

import base64
import json
import os
import sqlite3
import struct
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from PySide6.QtCore import QObject, QTimer, QUrl
from PySide6.QtGui import QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QSystemTrayIcon

from app.platform.graceful_exit import GracefulExitController
from app.platform.single_instance import SingleInstanceGuard
from app.platform.tray import create_tray
from app.settings import Settings
from app.strings import STRINGS
from app.viewmodels import AppViewModel
from app.viewmodels.settings_viewmodel import SettingsViewModel


class FakeApplication(QObject):
    def __init__(self):
        super().__init__(); self.quit_calls = 0

    def quit(self):
        self.quit_calls += 1


def _wait(predicate, timeout=2):
    application = QApplication.instance() or QApplication([])
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        application.processEvents()
        if predicate(): return
        time.sleep(.01)
    raise AssertionError("Qt condition did not complete within the timeout")


def test_repeated_exit_runs_cleanup_and_quit_once():
    QApplication.instance() or QApplication([])
    application = FakeApplication(); events = []
    controller = GracefulExitController(application)
    controller.add_cleanup(lambda: events.append("saved"))
    controller.request_exit(); controller.request_exit()
    _wait(lambda: application.quit_calls == 1)
    assert events == ["saved"] and controller.requested


def test_active_timer_and_single_instance_listener_are_closed():
    QApplication.instance() or QApplication([])
    application = FakeApplication(); controller = GracefulExitController(application)
    timer = QTimer(); timer.start(1000)
    name = f"PourTask.Exit.Test.{uuid4().hex}"
    guard = SingleInstanceGuard(name); assert guard.acquire()
    controller.add_cleanup(timer.stop); controller.add_cleanup(guard.close)
    controller.request_exit(); _wait(lambda: application.quit_calls == 1)
    assert not timer.isActive() and not guard.server.isListening()
    replacement = SingleInstanceGuard(name)
    try: assert replacement.acquire()
    finally: replacement.close()


def test_tray_exit_uses_graceful_controller(monkeypatch):
    application = QApplication.instance() or QApplication([])
    monkeypatch.setattr(QSystemTrayIcon, "isSystemTrayAvailable", lambda: True)
    controller = GracefulExitController(application)
    requested = []; controller.request_exit = lambda: requested.append(True)
    tray = create_tray(application, QIcon(), lambda: None, lambda: None, controller.request_exit)
    assert tray is not None
    exit_action = next(action for action in tray.contextMenu().actions() if action.text() == "Exit")
    exit_action.trigger(); _wait(lambda: requested == [True])
    tray.hide()


def _qml_window(repository, tmp_path, close_behavior):
    application = QApplication.instance() or QApplication([])
    settings = Settings(tmp_path / "settings.json"); settings.values["close_behavior"] = close_behavior; settings.save()
    view_model = SettingsViewModel(settings, tmp_path / "PourTask.exe")
    requested = []
    engine = QQmlApplicationEngine(); warnings = []
    engine.warnings.connect(lambda items: warnings.extend(item.toString() for item in items))
    engine._app_view_model = AppViewModel(repository); engine._settings_view_model = view_model
    view_model.exitRequested.connect(engine._app_view_model.requestExit)
    engine._app_view_model.exitApproved.connect(lambda: requested.append(True))
    engine.rootContext().setContextProperty("appViewModel", engine._app_view_model)
    engine.rootContext().setContextProperty("settingsViewModel", view_model)
    engine.rootContext().setContextProperty("strings", STRINGS)
    engine.rootContext().setContextProperty("appVersion", "test")
    engine.rootContext().setContextProperty("appIconUrl", "")
    engine.rootContext().setContextProperty("launchHidden", False)
    engine.rootContext().setContextProperty("trayAvailable", True)
    engine.load(QUrl.fromLocalFile(str(Path(__file__).parents[1] / "app" / "qml" / "Main.qml")))
    assert engine.rootObjects()
    window = engine.rootObjects()[0]; window.show(); application.processEvents(); QTest.qWait(50)
    return application, engine, window, requested, warnings


def test_close_to_tray_hides_window_without_requesting_exit(repository, tmp_path):
    application, engine, window, requested, _ = _qml_window(repository, tmp_path, "tray")
    engine._app_view_model.beginNewTask(); draft = engine._app_view_model.draft
    engine._app_view_model.updateDraft("Tray draft", "", draft["scheduledDate"], draft["dueDate"], draft["assignedMonth"], False)
    window.close(); application.processEvents()
    assert not window.isVisible() and requested == []
    assert engine._app_view_model.draft["title"] == "Tray draft"
    engine.deleteLater()


def test_close_behavior_exit_requests_graceful_termination(repository, tmp_path):
    application, engine, window, requested, warnings = _qml_window(repository, tmp_path, "exit")
    window.close(); application.processEvents()
    assert requested == [True], "\n".join(warnings)
    window.hide(); engine.deleteLater()


def test_close_behavior_exit_requires_resolution_for_dirty_draft(repository, tmp_path):
    application, engine, window, requested, _ = _qml_window(repository, tmp_path, "exit")
    engine._app_view_model.beginNewTask(); draft = engine._app_view_model.draft
    engine._app_view_model.updateDraft("Exit draft", "", draft["scheduledDate"], draft["dueDate"], draft["assignedMonth"], False)
    window.close(); application.processEvents()
    assert requested == [] and engine._app_view_model.unsavedPromptVisible
    engine._app_view_model.resolveUnsavedChanges("cancel")
    assert engine._app_view_model.draft["title"] == "Exit draft"
    window.hide(); engine.deleteLater()


def _environment(root: Path, pipe_name: str, instance_name: str) -> dict[str, str]:
    environment = os.environ.copy()
    environment.update({
        "POURTASK_PHASE4_TEST": "1",
        "POURTASK_PHASE4_DATA_ROOT": str(root),
        "POURUPGRADE_REGISTRATION_ROOT": str(root / "registrations"),
        "POURTASK_PHASE4_CONTROL_PIPE": pipe_name,
        "POURTASK_PHASE4_SINGLE_INSTANCE": instance_name,
        "QT_QUICK_BACKEND": "software", "QT_QPA_PLATFORM": "windows",
    })
    return environment


def _start_real_app(tmp_path: Path, close_behavior: str, *, hidden: bool = False):
    root = tmp_path / "fixture-data"; settings = Settings(root / "settings.json")
    settings.values["close_behavior"] = close_behavior; settings.values["widget_enabled"] = False; settings.save()
    pipe_name = f"pourtask-exit-{uuid4().hex}"
    instance_name = f"PourTask.Exit.{uuid4().hex}"
    arguments = [sys.executable, str(Path(__file__).parents[1] / "main.py"), "--pourupgrade-phase4-test"]
    if hidden: arguments.append("--pourupgrade-tray")
    process = subprocess.Popen(arguments, env=_environment(root, pipe_name, instance_name), cwd=Path(__file__).parents[1])
    return process, root, pipe_name, instance_name


def _request_update_shutdown(pipe_name: str, timeout: float = 8):
    path = rf"\\.\pipe\{pipe_name}"; deadline = time.monotonic() + timeout
    request = {
        "appId": "com.pour.pourtask.phase4", "requestId": uuid4().hex,
        "targetVersion": "1.2.1-beta.2", "requestedRestartMode": "none",
        "createdAt": datetime.now(timezone.utc).isoformat(),
        "expiresAt": (datetime.now(timezone.utc) + timedelta(seconds=30)).isoformat(),
        "nonce": base64.b64encode(os.urandom(16)).decode(),
        "protocolIdentity": "pourtask-phase4-v1",
    }
    payload = json.dumps(request, separators=(",", ":")).encode()
    while True:
        try:
            with open(path, "r+b", buffering=0) as pipe:
                pipe.write(struct.pack("<I", len(payload)) + payload)
                length = struct.unpack("<I", pipe.read(4))[0]
                return json.loads(pipe.read(length))
        except OSError:
            if time.monotonic() >= deadline: raise
            time.sleep(.05)


@pytest.mark.skipif(sys.platform != "win32", reason="Windows process behavior")
def test_foreground_update_shutdown_is_bounded_and_releases_database(tmp_path):
    process, root, pipe_name, _ = _start_real_app(tmp_path, "exit")
    try:
        assert _request_update_shutdown(pipe_name)["status"] == "ready"
        assert process.wait(timeout=5) == 0
        with sqlite3.connect(root / "data" / "pourtask.db", timeout=.2) as database:
            database.execute("BEGIN EXCLUSIVE"); database.rollback()
    finally:
        if process.poll() is None: process.terminate(); process.wait(5)


@pytest.mark.skipif(sys.platform != "win32", reason="Windows process behavior")
def test_hidden_window_update_exit_is_bounded_and_leaves_no_instance_lock(tmp_path):
    process, _, pipe_name, instance_name = _start_real_app(tmp_path, "tray", hidden=True)
    try:
        response = _request_update_shutdown(pipe_name)
        assert response["status"] == "ready"
        assert process.wait(timeout=5) == 0
        replacement = SingleInstanceGuard(instance_name)
        try: assert replacement.acquire()
        finally: replacement.close()
        with pytest.raises(OSError):
            open(rf"\\.\pipe\{pipe_name}", "rb")
    finally:
        if process.poll() is None: process.terminate(); process.wait(5)
