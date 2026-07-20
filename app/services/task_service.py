from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timezone

from app.database import TaskRepository
from app.models import Task


class TaskService:
    def __init__(self, repository: TaskRepository):
        self.repository = repository

    @staticmethod
    def date_warning(scheduled: date | None, due: date | None) -> str | None:
        if scheduled and due and scheduled > due:
            return "Scheduled date must not be later than the deadline."
        return None

    def create(self, title: str, **values) -> Task:
        warning = self.date_warning(values.get("scheduled_date"), values.get("due_date"))
        if warning:
            raise ValueError(warning)
        return self.repository.create(title, **values)

    def edit(self, task_id: str, *, title: str, notes: str, scheduled_date: date | None,
             due_date: date | None, assigned_month: str | None) -> tuple[Task, str | None]:
        task = self.repository.get(task_id)
        if task is None:
            raise KeyError(task_id)
        warning = self.date_warning(scheduled_date, due_date)
        if warning:
            return self.repository.update(replace(task, title=title, notes=notes)), warning
        return self.repository.update(replace(task, title=title, notes=notes,
                                              scheduled_date=scheduled_date, due_date=due_date,
                                              assigned_month=assigned_month)), None

    def set_completed(self, task_id: str, completed: bool) -> Task:
        task = self.repository.get(task_id)
        if task is None:
            raise KeyError(task_id)
        timestamp = datetime.now(timezone.utc) if completed else None
        return self.repository.update(replace(task, completed=completed, completed_at=timestamp))

    def move_to_today(self, task_id: str, day: date) -> Task:
        task = self.repository.get(task_id)
        if task is None:
            raise KeyError(task_id)
        return self.repository.update(replace(task, scheduled_date=day, assigned_month=None))
