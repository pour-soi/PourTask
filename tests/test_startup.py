from pathlib import Path
import sys
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


@pytest.mark.parametrize(
    "argument,marker,value_name",
    [
        ("--stage43-stable-fixture", ".pourtask-stage43-stable-fixture", "PourTask Stage43 Stable Fixture"),
        ("--pourupgrade-phase4-test", ".pourtask-phase4-installed", "PourTask Phase4 Beta Fixture"),
    ],
)
def test_fixture_startup_identity_is_separate(monkeypatch, tmp_path, argument, marker, value_name):
    executable = tmp_path / value_name / "PourTask.exe"; executable.parent.mkdir(); executable.touch()
    (executable.parent / marker).touch(); monkeypatch.setattr(sys, "executable", str(executable))
    monkeypatch.setattr(sys, "argv", [str(executable), argument])
    startup = StartupService(executable, provider=FakeRunProvider(), platform_name="win32")
    assert startup.supported and startup.value_name == value_name
    assert startup.command == f'"{executable.resolve()}" {argument} --startup'


def test_stage43_fixture_installers_are_per_user_and_remove_only_fixture_startup_values():
    root = Path(__file__).parents[1] / "packaging"
    stable_fixture = (root / "PourTask.Stage43StableFixture.iss").read_text(encoding="utf-8")
    beta_fixture = (root / "PourTask.Phase4.iss").read_text(encoding="utf-8")
    assert "PrivilegesRequired=lowest" in stable_fixture and "PrivilegesRequired=lowest" in beta_fixture
    assert "CE634188-5D2E-4DC9-85EB-851060BB6092" in stable_fixture
    assert "F927AD06-CC4D-4B73-91D4-74259DC59EF4" in beta_fixture
    assert 'ValueName: "PourTask Stage43 Stable Fixture"' in stable_fixture
    assert 'ValueName: "PourTask Phase4 Beta Fixture"' in beta_fixture
    assert "Root: HKLM" not in stable_fixture and "Root: HKLM" not in beta_fixture
