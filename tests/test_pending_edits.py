from app.viewmodels import AppViewModel


def _dirty_new(view_model: AppViewModel, title="Draft title", notes="Draft notes"):
    view_model.beginNewTask()
    draft = view_model.draft
    view_model.updateDraft(title, notes, draft["scheduledDate"], draft["dueDate"],
                           draft["assignedMonth"], draft["assignedMonthManual"])
    assert view_model.hasUnsavedChanges


def test_new_task_navigation_cancel_preserves_authoritative_draft(repository):
    view_model = AppViewModel(repository); _dirty_new(view_model)
    assert not view_model.setView("settings")
    assert view_model.currentView == "today"
    view_model.resolveUnsavedChanges("cancel")
    assert view_model.isCreating and view_model.draft["title"] == "Draft title"
    assert repository.all() == []


def test_new_task_navigation_discard_is_explicit(repository):
    view_model = AppViewModel(repository); _dirty_new(view_model)
    view_model.setView("settings")
    assert view_model.resolveUnsavedChanges("discard")["ok"]
    assert view_model.currentView == "settings" and not view_model.isCreating
    assert repository.all() == []


def test_new_task_navigation_save_persists_before_leaving(repository):
    view_model = AppViewModel(repository); _dirty_new(view_model)
    view_model.setView("settings")
    assert view_model.resolveUnsavedChanges("save")["ok"]
    assert view_model.currentView == "settings"
    assert [task.title for task in repository.all()] == ["Draft title"]


def test_existing_task_cancel_and_discard_leave_persisted_values_unchanged(repository):
    task = repository.create("Original", notes="Original notes")
    view_model = AppViewModel(repository); view_model.openDetail(task.id)
    draft = view_model.draft
    view_model.updateDraft("Changed", "Changed notes", draft["scheduledDate"], draft["dueDate"], draft["assignedMonth"], True)
    assert not view_model.setView("settings")
    view_model.resolveUnsavedChanges("cancel")
    assert view_model.draft["title"] == "Changed"
    assert repository.get(task.id).title == "Original"
    view_model.setView("settings"); view_model.resolveUnsavedChanges("discard")
    assert repository.get(task.id).title == "Original"


def test_existing_task_save_then_navigation_persists(repository):
    task = repository.create("Original")
    view_model = AppViewModel(repository); view_model.openDetail(task.id)
    draft = view_model.draft
    view_model.updateDraft("Changed", "", draft["scheduledDate"], draft["dueDate"], draft["assignedMonth"], True)
    view_model.setView("settings")
    assert view_model.resolveUnsavedChanges("save")["ok"]
    assert repository.get(task.id).title == "Changed"


def test_task_selection_change_is_guarded(repository):
    first, second = repository.create("First"), repository.create("Second")
    view_model = AppViewModel(repository); view_model.openDetail(first.id)
    draft = view_model.draft
    view_model.updateDraft("First changed", "", draft["scheduledDate"], draft["dueDate"], draft["assignedMonth"], True)
    assert not view_model.openDetail(second.id)
    assert view_model.selectedTask["id"] == first.id
    view_model.resolveUnsavedChanges("discard")
    assert view_model.selectedTask["id"] == second.id


def test_exit_save_discard_cancel_share_dirty_guard(repository):
    view_model = AppViewModel(repository); approved = []
    view_model.exitApproved.connect(lambda: approved.append(True))
    _dirty_new(view_model); view_model.requestExit(); view_model.requestExit()
    assert view_model.unsavedPromptVisible and approved == []
    view_model.resolveUnsavedChanges("cancel")
    assert view_model.hasUnsavedChanges and approved == []
    view_model.requestExit(); view_model.resolveUnsavedChanges("discard")
    assert approved == [True]


def test_update_resolution_preserves_draft_until_explicit_choice(repository):
    view_model = AppViewModel(repository); _dirty_new(view_model)
    view_model.requestUpdateResolution(); view_model.requestUpdateResolution()
    assert view_model.unsavedPromptVisible and view_model.draft["notes"] == "Draft notes"
    view_model.resolveUnsavedChanges("cancel")
    assert view_model.hasUnsavedChanges
    view_model.requestUpdateResolution(); view_model.resolveUnsavedChanges("discard")
    assert not view_model.hasUnsavedChanges


def test_update_resolution_reannounces_an_existing_pending_exit(repository):
    view_model = AppViewModel(repository); announcements = []
    view_model.unsavedChangesRequested.connect(lambda: announcements.append(True))
    _dirty_new(view_model)
    view_model.requestExit()
    view_model.requestUpdateResolution()
    assert len(announcements) == 2
    assert view_model.unsavedPromptVisible


def test_saved_row_becomes_clean_baseline_for_shutdown_retry(repository):
    view_model = AppViewModel(repository); _dirty_new(view_model)
    row_id = view_model.saveDraft()["taskId"]
    assert not view_model.hasUnsavedChanges
    assert view_model.draft["taskId"] == row_id
    assert view_model.updateShutdownState() == "ready"
    view_model.requestUpdateResolution()
    assert not view_model.unsavedPromptVisible


def test_update_save_clears_prompt_and_allows_ready_retry(repository):
    view_model = AppViewModel(repository); _dirty_new(view_model)
    view_model.requestUpdateResolution()
    result = view_model.resolveUnsavedChanges("save")
    assert result["ok"] and not view_model.hasUnsavedChanges
    assert not view_model.unsavedPromptVisible
    assert view_model.updateShutdownState() == "ready"


def test_update_discard_allows_ready_retry_but_cancel_remains_dirty(repository):
    view_model = AppViewModel(repository); _dirty_new(view_model)
    view_model.requestUpdateResolution()
    view_model.resolveUnsavedChanges("cancel")
    assert view_model.hasUnsavedChanges and not view_model.unsavedPromptVisible
    assert view_model.updateShutdownState() == "dirty"
    view_model.requestUpdateResolution()
    view_model.resolveUnsavedChanges("discard")
    assert not view_model.hasUnsavedChanges
    assert view_model.updateShutdownState() == "ready"


def test_invalid_save_does_not_navigate_or_discard(repository):
    view_model = AppViewModel(repository); _dirty_new(view_model, title="")
    view_model.setView("settings")
    result = view_model.resolveUnsavedChanges("save")
    assert not result["ok"] and view_model.currentView == "today"
    assert view_model.unsavedPromptVisible and view_model.draft["notes"] == "Draft notes"


def test_failed_update_save_is_reported_without_task_content(repository):
    view_model = AppViewModel(repository); _dirty_new(view_model, title="")
    view_model.requestUpdateResolution()
    result = view_model.resolveUnsavedChanges("save")
    assert not result["ok"] and view_model.updateShutdownState() == "save-failed"
