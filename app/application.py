from __future__ import annotations

import logging
import sys
from pathlib import Path

from PySide6.QtCore import QTimer, QUrl
from PySide6.QtGui import QColor, QGuiApplication, QIcon, QPainter, QPixmap
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication, QSystemTrayIcon

from app import __version__
from app.database import Database, TaskRepository
from app.logging_config import configure_logging
from app.paths import AppPaths
from app.settings import Settings
from app.strings import STRINGS
from app.viewmodels import AppViewModel
from app.viewmodels.settings_viewmodel import SettingsViewModel
from app.platform.desktop_widget import DesktopWidgetController
from app.platform.tray import create_tray


def run() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("PourTask"); app.setApplicationVersion(__version__); app.setOrganizationName("Pour")
    paths = AppPaths.default(); paths.ensure(); configure_logging(paths.logs)
    settings = Settings(paths.settings)
    try:
        repository = TaskRepository(Database(paths.database))
        view_model = AppViewModel(repository)
    except Exception:
        logging.exception("Database initialization failed")
        return 2
    engine = QQmlApplicationEngine()
    startup_launch = "--startup" in sys.argv
    tray_available = QSystemTrayIcon.isSystemTrayAvailable()
    settings_view_model = SettingsViewModel(settings, Path(sys.executable))
    engine.rootContext().setContextProperty("appViewModel", view_model)
    engine.rootContext().setContextProperty("settingsViewModel", settings_view_model)
    engine.rootContext().setContextProperty("strings", STRINGS)
    engine.rootContext().setContextProperty("appVersion", __version__)
    engine.rootContext().setContextProperty("launchHidden", startup_launch and tray_available)
    engine.rootContext().setContextProperty("trayAvailable", tray_available)
    qml = Path(__file__).parent / "qml" / "Main.qml"
    engine.load(QUrl.fromLocalFile(str(qml)))
    if not engine.rootObjects():
        logging.error("QML failed to load")
        return 3
    window = engine.rootObjects()[0]
    geometry = settings.values.get("window_geometry")
    if geometry:
        window.setX(geometry.get("x", window.x())); window.setY(geometry.get("y", window.y()))
        window.setWidth(geometry.get("width", window.width())); window.setHeight(geometry.get("height", window.height()))
    timer = QTimer(app); timer.setInterval(60_000); timer.timeout.connect(view_model.refresh); timer.start()
    widget_controller = DesktopWidgetController()
    engine.load(QUrl.fromLocalFile(str(Path(__file__).parent / "qml" / "DesktopWidget.qml")))
    widget = engine.rootObjects()[1] if len(engine.rootObjects()) > 1 else None
    if widget and settings.values["widget_enabled"]:
        widget_controller.show(widget)

    pixmap = QPixmap(32, 32); pixmap.fill(QColor("transparent"))
    painter = QPainter(pixmap); painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor("#5d8ff3")); painter.setPen(QColor("#4779df")); painter.drawRoundedRect(3, 3, 26, 26, 8, 8); painter.end()
    icon = QIcon(pixmap); app.setWindowIcon(icon)
    tray = create_tray(app, icon, lambda: (window.show(), window.raise_(), window.requestActivate()),
                       lambda: (window.show(), window.setProperty("adding", True)), app.quit)
    if tray:
        app.setQuitOnLastWindowClosed(False); tray.show()

    def sync_widget():
        if not widget: return
        widget_controller.show(widget) if settings.values["widget_enabled"] else widget_controller.hide()
    settings_view_model.changed.connect(sync_widget)

    def persist_geometry():
        settings.values["window_geometry"] = {"x": window.x(), "y": window.y(), "width": window.width(), "height": window.height()}
        settings.save()
    app.aboutToQuit.connect(persist_geometry)
    return app.exec()
