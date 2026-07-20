from pathlib import Path

import pytest

from app.services.backup_service import BackupError, BackupService


def test_export_and_replace_create_safety_backup(database, repository, tmp_path: Path):
    repository.create("Before")
    backups = BackupService(database, tmp_path / "backups")
    exported = backups.export(tmp_path / "export.db")
    repository.create("After")
    safety = backups.replace(exported)
    assert safety.exists()
    assert [task.title for task in repository.all()] == ["Before"]


def test_invalid_import_does_not_replace_database(database, repository, tmp_path: Path):
    repository.create("Safe")
    invalid = tmp_path / "invalid.db"
    invalid.write_text("not sqlite", encoding="utf-8")
    with pytest.raises(BackupError):
        BackupService(database, tmp_path / "backups").replace(invalid)
    assert repository.all()[0].title == "Safe"
