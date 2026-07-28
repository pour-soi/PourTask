from __future__ import annotations

import struct
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from app.application import _resource_path, _set_windows_app_id


ROOT = Path(__file__).parents[1]
ICON_DIR = ROOT / "assets" / "icons"
QT_APP = QApplication.instance() or QApplication([])


def _ico_sizes(path: Path) -> set[int]:
    data = path.read_bytes()
    reserved, icon_type, count = struct.unpack_from("<HHH", data)
    assert reserved == 0 and icon_type == 1
    sizes = set()
    for index in range(count):
        width, height = struct.unpack_from("<BB", data, 6 + index * 16)
        resolved_width = 256 if width == 0 else width
        resolved_height = 256 if height == 0 else height
        assert resolved_width == resolved_height
        sizes.add(resolved_width)
    return sizes


def test_authoritative_icon_source_and_required_windows_sizes_exist():
    source = ICON_DIR / "PourTask.svg"
    icon = ICON_DIR / "PourTask.ico"
    preview = ICON_DIR / "PourTask-256.png"
    assert source.is_file()
    assert "<svg" in source.read_text(encoding="utf-8")
    assert icon.is_file() and icon.stat().st_size > 0
    assert preview.is_file() and preview.stat().st_size > 0
    assert _ico_sizes(icon) == {16, 20, 24, 32, 40, 48, 64, 128, 256}
    assert not QIcon(str(icon)).isNull()
    assert _resource_path("assets/icons/PourTask.ico").resolve() == icon.resolve()
    _set_windows_app_id()


def test_runtime_and_packaging_share_the_branded_icon():
    application = (ROOT / "app" / "application.py").read_text(encoding="utf-8")
    spec = (ROOT / "packaging" / "PourTask.spec").read_text(encoding="utf-8")
    installer = (ROOT / "packaging" / "PourTask.iss").read_text(encoding="utf-8")

    assert 'assets/icons/PourTask.ico' in application
    assert 'icon=str(project / "assets" / "icons" / "PourTask.ico")' in spec
    assert '(str(project / "assets" / "icons"), "assets/icons")' in spec
    assert "SetupIconFile=..\\assets\\icons\\PourTask.ico" in installer
    assert "UninstallDisplayIcon={app}\\PourTask.exe" in installer
    assert installer.count('IconFilename: "{app}\\PourTask.exe"') == 2
    assert "QPixmap(32, 32)" not in application
