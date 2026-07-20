from __future__ import annotations

from dataclasses import replace
from datetime import date, datetime, timezone
from uuid import uuid4

from app.models import Task
from .connection import Database


def _iso(value):
    return value.isoformat() if value is not None else None


def _task(row) -> Task:
    return Task(
        id=row["id"], title=row["title"], notes=row["notes"],
        scheduled_date=date.fromisoformat(row["scheduled_date"]) if row["scheduled_date"] else None,
        due_date=date.fromisoformat(row["due_date"]) if row["due_date"] else None,
        assigned_month=row["assigned_month"], completed=bool(row["completed"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        updated_at=datetime.fromisoformat(row["updated_at"]),
        completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
    )


class TaskRepository:
    def __init__(self, database: Database):
        self.database = database

    def create(self, title: str, notes: str = "", scheduled_date: date | None = None,
               due_date: date | None = None, assigned_month: str | None = None) -> Task:
        title = title.strip()
        if not title:
            raise ValueError("Title cannot be empty")
        now = datetime.now(timezone.utc)
        task = Task(str(uuid4()), title, notes, scheduled_date, due_date, assigned_month,
                    False, now, now, None)
        with self.database.session() as connection:
            connection.execute(
                """INSERT INTO tasks(id,title,notes,scheduled_date,due_date,assigned_month,completed,created_at,updated_at,completed_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (task.id, task.title, task.notes, _iso(task.scheduled_date), _iso(task.due_date),
                 task.assigned_month, 0, _iso(now), _iso(now), None),
            )
        return task

    def get(self, task_id: str) -> Task | None:
        with self.database.session() as connection:
            row = connection.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return _task(row) if row else None

    def all(self) -> list[Task]:
        with self.database.session() as connection:
            rows = connection.execute("SELECT * FROM tasks ORDER BY created_at, id").fetchall()
        return [_task(row) for row in rows]

    def update(self, task: Task) -> Task:
        title = task.title.strip()
        if not title:
            raise ValueError("Title cannot be empty")
        updated = replace(task, title=title, updated_at=datetime.now(timezone.utc))
        with self.database.session() as connection:
            cursor = connection.execute(
                """UPDATE tasks SET title=?,notes=?,scheduled_date=?,due_date=?,assigned_month=?,completed=?,updated_at=?,completed_at=? WHERE id=?""",
                (updated.title, updated.notes, _iso(updated.scheduled_date), _iso(updated.due_date),
                 updated.assigned_month, int(updated.completed), _iso(updated.updated_at),
                 _iso(updated.completed_at), updated.id),
            )
            if cursor.rowcount != 1:
                raise KeyError(task.id)
        return updated

    def delete(self, task_id: str) -> Task:
        task = self.get(task_id)
        if task is None:
            raise KeyError(task_id)
        with self.database.session() as connection:
            connection.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        return task

    def restore_record(self, task: Task) -> None:
        with self.database.session() as connection:
            connection.execute(
                """INSERT INTO tasks VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (task.id, task.title, task.notes, _iso(task.scheduled_date), _iso(task.due_date),
                 task.assigned_month, int(task.completed), _iso(task.created_at), _iso(task.updated_at),
                 _iso(task.completed_at)),
            )
