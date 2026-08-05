from pathlib import Path

from PySide6.QtCore import QObject, Property, Signal, Slot

from app.platform.startup import StartupError, StartupService
from app.settings import Settings
from app.update_integration import UpdaterLauncher


class SettingsViewModel(QObject):
    changed = Signal()
    showWidgetRequested = Signal()
    resetWidgetRequested = Signal()
    updateStatusChanged = Signal()
    exitRequested = Signal()

    def __init__(self, settings: Settings, executable: Path, startup_service=None, updater_launcher=None):
        super().__init__()
        self.settings = settings
        self.executable = executable
        self.startup_service = startup_service or StartupService(executable)
        self._startup_error = ""
        self.updater_launcher = updater_launcher or UpdaterLauncher()
        self._update_status = ""

    @Property(str, notify=updateStatusChanged)
    def updateStatus(self): return self._update_status

    @Slot()
    def checkForUpdates(self):
        _, self._update_status = self.updater_launcher.launch_for_pourtask()
        self.updateStatusChanged.emit()

    @Property(bool, notify=changed)
    def launchAtStartup(self):
        try:
            return self.startup_service.is_enabled()
        except StartupError as exc:
            self._startup_error = str(exc)
            return False
    @Property(bool, notify=changed)
    def startupSupported(self): return self.startup_service.supported
    @Property(str, notify=changed)
    def startupUnavailableReason(self): return self.startup_service.unavailable_reason
    @Property(str, notify=changed)
    def startupError(self): return self._startup_error
    @Property(bool, notify=changed)
    def minimizeToTray(self): return self.settings.values["close_behavior"] == "tray"
    @Property(bool, notify=changed)
    def widgetEnabled(self): return bool(self.settings.values["widget_enabled"])
    @Property(float, notify=changed)
    def mainSidebarWidth(self):
        splitters = self.settings.values.get("main_splitters") or {}
        value = float(splitters.get("sidebar", 0))
        return value if 130 <= value <= 420 else 0
    @Property(float, notify=changed)
    def mainEditorWidth(self):
        splitters = self.settings.values.get("main_splitters") or {}
        value = float(splitters.get("editor", 0))
        return value if 260 <= value <= 2400 else 0
    @Property(float, notify=changed)
    def mainTaskWidth(self):
        splitters = self.settings.values.get("main_splitters") or {}
        value = float(splitters.get("task", 0))
        return value if 180 <= value <= 2400 else 0
    @Property(bool, notify=changed)
    def editorCollapsed(self): return bool(self.settings.values["editor_collapsed"])
    @Property(bool, notify=changed)
    def widgetCompact(self): return bool(self.settings.values["widget_compact"])
    @Property(int, notify=changed)
    def widgetExpandedWidth(self):
        return int((self.settings.values.get("widget_expanded_size") or {}).get("width", 260))
    @Property(int, notify=changed)
    def widgetExpandedHeight(self):
        return int((self.settings.values.get("widget_expanded_size") or {}).get("height", 160))
    @Property(bool, notify=changed)
    def widgetAlwaysOnTop(self): return bool(self.settings.values["widget_always_on_top"])
    @Property(bool, notify=changed)
    def widgetLockPosition(self): return bool(self.settings.values["widget_lock_position"])
    @Property(bool, notify=changed)
    def widgetExpandOnHover(self): return bool(self.settings.values["widget_expand_on_hover"])

    @Slot(bool)
    def setLaunchAtStartup(self, enabled):
        try:
            self.startup_service.set_enabled(enabled)
            actual = self.startup_service.is_enabled()
            if actual != enabled:
                raise StartupError("Windows startup state did not change.")
            self._startup_error = ""
            self.settings.values["launch_at_startup"] = actual
            self.settings.save()
        except StartupError as exc:
            self._startup_error = str(exc)
        self.changed.emit()

    @Slot(bool)
    def setMinimizeToTray(self, enabled):
        self.settings.values["close_behavior"] = "tray" if enabled else "exit"; self.settings.save(); self.changed.emit()

    @Slot()
    def requestExit(self):
        self.exitRequested.emit()

    @Slot(bool)
    def setWidgetEnabled(self, enabled):
        self.settings.values["widget_enabled"] = enabled
        self.settings.values["widget_visible"] = enabled
        self.settings.save(); self.changed.emit()

    @Slot(float, float, float)
    def setMainSplitters(self, sidebar, task, editor):
        self.settings.values["main_splitters"] = {
            "sidebar": max(130, round(sidebar)),
            "task": max(180, round(task)),
            "editor": max(260, round(editor)),
        }
        self.settings.save()

    @Slot(bool)
    def setEditorCollapsed(self, collapsed):
        self.settings.values["editor_collapsed"] = collapsed
        self.settings.save(); self.changed.emit()

    @Slot(bool)
    def setWidgetCompact(self, compact):
        self.settings.values["widget_compact"] = compact
        self.settings.save(); self.changed.emit()

    @Slot(int, int)
    def setWidgetExpandedSize(self, width, height):
        self.settings.values["widget_expanded_size"] = {
            "width": max(220, width), "height": max(115, height),
        }
        self.settings.save(); self.changed.emit()

    @Slot(int, int, int, int)
    def setWidgetGeometry(self, x, y, width, height):
        self.settings.values["widget_geometry"] = {
            "x": x, "y": y, "width": width, "height": height,
        }
        self.settings.save()

    @Slot(bool)
    def setWidgetAlwaysOnTop(self, enabled):
        self.settings.values["widget_always_on_top"] = enabled
        self.settings.save(); self.changed.emit()

    @Slot(bool)
    def setWidgetLockPosition(self, locked):
        self.settings.values["widget_lock_position"] = locked
        self.settings.save(); self.changed.emit()

    @Slot(bool)
    def setWidgetExpandOnHover(self, enabled):
        self.settings.values["widget_expand_on_hover"] = enabled
        self.settings.save(); self.changed.emit()

    @Slot()
    def showWidget(self):
        self.settings.values["widget_enabled"] = True
        self.settings.values["widget_visible"] = True
        self.settings.save()
        self.changed.emit()
        self.showWidgetRequested.emit()

    @Slot()
    def resetWidgetPosition(self):
        self.resetWidgetRequested.emit()
