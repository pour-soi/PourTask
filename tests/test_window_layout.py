from datetime import date
from pathlib import Path

from PySide6.QtCore import QObject, QUrl
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from shiboken6 import getCppPointer, wrapInstance

from app import __version__
from app.settings import Settings
from app.strings import STRINGS
from app.viewmodels import AppViewModel
from app.viewmodels.settings_viewmodel import SettingsViewModel


def _load_main_and_widget(repository, tmp_path: Path):
    application = QApplication.instance() or QApplication([])
    engine = QQmlApplicationEngine()
    warnings = []
    engine._warnings = warnings
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


def _visual_items_with_name(item, object_name: str):
    if not isinstance(item, QQuickItem):
        item = wrapInstance(getCppPointer(item)[0], QQuickItem)
    matches = []
    for child in item.childItems():
        if child.objectName() == object_name:
            matches.append(child)
        matches.extend(_visual_items_with_name(child, object_name))
    return matches


def test_main_window_resizes_collapses_and_hides_settings_search(repository, tmp_path):
    application, engine, view_model, settings, window, widget = _load_main_and_widget(repository, tmp_path)
    assert window.property("minimumWidth") == 720
    assert window.property("minimumHeight") == 520
    QTest.qWait(75)
    assert not window.property("editorCollapsed")
    assert window.property("maximumWidth") > 10000
    assert window.findChild(QObject, "mainSplitView")
    assert window.findChild(QObject, "contentSplitView")

    sidebar = window.findChild(QObject, "sidebarPanel")
    task_panel = window.findChild(QObject, "taskListPanel")
    details = window.findChild(QObject, "detailsPanel")
    window.setProperty("width", 720)
    application.processEvents()
    assert sidebar.property("width") >= 130
    assert task_panel.property("width") >= 180
    assert details.property("width") >= 260

    window.setProperty("width", 1500)
    application.processEvents()
    window.findChild(QObject, "expandEditorButton").clicked.emit()
    application.processEvents()
    assert details.property("width") > task_panel.property("width")

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
    assert about_version.property("text") == "PourTask 1.2.0-beta.2"

    widget.close()
    window.close()
    application.processEvents()
    del engine


def test_editor_date_controls_wrap_without_overlap(repository, tmp_path):
    application, engine, view_model, settings, window, widget = _load_main_and_widget(repository, tmp_path)
    settings.setMainSplitters(130, 180, 280)
    window.setProperty("lastEditorWidth", 280)
    window.setProperty("width", 720)
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
    widget.show()
    application.processEvents()
    assert widget.property("width") == 260
    assert widget.property("height") == 160
    assert widget.property("minimumWidth") == 220
    assert widget.property("minimumHeight") == 115
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
    assert widget.property("height") == 70
    assert widget.property("minimumHeight") == 60
    assert not widget.findChild(QObject, "widgetTaskList").property("visible")
    assert not widget.findChild(QObject, "widgetQuickAdd").property("visible")

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
    rows = _visual_items_with_name(task_list, "widgetTaskRow")
    assert len(rows) == 1, "\n".join(engine._warnings)
    title = rows[0].findChild(QObject, "widgetTaskTitle")
    assert title.property("text") == "Widget task"
    assert rows[0].property("height") == 30
    rows[0].toggled.emit(True)
    application.processEvents()
    assert task_list.property("count") == 0
    assert repository.get(created[0].id).completed

    widget.close()
    window.close()
    application.processEvents()
    del engine


def test_layout_settings_round_trip(tmp_path):
    settings = Settings(tmp_path / "settings.json")
    view_model = SettingsViewModel(settings, tmp_path / "PourTask.exe")
    view_model.setMainSplitters(154.4, 326.2, 479.8)
    view_model.setEditorCollapsed(True)
    view_model.setWidgetExpandedSize(305, 215)
    view_model.setWidgetGeometry(90, 110, 305, 215)
    view_model.setWidgetCompact(True)
    view_model.setWidgetAlwaysOnTop(True)
    view_model.setWidgetLockPosition(True)

    restored = Settings(tmp_path / "settings.json")
    assert restored.values["main_splitters"] == {
        "sidebar": 154, "task": 326, "editor": 480,
    }
    assert restored.values["editor_collapsed"] is True
    assert restored.values["widget_expanded_size"] == {"width": 305, "height": 215}
    assert restored.values["widget_geometry"] == {"x": 90, "y": 110, "width": 305, "height": 215}
    assert restored.values["widget_compact"] is True
    assert restored.values["widget_always_on_top"] is True
    assert restored.values["widget_lock_position"] is True


def test_editor_auto_collapse_preserves_unsaved_content(repository, tmp_path):
    application, engine, view_model, settings, window, widget = _load_main_and_widget(
        repository, tmp_path
    )
    window.findChild(QObject, "newTaskButton").clicked.emit()
    title = window.findChild(QObject, "taskTitleField")
    title.setProperty("text", "Keep this draft")

    window.collapseEditorIfNeeded(400)
    application.processEvents()
    assert settings.editorCollapsed

    window.setProperty("width", 960)
    window.setProperty("lastSidebarWidth", 154)
    application.processEvents()
    window.findChild(QObject, "expandEditorButton").clicked.emit()
    application.processEvents()
    assert not settings.editorCollapsed
    assert title.property("text") == "Keep this draft"

    widget.close()
    window.close()
    application.processEvents()
    del engine


def test_widget_empty_multiple_and_long_titles_render_compactly(repository, tmp_path):
    application, engine, view_model, settings, window, widget = _load_main_and_widget(
        repository, tmp_path
    )
    widget.show()
    application.processEvents()
    task_list = widget.findChild(QObject, "widgetTaskList")
    quick_add = widget.findChild(QObject, "widgetQuickAdd")
    empty = widget.findChild(QObject, "widgetEmptyState")
    assert task_list.property("count") == 0
    assert empty.property("visible")
    assert quick_add.property("visible")

    titles = [
        "First task",
        "Second task",
        "A very long Today task title that must be elided inside the small widget",
    ]
    for title in titles:
        assert view_model.addTodayTask(title)
    widget.setProperty("height", 260)
    QTest.qWait(50)
    application.processEvents()

    rows = _visual_items_with_name(task_list, "widgetTaskRow")
    assert task_list.property("count") == 3
    assert len(rows) == 3, (
        f"widget height={widget.property('height')} list height={task_list.property('height')} "
        f"contentHeight={task_list.property('contentHeight')} rows={len(rows)}"
    )
    assert all(row.property("height") == 30 for row in rows)
    title_items = _visual_items_with_name(task_list, "widgetTaskTitle")
    assert {item.property("text") for item in title_items} == set(titles)
    assert all(item.property("maximumLineCount") == 1 for item in title_items)

    widget.close()
    window.close()
    application.processEvents()
    del engine
