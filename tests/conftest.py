from pathlib import Path
import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from app.database import Database, TaskRepository
from app.services import TaskService


@pytest.fixture
def database(tmp_path: Path):
    return Database(tmp_path / "test.db")


@pytest.fixture
def repository(database):
    return TaskRepository(database)


@pytest.fixture
def service(repository):
    return TaskService(repository)
