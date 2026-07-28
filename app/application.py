from __future__ import annotations

import logging
import sys
from pathlib import Path

from PySide6.QtCore import QTimer, QUrl
from PySide6.QtGui import QColor, QGuiApplication, QIcon, QPainter, QPixmap, QWindow
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
from app.platform.window_geometry import visible_geometry


def _screen_work_areas():
    return [
        {
            "x": screen.availableGeometry().x(),
            "y": screen.availableGeometry().y(),
            "width": screen.availableGeometry().width(),
            "height": screen.availableGeometry().height(),
        }
        for screen in QGuiApplication.screens()
    ]


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
    screens = _screen_work_areas()
    geometry = visible_geometry(
        settings.values.get("window_geometry"),
        screens,
        {"x": window.x(), "y": window.y(), "width": 1300, "height": 780},
        minimum=(900, 620),
    )
    window.setX(geometry["x"]); window.setY(geometry["y"])
    window.setWidth(geometry["width"]); window.setHeight(geometry["height"])
    normal_geometry = dict(geometry)

    def remember_normal_geometry():
        if window.visibility() == QWindow.Visibility.Windowed:
            normal_geometry.update({
                "x": window.x(), "y": window.y(),
                "width": window.width(), "height": window.height(),
            })

    window.xChanged.connect(remember_normal_geometry)
    window.yChanged.connect(remember_normal_geometry)
    window.widthChanged.connect(remember_normal_geometry)
    window.heightChanged.connect(remember_normal_geometry)

    saved_maximized = bool(settings.values.get("window_maximized"))
    window_state = {"maximized": saved_maximized}

    def remember_window_state(visibility):
        if visibility == QWindow.Visibility.Maximized:
            window_state["maximized"] = True
        elif visibility == QWindow.Visibility.Windowed:
            window_state["maximized"] = False

    window.visibilityChanged.connect(remember_window_state)
    if saved_maximized and not launchHidden:
        QTimer.singleShot(0, window.showMaximized)
    timer = QTimer(app); timer.setInterval(60_000); timer.timeout.connect(view_model.refresh); timer.start()
    widget_controller = DesktopWidgetController()
    engine.rootContext().setContextProperty("mainWindow", window)
    engine.load(QUrl.fromLocalFile(str(Path(__file__).parent / "qml" / "DesktopWidget.qml")))
    widget = engine.rootObjects()[1] if len(engine.rootObjects()) > 1 else None
    if widget:
        widget_controller.set_window(widget)
        compact = bool(settings.values.get("widget_compact"))
        widget_default = {
            "x": widget.x(), "y": widget.y(),
            "width": widget.width(), "height": widget.height(),
        }
        widget_geometry = visible_geometry(
            settings.values.get("widget_geometry"),
            screens,
            widget_default,
            minimum=(220, 70 if compact else 130),
            title_height=48,
            keep_entire_window=False,
        )
        widget.setX(widget_geometry["x"]); widget.setY(widget_geometry["y"])
        widget.setWidth(widget_geometry["width"])
        widget.setHeight(80 if compact else widget_geometry["height"])
    if widget and settings.values["widget_enabled"]:
        widget_controller.show(widget)

    def recover_visible_windows():
        current_screens = _screen_work_areas()
        if not current_screens:
            return
        primary = current_screens[0]
        if window.visibility() == QWindow.Visibility.Windowed:
            current = {
                "x": window.x(), "y": window.y(),
                "width": window.width(), "height": window.height(),
            }
            safe_default = {
                "x": primary["x"] + 40, "y": primary["y"] + 40,
                "width": current["width"], "height": current["height"],
            }
            recovered = visible_geometry(
                current, current_screens, safe_default, minimum=(900, 620),
            )
            window.setX(recovered["x"]); window.setY(recovered["y"])
            window.setWidth(recovered["width"]); window.setHeight(recovered["height"])
        if widget:
            current = {
                "x": widget.x(), "y": widget.y(),
                "width": widget.width(), "height": widget.height(),
            }
            safe_default = {
                "x": primary["x"] + 40, "y": primary["y"] + 40,
                "width": current["width"], "height": current["height"],
            }
            recovered = visible_geometry(
                current, current_screens, safe_default,
                minimum=(220, 70 if bool(settings.values.get("widget_compact")) else 130),
                title_height=48,
                keep_entire_window=False,
            )
            widget.setX(recovered["x"]); widget.setY(recovered["y"])
            widget.setWidth(recovered["width"]); widget.setHeight(recovered["height"])

    def watch_screen(screen):
        screen.availableGeometryChanged.connect(
            lambda _geometry: QTimer.singleShot(0, recover_visible_windows)
        )

    for screen in QGuiApplication.screens():
        watch_screen(screen)
    app.screenAdded.connect(lambda screen: (watch_screen(screen), QTimer.singleShot(0, recover_visible_windows)))
    app.screenRemoved.connect(lambda _screen: QTimer.singleShot(0, recover_visible_windows))

    pixmap = QPixmap(32, 32); pixmap.fill(QColor("transparent"))
    painter = QPainter(pixmap); painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor("#5d8ff3")); painter.setPen(QColor("#4779df")); painter.drawRoundedRect(3, 3, 26, 26, 8, 8); painter.end()
    icon = QIcon(pixmap); app.setWindowIcon(icon)
    def open_window():
        if window_state["maximized"]:
            window.showMaximized()
        else:
            window.showNormal()
        window.raise_(); window.requestActivate()

    def quick_add():
        open_window()
        view_model.beginNewTask()

    tray = create_tray(
        app, icon, open_window, quick_add, app.quit,
        widget_controller=widget_controller if widget else None,
    )
    if tray:
        app.setQuitOnLastWindowClosed(False); tray.show()

    def sync_widget():
        if not widget: return
        widget_controller.show(widget) if settings.values["widget_enabled"] else widget_controller.hide()
    settings_view_model.changed.connect(sync_widget)

    def persist_geometry():
        remember_normal_geometry()
        settings.values["window_geometry"] = dict(normal_geometry)
        settings.values["window_maximized"] = window_state["maximized"]
        if widget:
            settings.values["widget_geometry"] = {
                "x": widget.x(), "y": widget.y(),
                "width": widget.width(), "height": widget.height(),
            }
        settings.save()
    app.aboutToQuit.connect(persist_geometry)
    return app.exec()
