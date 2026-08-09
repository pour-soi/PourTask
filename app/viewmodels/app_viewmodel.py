from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date

from PySide6.QtCore import QAbstractListModel, QByteArray, QModelIndex, Property, Qt, Signal, Slot

from app.database import TaskRepository
from app.models import Task
from app.services import (
    DateParseError,
    TaskService,
    format_assigned_month,
    format_us_date,
    parse_assigned_month,
    parse_us_date,
)
from app.services import task_queries
from app.services.undo_service import UndoService
from app.services.backup_service import BackupService, BackupError
from PySide6.QtWidgets import QFileDialog


@dataclass
class EditDraft:
    task_id: str | None
    creating: bool
    title: str
    notes: str
    scheduled: str
    due: str
    assigned: str
    assigned_manual: bool
    original: tuple[str, str, str, str, str]
    save_state: str = "idle"

    @property
    def dirty(self) -> bool:
        return (self.title, self.notes, self.scheduled, self.due, self.assigned) != self.original


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
            return format_us_date(task.scheduled_date or task.due_date)
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
    draftChanged = Signal()
    unsavedChangesRequested = Signal()
    exitApproved = Signal()

    def __init__(self, repository: TaskRepository):
        super().__init__()
        self.repository = repository
        self.service = TaskService(repository)
        self.undo_service = UndoService()
        self.backups = BackupService(repository.database, repository.database.path.parent.parent / "backups")
        self.model = TaskListModel()
        self.today_model = TaskListModel()
        self._view, self._month, self._query, self._message = "today", date.today().strftime("%Y-%m"), "", ""
        self._view_before_search = "today"
        self._selected: Task | None = None
        self._creating = False
        self._selection_before_create: Task | None = None
        self._new_defaults: dict[str, object] = {}
        self._draft: EditDraft | None = None
        self._pending_action: tuple[str, str | None] | None = None
        self._update_save_failed = False
        self.refresh()

    @Property("QVariant", constant=True)
    def tasks(self): return self.model
    @Property("QVariant", constant=True)
    def todayTasks(self): return self.today_model
    @Property(str, notify=viewChanged)
    def currentView(self): return self._view
    @Property(str, notify=monthChanged)
    def selectedMonth(self): return self._month
    @Property(str, notify=messageChanged)
    def message(self): return self._message
    @Property(bool, notify=detailChanged)
    def detailOpen(self): return self._selected is not None
    @Property(bool, notify=detailChanged)
    def isCreating(self): return self._creating
    @Property("QVariantMap", notify=detailChanged)
    def newTaskDefaults(self): return self._new_defaults
    @Property("QVariantMap", notify=detailChanged)
    def selectedTask(self):
        task = self._selected
        return {} if not task else {"id": task.id, "title": task.title, "notes": task.notes,
            "scheduledDate": format_us_date(task.scheduled_date),
            "dueDate": format_us_date(task.due_date),
            "assignedMonth": format_assigned_month(task.assigned_month), "completed": task.completed}
    @Property("QVariantMap", notify=draftChanged)
    def draft(self):
        value = self._draft
        return {} if value is None else {
            "taskId": value.task_id or "", "creating": value.creating,
            "title": value.title, "notes": value.notes,
            "scheduledDate": value.scheduled, "dueDate": value.due,
            "assignedMonth": value.assigned, "assignedMonthManual": value.assigned_manual,
            "dirty": value.dirty, "saveState": value.save_state,
        }
    @Property(bool, notify=draftChanged)
    def hasUnsavedChanges(self): return bool(self._draft and self._draft.dirty)
    @Property(bool, notify=unsavedChangesRequested)
    def unsavedPromptVisible(self): return self._pending_action is not None
    @Property(str, notify=unsavedChangesRequested)
    def unsavedPromptContext(self):
        if not self._pending_action: return ""
        return "new task" if self._draft and self._draft.creating else "task"

    def _tell(self, message): self._message = message; self.messageChanged.emit()

    @staticmethod
    def _draft_for_task(task: Task) -> EditDraft:
        fields = (task.title, task.notes, format_us_date(task.scheduled_date),
                  format_us_date(task.due_date), format_assigned_month(task.assigned_month))
        return EditDraft(task.id, False, *fields, True, fields)

    def _request_or_run(self, action: tuple[str, str | None]) -> bool:
        if self.hasUnsavedChanges:
            if self._pending_action is None:
                self._pending_action = action
                self.unsavedChangesRequested.emit()
            return False
        self._run_action(action)
        return True

    def _run_action(self, action: tuple[str, str | None]) -> None:
        kind, value = action
        if kind == "view": self._set_view(value or "today")
        elif kind == "search": self._set_search(value or "")
        elif kind == "detail": self._open_detail(value or "")
        elif kind == "close": self._close_detail()
        elif kind == "new": self._begin_new_task()
        elif kind == "exit": self.exitApproved.emit()

    def _set_view(self, view):
        self._view, self._query = view, ""
        self._creating = False; self._selected = None; self._draft = None
        self.detailChanged.emit(); self.draftChanged.emit(); self.viewChanged.emit(); self.refresh()

    @Slot(str, result=bool)
    def setView(self, view):
        return self._request_or_run(("view", view))

    def _set_search(self, query):
        if self._view != "search": self._view_before_search = self._view
        self._creating = False; self._selected = None; self._draft = None
        self._query = query; self._view = "search"
        self.detailChanged.emit(); self.draftChanged.emit(); self.viewChanged.emit(); self.refresh()

    @Slot(str, result=bool)
    def setSearch(self, query):
        return self._request_or_run(("search", query))

    @Slot(result=bool)
    def clearSearch(self): return self.setView(self._view_before_search)

    @Slot(int)
    def changeMonth(self, offset):
        year, month = map(int, self._month.split("-")); month += offset
        year += (month - 1) // 12; month = (month - 1) % 12 + 1
        self._month = f"{year:04d}-{month:02d}"; self.monthChanged.emit(); self.refresh()

    @Slot()
    def currentMonth(self): self._month = date.today().strftime("%Y-%m"); self.monthChanged.emit(); self.refresh()

    @Slot(str, result=bool)
    def addTask(self, title):
        try:
            self.service.create(title)
        except ValueError as exc:
            self._tell(str(exc)); return False
        self._tell("Task created"); self.refresh(); return True

    @Slot(str, result=bool)
    def addTodayTask(self, title):
        today = date.today()
        try:
            self.service.create(
                title,
                scheduled_date=today,
                assigned_month=today.strftime("%Y-%m"),
            )
        except ValueError as exc:
            self._tell(str(exc)); return False
        self._tell("Task created in Today."); self.refresh(); return True

    def _begin_new_task(self):
        self._selection_before_create = self._selected
        today = date.today()
        scheduled = today if self._view == "today" else None
        assigned = today.strftime("%Y-%m") if self._view == "today" else (
            self._month if self._view == "month" else None
        )
        self._new_defaults = {
            "title": "", "notes": "", "scheduledDate": format_us_date(scheduled),
            "dueDate": "", "assignedMonth": format_assigned_month(assigned),
            "assignedMonthManual": False,
        }
        self._creating = True
        self._draft = EditDraft(None, True, "", "", self._new_defaults["scheduledDate"], "",
                                self._new_defaults["assignedMonth"], False,
                                ("", "", self._new_defaults["scheduledDate"], "", self._new_defaults["assignedMonth"]))
        self.detailChanged.emit(); self.draftChanged.emit()

    @Slot(result=bool)
    def beginNewTask(self): return self._request_or_run(("new", None))

    @Slot()
    def cancelNewTask(self):
        if not self._creating:
            return
        self._creating = False
        self._selected = self._selection_before_create
        self._selection_before_create = None
        self._draft = self._draft_for_task(self._selected) if self._selected else None
        self.detailChanged.emit(); self.draftChanged.emit()

    @Slot(str, str, str, str, str, bool)
    def updateDraft(self, title, notes, scheduled, due, assigned, assigned_manual):
        if not self._draft: return
        self._update_save_failed = False
        self._draft.save_state = "idle"
        self._draft.title, self._draft.notes = title, notes
        self._draft.scheduled, self._draft.due, self._draft.assigned = scheduled, due, assigned
        self._draft.assigned_manual = assigned_manual
        self.draftChanged.emit()

    @Slot(str, result="QVariantMap")
    def resolveUnsavedChanges(self, choice):
        if self._pending_action is None: return {"ok": True}
        if choice == "cancel":
            self._pending_action = None; self.unsavedChangesRequested.emit()
            return {"ok": True}
        if choice == "save":
            result = self.saveDraft()
            if not result.get("ok"):
                self._update_save_failed = self._pending_action[0] == "update"
                return result
        elif choice == "discard":
            self._draft = None; self.draftChanged.emit()
        else:
            return {"ok": False, "errors": {}}
        action, self._pending_action = self._pending_action, None
        self.unsavedChangesRequested.emit(); self._run_action(action)
        return {"ok": True}

    @Slot()
    def requestExit(self): self._request_or_run(("exit", None))

    @Slot()
    def requestUpdateResolution(self):
        if not self.hasUnsavedChanges:
            return
        if self._pending_action is None:
            self._pending_action = ("update", None)
        self.unsavedChangesRequested.emit()

    def updateShutdownState(self):
        if self._update_save_failed: return "save-failed"
        return "dirty" if self.hasUnsavedChanges else "ready"

    @Slot(str, result="QVariantMap")
    def normalizeDate(self, value):
        try:
            parsed = parse_us_date(value)
        except DateParseError:
            return {"valid": False, "display": value.strip(), "iso": ""}
        return {"valid": True, "display": format_us_date(parsed), "iso": parsed.isoformat() if parsed else ""}

    @Slot(str, result="QVariantMap")
    def normalizeMonth(self, value):
        try:
            parsed = parse_assigned_month(value)
        except DateParseError:
            return {"valid": False, "display": value.strip(), "iso": ""}
        return {"valid": True, "display": format_assigned_month(parsed), "iso": parsed or ""}

    @staticmethod
    def _validated_fields(title, scheduled, due, assigned):
        errors = {}
        if not title.strip():
            errors["title"] = "Enter a task title."
        values = {}
        for key, raw, message in (
            ("scheduled", scheduled, "Enter a valid date, for example 07/23/2026."),
            ("due", due, "Enter a valid date, for example 08/01/2026."),
        ):
            try:
                values[key] = parse_us_date(raw)
            except DateParseError:
                errors[key] = message
        try:
            values["assigned"] = parse_assigned_month(assigned)
        except DateParseError:
            errors["assigned"] = "Enter a valid month, for example 07/2026."
        if not errors and values["scheduled"] and values["due"] and values["scheduled"] > values["due"]:
            errors["scheduled"] = "Schedule Date must not be later than Due Date."
        return values, errors

    def _task_in_current_view(self, task: Task, day: date) -> bool:
        if self._view == "inbox":
            return task in task_queries.inbox([task])
        if self._view == "today":
            return bool(task_queries.overdue([task], day) + task_queries.today([task], day)
                        + task_queries.due_soon([task], day))
        if self._view == "month":
            return task in task_queries.month([task], self._month)
        return False

    def _follow_task(self, task: Task) -> str:
        day = date.today()
        if not self._task_in_current_view(task, day):
            if task_queries.today([task], day) or task_queries.overdue([task], day) or task_queries.due_soon([task], day):
                self._view = "today"
            elif task_queries.inbox([task]):
                self._view = "inbox"
            else:
                self._view = "month"
                self._month = (
                    task.scheduled_date.strftime("%Y-%m") if task.scheduled_date else
                    task.due_date.strftime("%Y-%m") if task.due_date else
                    task.assigned_month or day.strftime("%Y-%m")
                )
                self.monthChanged.emit()
            self.viewChanged.emit()
        if self._view == "month":
            return f"{date.fromisoformat(self._month + '-01'):%B %Y}"
        return self._view.capitalize()

    @Slot(str, str, str, str, str, result="QVariantMap")
    def createTask(self, title, notes, scheduled, due, assigned):
        values, errors = self._validated_fields(title, scheduled, due, assigned)
        if errors:
            self._tell("Check the highlighted fields.")
            return {"ok": False, "errors": errors}
        try:
            task = self.service.create(
                title, notes=notes, scheduled_date=values["scheduled"],
                due_date=values["due"], assigned_month=values["assigned"],
            )
        except ValueError:
            self._tell("Check the highlighted fields.")
            return {"ok": False, "errors": {"scheduled": "Scheduled date must not be later than the due date."}}
        self._creating = False
        self._selection_before_create = None
        self._selected = task
        fields = (task.title, task.notes, format_us_date(task.scheduled_date),
                  format_us_date(task.due_date), format_assigned_month(task.assigned_month))
        self._draft = EditDraft(task.id, False, *fields, True, fields)
        destination = self._follow_task(task)
        self.refresh()
        self.detailChanged.emit(); self.draftChanged.emit()
        self._tell(f"Task created in {destination}.")
        return {"ok": True, "taskId": task.id, "destination": destination}

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
        self._close_detail(); self._tell("Task deleted — Undo"); self.refresh()

    @Slot()
    def undo(self):
        if self.undo_service.undo(): self._tell("Action undone")

    @Slot()
    def clearMessage(self):
        if self._message:
            self._tell("")

    def _open_detail(self, task_id):
        self._selected = self.repository.get(task_id); self._creating = False
        self._draft = self._draft_for_task(self._selected)
        self.detailChanged.emit(); self.draftChanged.emit()

    @Slot(str, result=bool)
    def openDetail(self, task_id):
        if self._draft and self._draft.task_id == task_id and not self._draft.creating: return True
        return self._request_or_run(("detail", task_id))

    def _close_detail(self):
        self._selected = None; self._creating = False; self._draft = None
        self.detailChanged.emit(); self.draftChanged.emit()

    @Slot(result=bool)
    def closeDetail(self): return self._request_or_run(("close", None))

    @Slot(str, str, str, str, str, result="QVariantMap")
    def saveDetail(self, title, notes, scheduled, due, assigned):
        if not self._selected:
            return {"ok": False, "errors": {}}
        values, errors = self._validated_fields(title, scheduled, due, assigned)
        if errors:
            self._tell("Check the highlighted fields.")
            return {"ok": False, "errors": errors}
        saved, warning = self.service.edit(
            self._selected.id, title=title, notes=notes,
            scheduled_date=values["scheduled"], due_date=values["due"],
            assigned_month=values["assigned"],
        )
        self._selected = saved
        self._draft = self._draft_for_task(saved)
        destination = self._follow_task(saved)
        self.detailChanged.emit(); self.draftChanged.emit()
        self._tell(warning or f"Task saved in {destination}.")
        self.refresh()
        return {"ok": True, "taskId": saved.id, "destination": destination}

    @Slot(result="QVariantMap")
    def saveDraft(self):
        draft = self._draft
        if not draft: return {"ok": True}
        draft.save_state = "saving"; self.draftChanged.emit()
        result = (self.createTask(draft.title, draft.notes, draft.scheduled, draft.due, draft.assigned)
                  if draft.creating else
                  self.saveDetail(draft.title, draft.notes, draft.scheduled, draft.due, draft.assigned))
        if not result.get("ok") and self._draft:
            self._draft.save_state = "failed"; self.draftChanged.emit()
        return result

    @Slot()
    def refresh(self):
        tasks, day = self.repository.all(), date.today()
        today_result = (
            task_queries.overdue(tasks, day)
            + task_queries.today(tasks, day)
            + task_queries.due_soon(tasks, day)
        )
        self.today_model.reset_tasks(list({task.id: task for task in today_result}.values()))
        if self._view == "inbox": result = task_queries.inbox(tasks)
        elif self._view == "today": result = today_result
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
