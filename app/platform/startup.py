from __future__ import annotations

import sys
from pathlib import Path

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE_NAME = "PourTask"
INSTALLED_MARKER = ".pourtask-installed"


class StartupError(RuntimeError):
    pass


class WindowsRunProvider:
    def read(self) -> str | None:
        import winreg

        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
                return str(winreg.QueryValueEx(key, VALUE_NAME)[0])
        except FileNotFoundError:
            return None

    def write(self, command: str) -> None:
        import winreg

        with winreg.CreateKeyEx(
            winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE
        ) as key:
            winreg.SetValueEx(key, VALUE_NAME, 0, winreg.REG_SZ, command)

    def remove(self) -> None:
        import winreg

        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE
            ) as key:
                winreg.DeleteValue(key, VALUE_NAME)
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
        self.installed = (
            (self.executable.parent / INSTALLED_MARKER).is_file()
            if installed is None
            else installed
        )
        self.provider = provider or (
            WindowsRunProvider() if self.platform_name == "win32" else None
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
        return f'"{self.executable}" --startup'

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
