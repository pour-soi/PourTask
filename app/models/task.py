from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True, slots=True)
class Task:
    id: str
    title: str
    notes: str = ""
    scheduled_date: date | None = None
    due_date: date | None = None
    assigned_month: str | None = None
    completed: bool = False
    created_at: datetime | None = None
    updated_at: datetime | None = None
    completed_at: datetime | None = None
