from datetime import date

from app.database import TaskRepository
from app.services import TaskService
from app.services.task_queries import completed, due_soon, inbox, month, search, today


def test_required_task_flow_survives_repository_restart(database):
    day = date.today()
    repository = TaskRepository(database)
    service = TaskService(repository)
    created = service.create("Inbox item", notes="Find this phrase")
    assert inbox(repository.all()) == [created]
    moved = service.move_to_today(created.id, day)
    assert today(repository.all(), day)[0].id == moved.id
    assert month(repository.all(), day.strftime("%Y-%m"))[0].id == moved.id
    service.set_completed(created.id, True)
    assert today(repository.all(), day) == []
    assert completed(repository.all())[0].id == created.id
    service.set_completed(created.id, False)
    assert search(repository.all(), "THIS PHRASE")[0].id == created.id
    deadline = service.create("Deadline only", due_date=day)
    assert due_soon(repository.all(), day)[0].id == deadline.id
    reopened = TaskRepository(database)
    assert {task.id for task in reopened.all()} == {created.id, deadline.id}
