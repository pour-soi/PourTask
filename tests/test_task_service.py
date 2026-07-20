from datetime import date


def test_complete_restore_and_move_to_today(service, repository):
    created = service.create("Plan trip")
    moved = service.move_to_today(created.id, date(2026, 7, 20))
    assert moved.scheduled_date == date(2026, 7, 20)
    done = service.set_completed(created.id, True)
    assert done.completed and done.completed_at is not None
    restored = service.set_completed(created.id, False)
    assert not restored.completed and restored.completed_at is None


def test_invalid_date_edit_saves_text_but_preserves_valid_dates(service, repository):
    created = service.create("Original", scheduled_date=date(2026, 7, 20), due_date=date(2026, 7, 22))
    saved, warning = service.edit(created.id, title="Edited", notes="New notes",
                                  scheduled_date=date(2026, 7, 25), due_date=date(2026, 7, 22),
                                  assigned_month=None)
    assert warning
    assert saved.title == "Edited" and saved.notes == "New notes"
    assert saved.scheduled_date == date(2026, 7, 20)


def test_completion_is_preserved_when_completed_task_text_is_edited(service, repository):
    created = service.create("Task")
    service.set_completed(created.id, True)
    completed_at = repository.get(created.id).completed_at
    saved, warning = service.edit(created.id, title="Task changed", notes="Viewed and corrected",
                                  scheduled_date=None, due_date=None, assigned_month=None)
    assert warning is None
    assert saved.completed and saved.completed_at == completed_at
