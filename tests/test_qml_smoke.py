from pathlib import Path

from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication

from app.strings import STRINGS
from app.viewmodels import AppViewModel
from app.viewmodels.settings_viewmodel import SettingsViewModel
from app.settings import Settings


def test_main_qml_loads(repository, tmp_path: Path):
    application = QApplication.instance() or QApplication([])
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(lambda items: warnings.extend(item.toString() for item in items))
    engine.rootContext().setContextProperty("appViewModel", AppViewModel(repository))
    engine.rootContext().setContextProperty("settingsViewModel", SettingsViewModel(Settings(tmp_path / "settings.json"), tmp_path / "PourTask.exe"))
    engine.rootContext().setContextProperty("strings", STRINGS)
    engine.rootContext().setContextProperty("launchHidden", False)
    engine.rootContext().setContextProperty("trayAvailable", False)
    qml = Path(__file__).parents[1] / "app" / "qml" / "Main.qml"
    engine.load(QUrl.fromLocalFile(str(qml)))
    assert engine.rootObjects(), "\n".join(warnings)
    engine.rootObjects()[0].close()
    application.processEvents()
