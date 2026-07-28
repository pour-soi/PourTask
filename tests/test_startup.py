from pathlib import Path
from uuid import uuid4

import pytest
from PySide6.QtCore import QCoreApplication
from PySide6.QtTest import QTest

from app.platform.single_instance import SingleInstanceGuard
from app.platform.startup import StartupError, StartupService
from app.settings import Settings
from app.viewmodels.settings_viewmodel import SettingsViewModel


class FakeRunProvider:
    def __init__(self, value=None, fail_write=False):
        self.value = value
        self.fail_write = fail_write
        self.unrelated = {"AnotherApp": "another.exe"}

    def read(self):
        return self.value

    def write(self, command):
        if self.fail_write:
            raise OSError("denied")
        self.value = command

    def remove(self):
        self.value = None


def service(executable: Path, provider: FakeRunProvider, installed=True):
    return StartupService(
        executable,
        provider=provider,
        platform_name="win32",
        installed=installed,
    )


def test_startup_reads_provider_and_enable_is_idempotent(tmp_path):
    executable = tmp_path / "Pour Task" / "PourTask.exe"
    provider = FakeRunProvider()
    startup = service(executable, provider)
    assert not startup.is_enabled()

    startup.set_enabled(True)
    startup.set_enabled(True)
    assert provider.value == f'"{executable.resolve()}" --startup'
    assert startup.is_enabled()
    assert provider.unrelated == {"AnotherApp": "another.exe"}


def test_startup_disable_removes_only_pourtask(tmp_path):
    executable = tmp_path / "PourTask.exe"
    provider = FakeRunProvider(f'"{executable.resolve()}" --startup')
    startup = service(executable, provider)
    startup.set_enabled(False)
    assert provider.value is None
    assert provider.unrelated == {"AnotherApp": "another.exe"}


def test_startup_failure_keeps_view_model_consistent(tmp_path):
    provider = FakeRunProvider(fail_write=True)
    startup = service(tmp_path / "PourTask.exe", provider)
    settings = Settings(tmp_path / "settings.json")
    view_model = SettingsViewModel(settings, startup.executable, startup)
    view_model.setLaunchAtStartup(True)
    assert not view_model.launchAtStartup
    assert view_model.startupError
    assert settings.values["launch_at_startup"] is False


def test_portable_build_is_explicitly_unsupported(tmp_path):
    provider = FakeRunProvider()
    startup = service(tmp_path / "PourTask.exe", provider, installed=False)
    assert not startup.supported
    assert "installed Windows build" in startup.unavailable_reason
    with pytest.raises(StartupError):
        startup.set_enabled(True)
    assert provider.value is None


def test_startup_invocation_does_not_activate_duplicate_instance():
    application = QCoreApplication.instance() or QCoreApplication([])
    name = f"PourTask.Test.{uuid4()}"
    primary = SingleInstanceGuard(name)
    activated = []
    primary.activateRequested.connect(lambda: activated.append(True))
    assert primary.acquire()

    startup_duplicate = SingleInstanceGuard(name)
    assert not startup_duplicate.acquire(startup_launch=True)
    for _ in range(10):
        application.processEvents()
        QTest.qWait(5)
    assert activated == []

    normal_duplicate = SingleInstanceGuard(name)
    assert not normal_duplicate.acquire(startup_launch=False)
    for _ in range(10):
        application.processEvents()
        QTest.qWait(5)
    assert activated == [True]
    primary.server.close()


def test_installer_marks_installed_build_and_removes_startup_value():
    installer = (
        Path(__file__).parents[1] / "packaging" / "PourTask.iss"
    ).read_text(encoding="utf-8")
    assert 'DestName: ".pourtask-installed"' in installer
    assert 'ValueName: "PourTask"' in installer
    assert "uninsdeletevalue" in installer
    assert "Root: HKCU" in installer
    assert "Root: HKLM" not in installer
