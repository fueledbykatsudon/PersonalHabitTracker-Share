"""Controller layer for daily tracking and report workflows."""

from repositories.progress_repository import ProgressRepository, ProgressRepositoryError


class ProgressController:
    def __init__(self, repository=None):
        self.repository = repository or ProgressRepository()

    def list_today(self, user_id: int):
        return self.repository.list_today(user_id)

    def set_status(self, user_id: int, habit_id: int, completed: bool):
        return self.repository.set_status(user_id, habit_id, completed)

    def get_report(self, user_id: int):
        return self.repository.get_report(user_id)


__all__ = ["ProgressController", "ProgressRepositoryError"]
