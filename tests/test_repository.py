from dataclasses import replace
from datetime import date

import pytest


def test_create_update_and_delete_preserve_stable_id(repository):
    created = repository.create("  Read notes  ", notes="中文 and English", due_date=date(2026, 8, 5))
    assert created.title == "Read notes"
    stored = repository.get(created.id)
    assert stored.id == created.id
    assert stored.notes == "中文 and English"
    updated = repository.update(replace(stored, title="Read all notes"))
    assert updated.id == created.id
    assert repository.delete(created.id).id == created.id
    assert repository.get(created.id) is None


def test_empty_title_is_rejected(repository):
    with pytest.raises(ValueError, match="empty"):
        repository.create("  ")


def test_database_enables_wal_foreign_keys_and_schema_version(database):
    with database.connect() as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert connection.execute("SELECT MAX(version) FROM schema_version").fetchone()[0] == 1
