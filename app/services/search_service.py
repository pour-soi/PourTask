from app.models import Task
from .task_queries import search


class SearchService:
    @staticmethod
    def find(tasks: list[Task], query: str) -> list[Task]:
        return search(tasks, query)
