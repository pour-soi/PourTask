from pathlib import Path

from PySide6.QtCore import QMetaObject, QObject, Qt, QUrl
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

from app.strings import STRINGS
from app.viewmodels import AppViewModel
from app.viewmodels.settings_viewmodel import SettingsViewModel
from app.settings import Settings


def test_main_qml_loads(repository, tmp_path: Path):
    application = QApplication.instance() or QApplication([])
    engine = QQmlApplicationEngine()
    warnings = []
    engine.warnings.connect(lambda items: warnings.extend(item.toString() for item in items))
    engine.rootContext().setContextProperty("appViewModel", AppViewModel(repository))
    engine.rootContext().setContextProperty("settingsViewModel", SettingsViewModel(Settings(tmp_path / "settings.json"), tmp_path / "PourTask.exe"))
    engine.rootContext().setContextProperty("strings", STRINGS)
    engine.rootContext().setContextProperty("launchHidden", False)
    engine.rootContext().setContextProperty("trayAvailable", False)
    qml = Path(__file__).parents[1] / "app" / "qml" / "Main.qml"
    engine.load(QUrl.fromLocalFile(str(qml)))
    assert engine.rootObjects(), "\n".join(warnings)
    engine.rootObjects()[0].close()
    application.processEvents()


def test_new_task_editor_and_pickers_are_interactive(repository, tmp_path: Path):
    application = QApplication.instance() or QApplication([])
    engine = QQmlApplicationEngine()
    view_model = AppViewModel(repository)
    engine.rootContext().setContextProperty("appViewModel", view_model)
    engine.rootContext().setContextProperty("settingsViewModel", SettingsViewModel(Settings(tmp_path / "settings.json"), tmp_path / "PourTask.exe"))
    engine.rootContext().setContextProperty("strings", STRINGS)
    engine.rootContext().setContextProperty("launchHidden", False)
    engine.rootContext().setContextProperty("trayAvailable", False)
    qml = Path(__file__).parents[1] / "app" / "qml" / "Main.qml"
    engine.load(QUrl.fromLocalFile(str(qml)))
    window = engine.rootObjects()[0]

    new_button = window.findChild(QObject, "newTaskButton")
    assert new_button is not None
    new_button.clicked.emit()
    application.processEvents()

    title = window.findChild(QObject, "taskTitleField")
    notes = window.findChild(QObject, "taskNotesField")
    schedule = window.findChild(QObject, "scheduleDateField")
    due = window.findChild(QObject, "dueDateField")
    month = window.findChild(QObject, "assignedMonthField")
    save = window.findChild(QObject, "saveTaskButton")
    cancel = window.findChild(QObject, "cancelTaskButton")
    delete = window.findChild(QObject, "deleteTaskButton")
    assert all((title, notes, schedule, due, month, save, cancel, delete))
    assert view_model.isCreating
    assert title.property("activeFocus")
    assert save.property("visible") and cancel.property("visible")
    assert not delete.property("visible")

    schedule.setProperty("text", "07232026")
    assert QMetaObject.invokeMethod(schedule, "normalize")
    application.processEvents()
    assert schedule.property("text") == "07/23/2026"

    assert QMetaObject.invokeMethod(schedule, "openCalendar")
    application.processEvents()
    schedule_popup = window.findChild(QObject, "scheduleCalendarButtonPopup")
    due_popup = window.findChild(QObject, "dueCalendarButtonPopup")
    month_popup = window.findChild(QObject, "assignedMonthFieldPopup")
    assert schedule_popup.property("opened")

    assert QMetaObject.invokeMethod(due, "openCalendar")
    application.processEvents()
    assert due_popup.property("opened")
    assert not schedule_popup.property("opened")

    assert QMetaObject.invokeMethod(month, "openPicker")
    application.processEvents()
    assert month_popup.property("opened")
    assert not due_popup.property("opened")
    QTest.keyClick(window, Qt.Key_Escape)
    application.processEvents()
    assert not month_popup.property("opened")
    assert view_model.isCreating

    for width in (1100, 1300, 1500, 1700):
        window.setProperty("width", width)
        application.processEvents()
        assert QMetaObject.invokeMethod(schedule, "openCalendar")
        application.processEvents()
        assert schedule_popup.property("x") >= 0
        assert schedule_popup.property("y") >= 0
        assert schedule_popup.property("x") + schedule_popup.property("width") <= width
        assert schedule_popup.property("y") + schedule_popup.property("height") <= window.property("height")
        schedule_popup.close()
        assert QMetaObject.invokeMethod(month, "openPicker")
        application.processEvents()
        assert month_popup.property("x") >= 0
        assert month_popup.property("y") >= 0
        assert month_popup.property("x") + month_popup.property("width") <= width
        assert month_popup.property("y") + month_popup.property("height") <= window.property("height")
        month_popup.close()

    month_input = window.findChild(QObject, "assignedMonthFieldInput")
    month_input.setProperty("text", "09/2027")
    month_input.textEdited.emit()
    schedule.setProperty("text", "08/01/2026")
    assert QMetaObject.invokeMethod(schedule, "normalize")
    application.processEvents()
    assert month_input.property("text") == "09/2027"

    cancel.clicked.emit()
    application.processEvents()
    assert not view_model.isCreating
    assert repository.all() == []

    new_button.clicked.emit()
    application.processEvents()
    title.setProperty("text", "Keyboard task")
    notes.setProperty("text", "First line")
    QMetaObject.invokeMethod(notes, "forceActiveFocus")
    QTest.keyClick(window, Qt.Key_Return)
    application.processEvents()
    assert repository.all() == []
    assert "\n" in notes.property("text")
    QTest.keyClick(window, Qt.Key_Return, Qt.KeyboardModifier.ControlModifier)
    application.processEvents()
    assert [task.title for task in repository.all()] == ["Keyboard task"]

    new_button.clicked.emit()
    application.processEvents()
    QTest.keyClick(window, Qt.Key_Escape)
    application.processEvents()
    assert not view_model.isCreating
    assert [task.title for task in repository.all()] == ["Keyboard task"]

    window.close()
    application.processEvents()
