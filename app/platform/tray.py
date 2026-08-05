from PySide6.QtCore import QThread
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QApplication, QMenu, QSystemTrayIcon


def create_tray(app, icon, open_window, quick_add, exit_app, widget_controller=None):
    if not isinstance(app, QApplication) or QApplication.instance() is not app:
        raise RuntimeError("Tray creation requires the active QApplication.")
    if QThread.currentThread() != app.thread():
        raise RuntimeError("Tray creation must run on the GUI thread.")
    if not QSystemTrayIcon.isSystemTrayAvailable():
        return None
    tray = QSystemTrayIcon(icon, app)
    menu = QMenu()
    actions = []
    for label, callback in (("Open PourTask", open_window), ("Quick Add", quick_add), ("Exit", exit_app)):
        action = QAction(label, menu)
        action.triggered.connect(callback)
        menu.addAction(action)
        actions.append(action)
        if label == "Quick Add" and widget_controller is not None:
            widget_action = QAction("Show Widget", menu)
            widget_action.triggered.connect(widget_controller.toggle)
            menu.addAction(widget_action)
            actions.append(widget_action)

            def update_widget_action():
                widget_action.setText("Hide Widget" if widget_controller.visible else "Show Widget")

            menu.aboutToShow.connect(update_widget_action)
    tray.setContextMenu(menu)
    tray.activated.connect(lambda reason: open_window() if reason == QSystemTrayIcon.ActivationReason.Trigger else None)
    tray._menu = menu
    tray._actions = actions
    return tray


def dispose_tray(tray):
    if tray is None:
        return
    if QThread.currentThread() != tray.thread():
        raise RuntimeError("Tray disposal must run on the GUI thread.")
    menu = tray.contextMenu()
    tray.hide()
    tray.setContextMenu(None)
    if menu is not None:
        menu.deleteLater()
    tray.deleteLater()
