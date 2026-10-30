"""Controller layer for habit workflows between Tkinter views and repositories."""

from repositories.habit_repository import HabitRepository, HabitRepositoryError
from repositories.reminder_notification_repository import ReminderNotificationRepository


class HabitController:
    def __init__(self, repository=None, reminder_notification_repository=None):
        self.repository = repository or HabitRepository()
        self.reminder_notification_repository = (
            reminder_notification_repository or ReminderNotificationRepository()
        )

    def list_for_user(self, user_id: int, search: str = ""):
        return self.repository.list_for_user(user_id, search)

    def get_summary(self, user_id: int):
        return self.repository.get_summary(user_id)

    def create(
        self, user_id: int, habit_name: str, category: str, description: str,
        target_frequency: str, reminder_time: str | None = None, reminder_enabled: bool = False,
    ):
        return self.repository.create(
            user_id, habit_name, category, description, target_frequency,
            reminder_time, reminder_enabled,
        )

    def update(
        self, user_id: int, habit_id: int, habit_name: str, category: str,
        description: str, target_frequency: str, reminder_time: str | None = None,
        reminder_enabled: bool = False,
    ):
        return self.repository.update(
            user_id, habit_id, habit_name, category, description, target_frequency,
            reminder_time, reminder_enabled,
        )

    def list_enabled_reminders(self, user_id: int):
        return self.repository.list_enabled_reminders(user_id)

    def record_due_reminders(self, user_id: int, reminders, reminder_date, reminder_time):
        return self.reminder_notification_repository.record_due_reminders(
            user_id, reminders, reminder_date, reminder_time
        )

    def delete(self, user_id: int, habit_id: int):
        return self.repository.delete(user_id, habit_id)


__all__ = ["HabitController", "HabitRepositoryError"]
