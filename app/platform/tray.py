from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu, QSystemTrayIcon


def create_tray(app, icon, open_window, quick_add, exit_app, widget_controller=None):
    if not QSystemTrayIcon.isSystemTrayAvailable():
        return None
    tray = QSystemTrayIcon(icon, app)
    menu = QMenu()
    for label, callback in (("Open PourTask", open_window), ("Quick Add", quick_add), ("Exit", exit_app)):
        action = QAction(label, menu)
        action.triggered.connect(callback)
        menu.addAction(action)
        if label == "Quick Add" and widget_controller is not None:
            widget_action = QAction("Show Widget", menu)
            widget_action.triggered.connect(widget_controller.toggle)
            menu.addAction(widget_action)

            def update_widget_action():
                widget_action.setText("Hide Widget" if widget_controller.visible else "Show Widget")

            menu.aboutToShow.connect(update_widget_action)
    tray.setContextMenu(menu)
    tray.activated.connect(lambda reason: open_window() if reason == QSystemTrayIcon.ActivationReason.Trigger else None)
    return tray
