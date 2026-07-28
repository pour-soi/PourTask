from PySide6.QtCore import QObject, Signal


class DesktopWidgetController(QObject):
    """Owns the optional widget window and exposes its actual visibility."""

    visibleChanged = Signal()

    def __init__(self):
        super().__init__()
        self.window = None

    @property
    def visible(self):
        return bool(self.window and self.window.isVisible())

    def set_window(self, window):
        if self.window is window:
            return
        self.window = window
        self.window.visibleChanged.connect(self.visibleChanged)

    def show(self, window):
        self.set_window(window)
        self.window.show()
        self.window.raise_()

    def hide(self):
        if self.window is not None:
            self.window.hide()

    def toggle(self):
        self.hide() if self.visible else self.show(self.window)
