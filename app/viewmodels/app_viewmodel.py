from __future__ import annotations

from dataclasses import replace
from datetime import date

from PySide6.QtCore import QAbstractListModel, QByteArray, QModelIndex, Property, Qt, Signal, Slot

from app.database import TaskRepository
from app.models import Task
from app.services import TaskService
from app.services import task_queries
from app.services.undo_service import UndoService
from app.services.backup_service import BackupService, BackupError
from PySide6.QtWidgets import QFileDialog


class TaskListModel(QAbstractListModel):
    IdRole, TitleRole, NotesRole, CompletedRole, DateRole, DateKindRole, WarningRole = range(Qt.UserRole + 1, Qt.UserRole + 8)

    def __init__(self):
        super().__init__()
        self.tasks: list[Task] = []

    def roleNames(self):
        return {
            self.IdRole: QByteArray(b"taskId"), self.TitleRole: QByteArray(b"title"),
            self.NotesRole: QByteArray(b"notes"), self.CompletedRole: QByteArray(b"completed"),
            self.DateRole: QByteArray(b"displayDate"), self.DateKindRole: QByteArray(b"dateKind"),
            self.WarningRole: QByteArray(b"warning"),
        }

    def rowCount(self, parent=QModelIndex()): return 0 if parent.isValid() else len(self.tasks)

    def data(self, index, role):
        if not index.isValid() or not 0 <= index.row() < len(self.tasks): return None
        task = self.tasks[index.row()]
        if role == self.IdRole: return task.id
        if role == self.TitleRole: return task.title
        if role == self.NotesRole: return task.notes
        if role == self.CompletedRole: return task.completed
        if role == self.DateRole:
            return (task.scheduled_date or task.due_date).isoformat() if (task.scheduled_date or task.due_date) else ""
        if role == self.DateKindRole:
            return "Scheduled" if task.scheduled_date else ("Deadline" if task.due_date else "Unscheduled")
        if role == self.WarningRole:
            day = date.today()
            if task.scheduled_date and task.scheduled_date < day and not task.completed: return "Previously scheduled"
            if task.due_date and task.due_date < day and not task.completed: return "Overdue"
        return ""

    def reset_tasks(self, tasks: list[Task]):
        self.beginResetModel(); self.tasks = tasks; self.endResetModel()


class AppViewModel(QAbstractListModel):
    viewChanged = Signal()
    monthChanged = Signal()
    messageChanged = Signal()
    detailChanged = Signal()

    def __init__(self, repository: TaskRepository):
        super().__init__()
        self.repository = repository
        self.service = TaskService(repository)
        self.undo_service = UndoService()
        self.backups = BackupService(repository.database, repository.database.path.parent.parent / "backups")
        self.model = TaskListModel()
        self._view, self._month, self._query, self._message = "today", date.today().strftime("%Y-%m"), "", ""
        self._view_before_search = "today"
        self._selected: Task | None = None
        self.refresh()

    @Property("QVariant", constant=True)
    def tasks(self): return self.model
    @Property(str, notify=viewChanged)
    def currentView(self): return self._view
    @Property(str, notify=monthChanged)
    def selectedMonth(self): return self._month
    @Property(str, notify=messageChanged)
    def message(self): return self._message
    @Property(bool, notify=detailChanged)
    def detailOpen(self): return self._selected is not None
    @Property("QVariantMap", notify=detailChanged)
    def selectedTask(self):
        task = self._selected
        return {} if not task else {"id": task.id, "title": task.title, "notes": task.notes,
            "scheduledDate": task.scheduled_date.isoformat() if task.scheduled_date else "",
            "dueDate": task.due_date.isoformat() if task.due_date else "",
            "assignedMonth": task.assigned_month or "", "completed": task.completed}

    def _tell(self, message): self._message = message; self.messageChanged.emit()

    @Slot(str)
    def setView(self, view):
        self._view, self._query = view, ""
        self._selected = None
        self.detailChanged.emit(); self.viewChanged.emit(); self.refresh()

    @Slot(str)
    def setSearch(self, query):
        if self._view != "search":
            self._view_before_search = self._view
            self._selected = None; self.detailChanged.emit()
        self._query = query; self._view = "search"; self.viewChanged.emit(); self.refresh()

    @Slot()
    def clearSearch(self): self.setView(self._view_before_search)

    @Slot(int)
    def changeMonth(self, offset):
        year, month = map(int, self._month.split("-")); month += offset
        year += (month - 1) // 12; month = (month - 1) % 12 + 1
        self._month = f"{year:04d}-{month:02d}"; self.monthChanged.emit(); self.refresh()

    @Slot()
    def currentMonth(self): self._month = date.today().strftime("%Y-%m"); self.monthChanged.emit(); self.refresh()

    @Slot(str)
    def addTask(self, title):
        try: self.service.create(title)
        except ValueError as exc: self._tell(str(exc)); return
        self._tell("Task created"); self.refresh()

    @Slot(str)
    def moveToToday(self, task_id): self.service.move_to_today(task_id, date.today()); self.refresh()

    @Slot(str, bool)
    def setCompleted(self, task_id, completed):
        old = self.repository.get(task_id); updated = self.service.set_completed(task_id, completed)
        if self._selected and self._selected.id == task_id:
            self._selected = updated; self.detailChanged.emit()
        self.undo_service.offer("Task completed" if completed else "Task restored",
                                lambda: (self.service.set_completed(task_id, old.completed), self.refresh()))
        self._tell(("Task completed" if completed else "Task restored") + " — Undo"); self.refresh()

    @Slot(str)
    def deleteTask(self, task_id):
        old = self.repository.delete(task_id)
        self.undo_service.offer("Task deleted", lambda: (self.repository.restore_record(old), self.refresh()))
        self.closeDetail(); self._tell("Task deleted — Undo"); self.refresh()

    @Slot()
    def undo(self):
        if self.undo_service.undo(): self._tell("Action undone")

    @Slot(str)
    def openDetail(self, task_id): self._selected = self.repository.get(task_id); self.detailChanged.emit()
    @Slot()
    def closeDetail(self): self._selected = None; self.detailChanged.emit()

    @Slot(str, str, str, str, str)
    def saveDetail(self, title, notes, scheduled, due, assigned):
        if not self._selected: return
        parse = lambda value: date.fromisoformat(value) if value.strip() else None
        try:
            saved, warning = self.service.edit(self._selected.id, title=title, notes=notes,
                scheduled_date=parse(scheduled), due_date=parse(due), assigned_month=assigned.strip() or None)
        except ValueError as exc: self._tell(f"Invalid date or title: {exc}"); return
        self._selected = saved; self.detailChanged.emit(); self._tell(warning or "Task saved"); self.refresh()

    @Slot()
    def refresh(self):
        tasks, day = self.repository.all(), date.today()
        if self._view == "inbox": result = task_queries.inbox(tasks)
        elif self._view == "today": result = task_queries.overdue(tasks, day) + task_queries.today(tasks, day) + task_queries.due_soon(tasks, day)
        elif self._view == "month": result = task_queries.month(tasks, self._month)
        elif self._view == "completed": result = task_queries.completed(tasks)
        elif self._view == "search": result = task_queries.search(tasks, self._query)
        else: result = []
        self.model.reset_tasks(list({task.id: task for task in result}.values()))

    @Slot()
    def exportBackup(self):
        name, _ = QFileDialog.getSaveFileName(None, "Export PourTask backup", "PourTask-backup.db", "SQLite database (*.db)")
        if not name: return
        try: self.backups.export(name); self._tell("Backup exported")
        except (BackupError, OSError) as exc: self._tell(f"Backup export failed: {exc}")

    @Slot()
    def importBackup(self):
        name, _ = QFileDialog.getOpenFileName(None, "Replace current data from backup", "", "SQLite database (*.db)")
        if not name: return
        try: self.backups.replace(name); self.closeDetail(); self.refresh(); self._tell("Backup imported; previous data was backed up")
        except (BackupError, OSError) as exc: self._tell(f"Backup import failed: {exc}")
