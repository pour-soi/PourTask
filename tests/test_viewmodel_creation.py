from datetime import date

import pytest

from app.viewmodels import AppViewModel


def test_today_new_task_defaults_and_does_not_create_before_save(repository):
    view_model = AppViewModel(repository)
    view_model.beginNewTask()

    assert view_model.isCreating
    assert view_model.newTaskDefaults["scheduledDate"] == date.today().strftime("%m/%d/%Y")
    assert view_model.newTaskDefaults["assignedMonth"] == date.today().strftime("%m/%Y")
    assert repository.all() == []


def test_month_and_inbox_new_task_defaults(repository):
    view_model = AppViewModel(repository)
    view_model.setView("month")
    selected_month = view_model.selectedMonth
    view_model.beginNewTask()
    assert view_model.newTaskDefaults["assignedMonth"] == date.fromisoformat(selected_month + "-01").strftime("%m/%Y")
    assert view_model.newTaskDefaults["scheduledDate"] == ""

    view_model.setView("inbox")
    view_model.beginNewTask()
    assert view_model.newTaskDefaults["scheduledDate"] == ""
    assert view_model.newTaskDefaults["dueDate"] == ""
    assert view_model.newTaskDefaults["assignedMonth"] == ""


def test_cancel_restores_selection_without_creating(repository):
    original = repository.create("Existing")
    view_model = AppViewModel(repository)
    view_model.openDetail(original.id)

    view_model.beginNewTask()
    view_model.cancelNewTask()

    assert not view_model.isCreating
    assert view_model.selectedTask["id"] == original.id
    assert [task.id for task in repository.all()] == [original.id]


@pytest.mark.parametrize("source", ["completed", "search", "settings"])
def test_new_task_from_non_task_view_follows_to_inbox(repository, source):
    view_model = AppViewModel(repository)
    if source == "search":
        view_model.setSearch("missing")
    else:
        view_model.setView(source)
    view_model.beginNewTask()

    result = view_model.createTask("Created", "Notes", "", "", "")

    assert result["ok"]
    assert view_model.currentView == "inbox"
    assert view_model.selectedTask["id"] == result["taskId"]
    assert view_model.message == "Task created in Inbox."


def test_save_new_task_follows_to_today_and_keeps_selection(repository):
    view_model = AppViewModel(repository)
    view_model.setView("inbox")
    view_model.beginNewTask()
    today = date.today().strftime("%m/%d/%Y")

    result = view_model.createTask("Today task", "", today, "", "")

    assert result["ok"]
    assert view_model.currentView == "today"
    assert view_model.selectedTask["id"] == result["taskId"]
    assert view_model.selectedTask["scheduledDate"] == today
    assert repository.get(result["taskId"]).scheduled_date == date.today()


def test_inbox_and_month_creation_stay_in_their_destination(repository):
    view_model = AppViewModel(repository)
    view_model.setView("inbox")
    view_model.beginNewTask()
    inbox_result = view_model.createTask("Inbox task", "", "", "", "")
    assert inbox_result["ok"] and view_model.currentView == "inbox"

    view_model.setView("month")
    selected_month = view_model.selectedMonth
    view_model.beginNewTask()
    month_result = view_model.createTask(
        "Month task", "", "", "", date.fromisoformat(selected_month + "-01").strftime("%m/%Y")
    )
    assert month_result["ok"]
    assert view_model.currentView == "month"
    assert view_model.selectedTask["id"] == month_result["taskId"]


def test_field_errors_are_separate_and_do_not_create(repository):
    view_model = AppViewModel(repository)
    view_model.beginNewTask()

    result = view_model.createTask("", "", "02/30/2026", "", "13/2026")

    assert not result["ok"]
    assert result["errors"] == {
        "title": "Enter a task title.",
        "scheduled": "Enter a valid date, for example 07/23/2026.",
        "assigned": "Enter a valid month, for example 07/2026.",
    }
    assert repository.all() == []


def test_edit_uses_us_display_but_keeps_iso_database_values(repository):
    task = repository.create("Existing", scheduled_date=date(2026, 7, 23), assigned_month="2026-07")
    view_model = AppViewModel(repository)
    view_model.openDetail(task.id)
    assert view_model.selectedTask["scheduledDate"] == "07/23/2026"
    assert view_model.selectedTask["assignedMonth"] == "07/2026"

    result = view_model.saveDetail("Existing", "", "08/01/2026", "", "08/2026")
    stored = repository.get(task.id)

    assert result["ok"]
    assert stored.scheduled_date == date(2026, 8, 1)
    assert stored.assigned_month == "2026-08"


def test_edit_can_clear_date_fields(repository):
    task = repository.create("Existing", scheduled_date=date(2026, 7, 23), due_date=date(2026, 7, 24))
    view_model = AppViewModel(repository)
    view_model.openDetail(task.id)

    result = view_model.saveDetail("Existing", "", "", "", "")

    assert result["ok"]
    stored = repository.get(task.id)
    assert stored.scheduled_date is None
    assert stored.due_date is None


def test_edit_follows_task_when_it_leaves_current_view(repository):
    task = repository.create("Move me")
    view_model = AppViewModel(repository)
    view_model.setView("inbox")
    view_model.openDetail(task.id)
    future = date.today().replace(day=1)
    future = date(future.year + (future.month == 12), future.month % 12 + 1, 15)

    result = view_model.saveDetail("Move me", "", future.strftime("%m/%d/%Y"), "", "")

    assert result["ok"]
    assert view_model.currentView == "month"
    assert view_model.selectedMonth == future.strftime("%Y-%m")
    assert view_model.selectedTask["id"] == task.id
