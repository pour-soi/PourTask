from pathlib import Path

from PySide6.QtCore import QObject, Property, Signal, Slot

from app.platform.startup import set_launch_at_startup
from app.settings import Settings


class SettingsViewModel(QObject):
    changed = Signal()

    def __init__(self, settings: Settings, executable: Path):
        super().__init__(); self.settings = settings; self.executable = executable

    @Property(bool, notify=changed)
    def launchAtStartup(self): return bool(self.settings.values["launch_at_startup"])
    @Property(bool, notify=changed)
    def minimizeToTray(self): return self.settings.values["close_behavior"] == "tray"
    @Property(bool, notify=changed)
    def widgetEnabled(self): return bool(self.settings.values["widget_enabled"])

    @Slot(bool)
    def setLaunchAtStartup(self, enabled):
        try: set_launch_at_startup(enabled, self.executable)
        except OSError: return
        self.settings.values["launch_at_startup"] = enabled; self.settings.save(); self.changed.emit()

    @Slot(bool)
    def setMinimizeToTray(self, enabled):
        self.settings.values["close_behavior"] = "tray" if enabled else "exit"; self.settings.save(); self.changed.emit()

    @Slot(bool)
    def setWidgetEnabled(self, enabled):
        self.settings.values["widget_enabled"] = enabled; self.settings.save(); self.changed.emit()
