from __future__ import annotations

from datetime import date, timedelta

from app.models import Task

DUE_SOON_DAYS = 3


def month_key(day: date) -> str:
    return day.strftime("%Y-%m")


def inbox(tasks: list[Task]) -> list[Task]:
    return _sort(t for t in tasks if not t.completed and not t.scheduled_date and not t.due_date and not t.assigned_month)


def today(tasks: list[Task], day: date) -> list[Task]:
    return _sort(t for t in tasks if not t.completed and t.scheduled_date == day)


def month(tasks: list[Task], selected: str) -> list[Task]:
    return _sort(t for t in tasks if not t.completed and (
        (t.scheduled_date and month_key(t.scheduled_date) == selected)
        or (t.due_date and month_key(t.due_date) == selected)
        or (not t.scheduled_date and not t.due_date and t.assigned_month == selected)
    ))


def overdue(tasks: list[Task], day: date) -> list[Task]:
    return _sort(t for t in tasks if not t.completed and (
        (t.scheduled_date is not None and t.scheduled_date < day)
        or (t.due_date is not None and t.due_date < day)
    ))


def due_soon(tasks: list[Task], day: date, window: int = DUE_SOON_DAYS) -> list[Task]:
    end = day + timedelta(days=window)
    return _sort(t for t in tasks if not t.completed and t.scheduled_date is None
                 and t.due_date is not None and day <= t.due_date <= end)


def completed(tasks: list[Task]) -> list[Task]:
    return sorted((t for t in tasks if t.completed), key=lambda t: (t.completed_at or t.updated_at), reverse=True)


def search(tasks: list[Task], query: str) -> list[Task]:
    needle = query.strip().casefold()
    if not needle:
        return []
    return [t for t in tasks if needle in t.title.casefold() or needle in t.notes.casefold()]


def _sort(tasks) -> list[Task]:
    far = date.max
    return sorted(tasks, key=lambda t: (t.scheduled_date or far, t.due_date or far, t.created_at, t.id))
