from datetime import date, datetime, timezone

from app.models import Task
from app.services.task_queries import completed, due_soon, inbox, month, overdue, today


def task(name, **values):
    return Task(id=name, title=name, created_at=datetime(2026, 7, 1, tzinfo=timezone.utc),
                updated_at=datetime(2026, 7, 1, tzinfo=timezone.utc), **values)


def test_cross_month_task_appears_in_both_months_as_one_record():
    item = task("cross", scheduled_date=date(2026, 7, 28), due_date=date(2026, 8, 5))
    assert month([item], "2026-07") == [item]
    assert month([item], "2026-08") == [item]


def test_month_only_task_moves_between_months():
    july = task("month-only", assigned_month="2026-07")
    assert month([july], "2026-07") == [july]
    assert month([july], "2026-08") == []


def test_due_soon_excludes_scheduled_overdue_and_completed_tasks():
    day = date(2026, 7, 20)
    deadline = task("deadline", due_date=date(2026, 7, 23))
    scheduled = task("scheduled", scheduled_date=day, due_date=date(2026, 7, 21))
    late = task("late", due_date=date(2026, 7, 19))
    done = task("done", due_date=date(2026, 7, 21), completed=True)
    assert due_soon([deadline, scheduled, late, done], day) == [deadline]


def test_active_views_do_not_duplicate_or_move_dates():
    day = date(2026, 7, 20)
    old = task("old", scheduled_date=date(2026, 7, 19))
    current = task("today", scheduled_date=day)
    loose = task("inbox")
    assert overdue([old], day) == [old]
    assert old.scheduled_date == date(2026, 7, 19)
    assert today([current], day) == [current]
    assert inbox([loose]) == [loose]


def test_completed_sorted_most_recent_first():
    first = task("first", completed=True, completed_at=datetime(2026, 7, 19, tzinfo=timezone.utc))
    second = task("second", completed=True, completed_at=datetime(2026, 7, 20, tzinfo=timezone.utc))
    assert completed([first, second]) == [second, first]
