from datetime import date
from pathlib import Path

from PySide6.QtCore import QObject, QUrl
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication

from app import __version__
from app.settings import Settings
from app.strings import STRINGS
from app.viewmodels import AppViewModel
from app.viewmodels.settings_viewmodel import SettingsViewModel


def _load_main_and_widget(repository, tmp_path: Path):
    application = QApplication.instance() or QApplication([])
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(lambda items: warnings.extend(item.toString() for item in items))
    view_model = AppViewModel(repository)
    settings = Settings(tmp_path / "settings.json")
    settings_view_model = SettingsViewModel(settings, tmp_path / "PourTask.exe")
    context = engine.rootContext()
    context.setContextProperty("appViewModel", view_model)
    context.setContextProperty("settingsViewModel", settings_view_model)
    context.setContextProperty("strings", STRINGS)
    context.setContextProperty("appVersion", __version__)
    context.setContextProperty("launchHidden", False)
    context.setContextProperty("trayAvailable", False)

    qml_root = Path(__file__).parents[1] / "app" / "qml"
    engine.load(QUrl.fromLocalFile(str(qml_root / "Main.qml")))
    assert engine.rootObjects(), "\n".join(warnings)
    main = engine.rootObjects()[0]
    context.setContextProperty("mainWindow", main)
    engine.load(QUrl.fromLocalFile(str(qml_root / "DesktopWidget.qml")))
    assert len(engine.rootObjects()) == 2, "\n".join(warnings)
    return application, engine, view_model, settings_view_model, main, engine.rootObjects()[1]


def test_main_window_resizes_collapses_and_hides_settings_search(repository, tmp_path):
    application, engine, view_model, settings, window, widget = _load_main_and_widget(repository, tmp_path)
    assert window.property("minimumWidth") == 900
    assert window.property("minimumHeight") == 620
    assert window.property("maximumWidth") > 10000
    assert window.findChild(QObject, "mainSplitView")
    assert window.findChild(QObject, "contentSplitView")

    sidebar = window.findChild(QObject, "sidebarPanel")
    task_panel = window.findChild(QObject, "taskListPanel")
    details = window.findChild(QObject, "detailsPanel")
    window.setProperty("width", 900)
    application.processEvents()
    narrow_task_width = task_panel.property("width")
    assert sidebar.property("width") >= 150
    assert task_panel.property("width") >= 260
    assert details.property("width") >= 300

    window.setProperty("width", 1500)
    application.processEvents()
    assert task_panel.property("width") > narrow_task_width

    collapse = window.findChild(QObject, "collapseEditorButton")
    collapse.clicked.emit()
    application.processEvents()
    assert settings.editorCollapsed
    assert not details.property("visible")

    new_task = window.findChild(QObject, "newTaskButton")
    new_task.clicked.emit()
    application.processEvents()
    assert view_model.isCreating
    assert not settings.editorCollapsed
    assert details.property("visible")

    view_model.cancelNewTask()
    view_model.setView("settings")
    application.processEvents()
    search = window.findChild(QObject, "taskSearchField")
    assert not search.property("visible")
    about_version = window.findChild(QObject, "aboutVersionText")
    assert about_version.property("text") == "PourTask 1.2.0-beta.1"

    widget.close()
    window.close()
    application.processEvents()
    del engine


def test_editor_date_controls_wrap_without_overlap(repository, tmp_path):
    application, engine, view_model, settings, window, widget = _load_main_and_widget(repository, tmp_path)
    settings.setMainSplitters(150, 300)
    window.setProperty("lastEditorWidth", 300)
    window.setProperty("width", 900)
    window.findChild(QObject, "newTaskButton").clicked.emit()
    application.processEvents()

    schedule = window.findChild(QObject, "scheduleDateField")
    schedule.setProperty("text", "07/23/2026")
    application.processEvents()
    input_field = window.findChild(QObject, "scheduleDateFieldInput")
    calendar = window.findChild(QObject, "scheduleCalendarButton")
    clear = window.findChild(QObject, "scheduleDateFieldClearButton")
    assert schedule.property("width") >= 0
    assert all((input_field, calendar, clear))

    input_bottom = input_field.property("y") + input_field.property("height")
    controls_on_second_line = (
        calendar.property("y") >= input_bottom
        and clear.property("y") >= input_bottom
    )
    controls_beside_input = (
        input_field.property("x") + input_field.property("width") <= calendar.property("x")
        and calendar.property("x") + calendar.property("width") <= clear.property("x")
    )
    assert controls_on_second_line or controls_beside_input

    widget.close()
    window.close()
    application.processEvents()
    del engine


def test_widget_defaults_compact_restore_and_quick_add(repository, tmp_path):
    application, engine, view_model, settings, window, widget = _load_main_and_widget(repository, tmp_path)
    assert widget.property("width") == 260
    assert widget.property("height") == 180
    assert widget.property("minimumWidth") == 220
    assert widget.property("minimumHeight") == 130
    assert widget.findChild(QObject, "widgetDragArea")
    assert widget.findChild(QObject, "widgetLeftResizeHandle")
    assert widget.findChild(QObject, "widgetBottomResizeHandle")
    assert not settings.widgetAlwaysOnTop
    assert not settings.widgetLockPosition

    widget.setProperty("width", 310)
    widget.setProperty("height", 230)
    compact = widget.findChild(QObject, "widgetCompactButton")
    compact.clicked.emit()
    application.processEvents()
    assert settings.widgetCompact
    assert widget.property("height") == 80
    assert widget.property("minimumHeight") == 70

    compact.clicked.emit()
    application.processEvents()
    assert not settings.widgetCompact
    assert widget.property("width") == 310
    assert widget.property("height") == 230

    quick_add = widget.findChild(QObject, "widgetQuickAdd")
    quick_add.setProperty("text", "Widget task")
    quick_add.accepted.emit()
    application.processEvents()
    created = repository.all()
    assert len(created) == 1
    assert created[0].scheduled_date == date.today()
    assert created[0].assigned_month == date.today().strftime("%Y-%m")
    assert quick_add.property("text") == ""

    task_list = widget.findChild(QObject, "widgetTaskList")
    assert task_list.property("count") == 1
    view_model.setCompleted(created[0].id, True)
    application.processEvents()
    assert task_list.property("count") == 0

    widget.close()
    window.close()
    application.processEvents()
    del engine


def test_layout_settings_round_trip(tmp_path):
    settings = Settings(tmp_path / "settings.json")
    view_model = SettingsViewModel(settings, tmp_path / "PourTask.exe")
    view_model.setMainSplitters(182.4, 412.8)
    view_model.setEditorCollapsed(True)
    view_model.setWidgetExpandedSize(305, 215)
    view_model.setWidgetGeometry(90, 110, 305, 215)
    view_model.setWidgetCompact(True)
    view_model.setWidgetAlwaysOnTop(True)
    view_model.setWidgetLockPosition(True)

    restored = Settings(tmp_path / "settings.json")
    assert restored.values["main_splitters"] == {"sidebar": 182, "editor": 413}
    assert restored.values["editor_collapsed"] is True
    assert restored.values["widget_expanded_size"] == {"width": 305, "height": 215}
    assert restored.values["widget_geometry"] == {"x": 90, "y": 110, "width": 305, "height": 215}
    assert restored.values["widget_compact"] is True
    assert restored.values["widget_always_on_top"] is True
    assert restored.values["widget_lock_position"] is True
