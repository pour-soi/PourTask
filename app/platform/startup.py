from __future__ import annotations

import sys
from pathlib import Path


def set_launch_at_startup(enabled: bool, executable: Path) -> None:
    if sys.platform != "win32":
        return
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE) as key:
        if enabled:
            winreg.SetValueEx(key, "PourTask", 0, winreg.REG_SZ, f'"{executable}" --startup')
        else:
            try:
                winreg.DeleteValue(key, "PourTask")
            except FileNotFoundError:
                pass
