from __future__ import annotations

import sys
from pathlib import Path

from app.paths import phase4_test_mode, stage43_stable_fixture_mode

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE_NAME = "PourTask"
INSTALLED_MARKER = ".pourtask-installed"


class StartupError(RuntimeError):
    pass


class WindowsRunProvider:
    def __init__(self, value_name: str = VALUE_NAME):
        self.value_name = value_name

    def read(self) -> str | None:
        import winreg

        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
                return str(winreg.QueryValueEx(key, self.value_name)[0])
        except FileNotFoundError:
            return None

    def write(self, command: str) -> None:
        import winreg

        with winreg.CreateKeyEx(
            winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE
        ) as key:
            winreg.SetValueEx(key, self.value_name, 0, winreg.REG_SZ, command)

    def remove(self) -> None:
        import winreg

        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE
            ) as key:
                winreg.DeleteValue(key, self.value_name)
        except FileNotFoundError:
            pass


class StartupService:
    def __init__(
        self,
        executable: Path,
        *,
        provider=None,
        platform_name: str | None = None,
        installed: bool | None = None,
    ):
        self.executable = Path(executable).resolve()
        self.platform_name = platform_name or sys.platform
        self.fixture_argument = (
            "--stage43-stable-fixture" if stage43_stable_fixture_mode()
            else "--pourupgrade-phase4-test" if phase4_test_mode()
            else ""
        )
        self.value_name = (
            "PourTask Stage43 Stable Fixture" if stage43_stable_fixture_mode()
            else "PourTask Phase4 Beta Fixture" if phase4_test_mode()
            else VALUE_NAME
        )
        installed_marker = (
            ".pourtask-stage43-stable-fixture" if stage43_stable_fixture_mode()
            else ".pourtask-phase4-installed" if phase4_test_mode()
            else INSTALLED_MARKER
        )
        self.installed = (
            (self.executable.parent / installed_marker).is_file()
            if installed is None
            else installed
        )
        self.provider = provider or (
            WindowsRunProvider(self.value_name) if self.platform_name == "win32" else None
        )

    @property
    def supported(self) -> bool:
        return self.platform_name == "win32" and self.installed

    @property
    def unavailable_reason(self) -> str:
        if self.platform_name != "win32":
            return "Windows startup is only available on Windows."
        if not self.installed:
            return "Available in the installed Windows build."
        return ""

    @property
    def command(self) -> str:
        argument = f" {self.fixture_argument}" if self.fixture_argument else ""
        return f'"{self.executable}"{argument} --startup'

    def is_enabled(self) -> bool:
        if not self.supported:
            return False
        try:
            return self.provider.read() == self.command
        except OSError as exc:
            raise StartupError("Windows startup state could not be read.") from exc

    def set_enabled(self, enabled: bool) -> None:
        if not self.supported:
            raise StartupError(self.unavailable_reason)
        try:
            if enabled:
                self.provider.write(self.command)
                if self.provider.read() != self.command:
                    raise StartupError("Windows did not confirm startup registration.")
            else:
                self.provider.remove()
                if self.provider.read() is not None:
                    raise StartupError("Windows did not confirm startup removal.")
        except OSError as exc:
            raise StartupError("Windows startup setting could not be changed.") from exc
