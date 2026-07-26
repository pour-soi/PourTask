from datetime import date

from app.database import Database, TaskRepository
from app.viewmodels import AppViewModel


def test_v1_database_opens_displays_and_saves_without_migration(tmp_path):
    path = tmp_path / "v1-pourtask.db"
    original_repository = TaskRepository(Database(path))
    task = original_repository.create(
        "v1 task", notes="preserved", scheduled_date=date(2026, 7, 23),
        due_date=date(2026, 8, 1), assigned_month="2026-07",
    )

    reopened = TaskRepository(Database(path))
    view_model = AppViewModel(reopened)
    view_model.openDetail(task.id)

    assert view_model.selectedTask["scheduledDate"] == "07/23/2026"
    assert view_model.selectedTask["dueDate"] == "08/01/2026"
    assert view_model.selectedTask["assignedMonth"] == "07/2026"

    result = view_model.saveDetail("v1 task edited", "preserved", "7/24/2026", "8/1/2026", "07/2026")
    saved = reopened.get(task.id)

    assert result["ok"]
    assert saved.title == "v1 task edited"
    assert saved.scheduled_date == date(2026, 7, 24)
    assert saved.due_date == date(2026, 8, 1)
    assert saved.assigned_month == "2026-07"
