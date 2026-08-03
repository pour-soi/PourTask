import base64
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.paths import AppPaths
from app.update_integration import (
    MAX_MESSAGE_BYTES, PHASE4_APP_ID, PHASE4_PROTOCOL_ID, RegistrationStore,
    ShutdownRequestValidator, UpdaterLauncher, health_report, phase4_registration,
    prepare_shutdown, register_test_installation,
)


def request(**changes):
    now = datetime.now(timezone.utc)
    value = {"appId": PHASE4_APP_ID, "requestId": "request-1", "targetVersion": "1.2.1-beta.1",
             "requestedRestartMode": "foreground", "createdAt": (now - timedelta(seconds=1)).isoformat(),
             "expiresAt": (now + timedelta(minutes=1)).isoformat(),
             "nonce": base64.b64encode(b"x" * 32).decode(), "protocolIdentity": PHASE4_PROTOCOL_ID}
    value.update(changes)
    return json.dumps(value).encode()


def test_registration_creation_update_repair_and_cleanup(tmp_path):
    executable = tmp_path / "install" / "PourTask.exe"; executable.parent.mkdir(); executable.touch()
    data = tmp_path / "data-root"; (data / "data").mkdir(parents=True)
    store = RegistrationStore(tmp_path / "registrations" / "pourtask.json")
    store.write(phase4_registration(executable, data, "1.2.0")); assert store.read().appId == PHASE4_APP_ID
    store.write(phase4_registration(executable, data, "1.2.1-beta.1")); assert store.read().currentVersion == "1.2.1-beta.1"
    store.path.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError): store.read()
    store.write(phase4_registration(executable, data, "1.2.1-beta.1")); store.remove(); assert not store.path.exists()


def test_development_launch_does_not_register(monkeypatch, tmp_path):
    monkeypatch.setenv("POURTASK_PHASE4_TEST", "1"); monkeypatch.setenv("POURUPGRADE_REGISTRATION_ROOT", str(tmp_path / "registrations"))
    executable = tmp_path / "dev" / "PourTask.exe"; executable.parent.mkdir(); executable.touch()
    assert register_test_installation(executable, tmp_path / "data", "1.2.0") is None


def test_installed_test_registration_is_isolated(monkeypatch, tmp_path):
    monkeypatch.setenv("POURTASK_PHASE4_TEST", "1"); monkeypatch.setenv("POURUPGRADE_REGISTRATION_ROOT", str(tmp_path / "registrations"))
    executable = tmp_path / "phase4" / "PourTask.exe"; executable.parent.mkdir(); executable.touch(); (executable.parent / ".pourtask-phase4-installed").touch()
    path = register_test_installation(executable, tmp_path / "test-data", "1.2.0")
    assert path and PHASE4_APP_ID in path.name


def test_installed_marker_enables_test_mode_without_command_line(monkeypatch, tmp_path):
    executable = tmp_path / "phase4" / "PourTask.exe"; executable.parent.mkdir(); executable.touch()
    (executable.parent / ".pourtask-phase4-installed").touch(); monkeypatch.setattr("sys.executable", str(executable))
    from app.update_integration import test_mode
    assert test_mode()
    assert AppPaths.default().root == (Path(os.environ["USERPROFILE"]) / "AppData" / "Local" / "PourTask-Phase4").resolve()


def test_marker_absent_uses_only_stable_root(monkeypatch, tmp_path):
    executable = tmp_path / "stable" / "PourTask.exe"; executable.parent.mkdir(); executable.touch()
    stable_base = tmp_path / "local"; monkeypatch.setenv("LOCALAPPDATA", str(stable_base))
    monkeypatch.delenv("POURTASK_PHASE4_TEST", raising=False); monkeypatch.delenv("POURTASK_PHASE4_DATA_ROOT", raising=False)
    monkeypatch.setattr(sys, "executable", str(executable)); monkeypatch.setattr(sys, "argv", [str(executable)])
    from app.update_integration import test_mode
    assert not test_mode()
    assert AppPaths.default().root == stable_base / "PourTask"


def test_phase4_command_line_centralizes_all_storage_paths(monkeypatch, tmp_path):
    root = tmp_path / "isolated"; monkeypatch.setenv("POURTASK_PHASE4_DATA_ROOT", str(root))
    monkeypatch.setattr(sys, "argv", ["PourTask.exe", "--pourupgrade-phase4-test", "--startup"])
    from app.update_integration import test_mode
    paths = AppPaths.default()
    assert test_mode() and paths.root == root.resolve()
    assert {paths.data, paths.database, paths.backups, paths.logs, paths.settings} == {
        paths.root / "data", paths.root / "data" / "pourtask.db", paths.root / "backups",
        paths.root / "logs", paths.root / "settings.json",
    }


@pytest.mark.parametrize("argument", ["--startup", "--pourupgrade-tray"])
def test_stable_restart_arguments_do_not_enable_phase4(monkeypatch, tmp_path, argument):
    executable = tmp_path / "stable" / "PourTask.exe"; executable.parent.mkdir(); executable.touch()
    stable_base = tmp_path / "local"; monkeypatch.setenv("LOCALAPPDATA", str(stable_base))
    monkeypatch.delenv("POURTASK_PHASE4_TEST", raising=False); monkeypatch.setattr(sys, "executable", str(executable))
    monkeypatch.setattr(sys, "argv", [str(executable), argument])
    from app.update_integration import test_mode
    assert not test_mode()
    assert AppPaths.default().root == stable_base / "PourTask"


def test_test_paths_use_explicit_isolated_root(monkeypatch, tmp_path):
    monkeypatch.setenv("POURTASK_PHASE4_TEST", "1")
    monkeypatch.setenv("POURTASK_PHASE4_DATA_ROOT", str(tmp_path)); assert AppPaths.default().root == tmp_path.resolve()


def test_updater_missing_is_safe(tmp_path):
    assert UpdaterLauncher(tmp_path / "missing.exe").launch_for_pourtask()[0] is False


def test_phase4_launcher_uses_only_isolated_coordinator_package(monkeypatch):
    monkeypatch.setenv("POURTASK_PHASE4_TEST", "1")
    assert "PourUpgrade-Phase4" in str(UpdaterLauncher().executable)


def test_update_entry_uses_only_fixed_app_identity(tmp_path):
    executable = tmp_path / "PourUpgrade.exe"; executable.touch(); calls = []
    assert UpdaterLauncher(executable, lambda *a, **k: calls.append((a, k))).launch_for_pourtask()[0]
    assert calls[0][0][0] == [str(executable), "--focus-app", PHASE4_APP_ID]


@pytest.mark.parametrize("mode", ["foreground", "tray", "none"])
def test_valid_shutdown_request_modes(mode):
    assert ShutdownRequestValidator().validate(request(requestedRestartMode=mode))["requestedRestartMode"] == mode


@pytest.mark.parametrize("change,error", [({"appId": "stable"}, "wrong-app-id"), ({"protocolIdentity": "wrong"}, "wrong-protocol-identity"), ({"nonce": "bad"}, "malformed-message")])
def test_shutdown_request_rejections(change, error):
    with pytest.raises(ValueError, match=error): ShutdownRequestValidator().validate(request(**change))


def test_expired_and_replayed_requests_are_rejected():
    now = datetime.now(timezone.utc); validator = ShutdownRequestValidator()
    with pytest.raises(ValueError, match="expired-request"): validator.validate(request(expiresAt=(now - timedelta(seconds=1)).isoformat()), now=now)
    validator.validate(request(), now=now)
    with pytest.raises(ValueError, match="replayed-request"): validator.validate(request(), now=now)


def test_malformed_and_oversized_messages_are_rejected():
    validator = ShutdownRequestValidator()
    with pytest.raises(ValueError, match="malformed-message"): validator.validate(b"{")
    with pytest.raises(ValueError, match="message-too-large"): validator.validate(b"x" * (MAX_MESSAGE_BYTES + 1))


def test_shutdown_saves_before_ready_and_fails_safely():
    calls = []; assert prepare_shutdown({}, pending_edits=False, save_state=lambda: calls.append("saved") or True)["status"] == "ready"; assert calls == ["saved"]
    assert prepare_shutdown({}, pending_edits=False, save_state=lambda: False)["status"] == "failed"
    assert prepare_shutdown({}, pending_edits=True, save_state=lambda: True)["status"] == "requires-user-action"


def test_health_report_contains_only_structural_data():
    report = health_report("1.2.1-beta.1", "tray", True, "attempt", "request")
    assert report["stateRestored"] and report["launchMode"] == "tray"
    assert not any(key in report for key in ("title", "notes", "path", "nonce"))
