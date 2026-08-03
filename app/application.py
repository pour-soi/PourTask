from __future__ import annotations

import ctypes
import logging
import os
import sys
from pathlib import Path

from PySide6.QtCore import QTimer, QUrl
from PySide6.QtGui import QGuiApplication, QIcon, QWindow
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
from app.platform.single_instance import SingleInstanceGuard
from app.platform.startup import StartupService
from app.platform.tray import create_tray
from app.platform.window_geometry import visible_geometry
from app.update_integration import UpdatePipeServer, health_report, register_test_installation, send_health, test_mode


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


def _resource_path(relative: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
    return base / relative


def _set_windows_app_id() -> None:
    if sys.platform == "win32":
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Pour.PourTask")


def run() -> int:
    _set_windows_app_id()
    app = QApplication(sys.argv)
    app.setApplicationName("PourTask"); app.setApplicationVersion(__version__); app.setOrganizationName("Pour")
    icon_path = _resource_path("assets/icons/PourTask.ico")
    icon = QIcon(str(icon_path))
    if icon.isNull():
        logging.error("Application icon could not be loaded from %s", icon_path)
    app.setWindowIcon(icon)
    startup_launch = "--startup" in sys.argv or "--pourupgrade-tray" in sys.argv
    instance_guard = SingleInstanceGuard()
    if not instance_guard.acquire(startup_launch):
        return 0
    paths = AppPaths.default(); paths.ensure(); configure_logging(paths.logs)
    register_test_installation(Path(sys.executable), paths.root, __version__)
    settings = Settings(paths.settings)
    try:
        repository = TaskRepository(Database(paths.database))
        view_model = AppViewModel(repository)
    except Exception:
        logging.exception("Database initialization failed")
        return 2
    engine = QQmlApplicationEngine()
    tray_available = QSystemTrayIcon.isSystemTrayAvailable()
    settings_view_model = SettingsViewModel(
        settings, Path(sys.executable), StartupService(Path(sys.executable))
    )
    engine.rootContext().setContextProperty("appViewModel", view_model)
    engine.rootContext().setContextProperty("settingsViewModel", settings_view_model)
    engine.rootContext().setContextProperty("strings", STRINGS)
    engine.rootContext().setContextProperty("appVersion", __version__)
    engine.rootContext().setContextProperty(
        "appIconUrl", QUrl.fromLocalFile(str(_resource_path("assets/icons/PourTask.svg")))
    )
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
        {"x": window.x(), "y": window.y(), "width": 960, "height": 700},
        minimum=(720, 520),
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
    if saved_maximized and not (startup_launch and tray_available):
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
            minimum=(220, 60 if compact else 115),
            title_height=48,
            keep_entire_window=False,
        )
        widget.setX(widget_geometry["x"]); widget.setY(widget_geometry["y"])
        widget.setWidth(widget_geometry["width"])
        widget.setHeight(70 if compact else widget_geometry["height"])
    saved_widget_visible = settings.values.get("widget_visible")
    if saved_widget_visible is None:
        saved_widget_visible = bool(settings.values["widget_enabled"])
    if widget and settings.values["widget_enabled"] and saved_widget_visible:
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
                current, current_screens, safe_default, minimum=(720, 520),
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
                minimum=(220, 60 if bool(settings.values.get("widget_compact")) else 115),
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

    def open_window():
        if window_state["maximized"]:
            window.showMaximized()
        else:
            window.showNormal()
        window.raise_(); window.requestActivate()

    def quick_add():
        open_window()
        view_model.beginNewTask()

    instance_guard.activateRequested.connect(open_window)

    tray = create_tray(
        app, icon, open_window, quick_add, app.quit,
        widget_controller=widget_controller if widget else None,
    )
    if tray:
        app.setQuitOnLastWindowClosed(False); tray.show()

    def sync_widget():
        if not widget: return
        desired = (
            settings.values["widget_enabled"]
            and settings.values.get("widget_visible") is not False
        )
        widget_controller.show(widget) if desired else widget_controller.hide()
    settings_view_model.changed.connect(sync_widget)
    settings_view_model.showWidgetRequested.connect(
        lambda: (recover_visible_windows(), widget_controller.show(widget)) if widget else None
    )

    def reset_widget_position():
        if not widget or not QGuiApplication.primaryScreen():
            return
        area = QGuiApplication.primaryScreen().availableGeometry()
        widget.setX(area.x() + max(12, area.width() - widget.width() - 24))
        widget.setY(area.y() + 24)
        widget_controller.show(widget)

    settings_view_model.resetWidgetRequested.connect(reset_widget_position)

    def remember_widget_visibility():
        if not widget:
            return
        settings.values["widget_visible"] = widget_controller.visible
        settings.save()

    widget_controller.visibleChanged.connect(remember_widget_visibility)

    def persist_geometry():
        remember_normal_geometry()
        settings.values["window_geometry"] = dict(normal_geometry)
        settings.values["window_maximized"] = window_state["maximized"]
        if widget:
            settings.values["widget_visible"] = widget_controller.visible
            settings.values["widget_geometry"] = {
                "x": widget.x(), "y": widget.y(),
                "width": widget.width(), "height": widget.height(),
            }
        settings.save()
    app.aboutToQuit.connect(persist_geometry)
    control_server = None
    if test_mode() and os.environ.get("POURTASK_PHASE4_CONTROL_PIPE"):
        control_server = UpdatePipeServer(
            os.environ["POURTASK_PHASE4_CONTROL_PIPE"], pending_edits=lambda: view_model.detailOpen,
            save_state=lambda: (persist_geometry() is None), quit_app=app.quit, parent=app,
        )
    health_pipe = os.environ.get("POURTASK_PHASE4_HEALTH_PIPE") if test_mode() else None
    if health_pipe:
        mode = "tray" if startup_launch else "foreground"
        report = health_report(__version__, mode, True, os.environ.get("POURTASK_PHASE4_ATTEMPT_ID", ""),
                               os.environ.get("POURTASK_PHASE4_REQUEST_ID", ""))
        QTimer.singleShot(0, lambda: send_health(health_pipe, report))
    return app.exec()
