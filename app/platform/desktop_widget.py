class DesktopWidgetController:
    """Owns one optional widget window; shell attachment is deliberately deferred."""

    def __init__(self):
        self.window = None

    def show(self, window):
        if self.window is None:
            self.window = window
        self.window.show()

    def hide(self):
        if self.window is not None:
            self.window.hide()
