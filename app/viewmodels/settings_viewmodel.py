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
    @Property(float, notify=changed)
    def mainSidebarWidth(self):
        splitters = self.settings.values.get("main_splitters") or {}
        return float(splitters.get("sidebar", 0))
    @Property(float, notify=changed)
    def mainEditorWidth(self):
        splitters = self.settings.values.get("main_splitters") or {}
        return float(splitters.get("editor", 0))
    @Property(bool, notify=changed)
    def editorCollapsed(self): return bool(self.settings.values["editor_collapsed"])
    @Property(bool, notify=changed)
    def widgetCompact(self): return bool(self.settings.values["widget_compact"])
    @Property(int, notify=changed)
    def widgetExpandedWidth(self):
        return int((self.settings.values.get("widget_expanded_size") or {}).get("width", 260))
    @Property(int, notify=changed)
    def widgetExpandedHeight(self):
        return int((self.settings.values.get("widget_expanded_size") or {}).get("height", 180))
    @Property(bool, notify=changed)
    def widgetAlwaysOnTop(self): return bool(self.settings.values["widget_always_on_top"])
    @Property(bool, notify=changed)
    def widgetLockPosition(self): return bool(self.settings.values["widget_lock_position"])

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

    @Slot(float, float)
    def setMainSplitters(self, sidebar, editor):
        self.settings.values["main_splitters"] = {
            "sidebar": max(150, round(sidebar)),
            "editor": max(300, round(editor)),
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
            "width": max(220, width), "height": max(130, height),
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
