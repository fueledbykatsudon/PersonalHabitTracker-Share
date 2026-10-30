"""DAO for durable one-per-day delivery records for scheduled habit reminders."""

from __future__ import annotations

import logging
from datetime import date
from typing import Any

from core.exceptions import DatabaseError
from database.database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class ReminderNotificationRepositoryError(DatabaseError):
    """Raised when reminder delivery history cannot be stored."""


class ReminderNotificationRepository:
    """Persist fired reminders so an app restart cannot re-fire the same schedule."""

    def __init__(self, database_manager=None):
        self.database_manager = database_manager or DatabaseManager()

    def record_due_reminders(
        self,
        user_id: int,
        reminders: list[dict[str, Any]],
        reminder_date: str | date,
        reminder_time: str,
    ) -> list[dict[str, Any]]:
        """Insert reminder events and return only reminders newly recorded.

        The unique key on (habit_id, reminder_date, reminder_time) makes this
        safe to call repeatedly during the scheduler's polling interval.
        """
        connection = None
        cursor = None
        recorded: list[dict[str, Any]] = []
        try:
            connection = self.database_manager.connect()
            cursor = connection.cursor()
            for reminder in reminders:
                habit_id = int(reminder["habit_id"])
                cursor.execute(
                    """INSERT IGNORE INTO reminder_notifications
                           (user_id, habit_id, reminder_date, reminder_time)
                       SELECT %s, h.habit_id, %s, %s
                       FROM habits AS h
                       WHERE h.habit_id = %s AND h.user_id = %s
                         AND h.reminder_enabled = 1
                         AND TIME_FORMAT(h.reminder_time, '%H:%i') = %s""",
                    (user_id, reminder_date, reminder_time, habit_id, user_id, reminder_time),
                )
                if int(getattr(cursor, "rowcount", 0) or 0) > 0:
                    recorded.append(dict(reminder))
            connection.commit()
            return recorded
        except Exception as exc:
            try:
                if connection is not None:
                    connection.rollback()
            except Exception:
                logger.debug("Could not roll back reminder history transaction", exc_info=True)
            logger.exception("Failed to record reminder history for user_id=%s", user_id)
            raise ReminderNotificationRepositoryError(
                "Unable to record scheduled reminder history. The reminder was not shown."
            ) from exc
        finally:
            if cursor is not None:
                try:
                    cursor.close()
                except Exception:
                    logger.debug("Could not close reminder-history cursor", exc_info=True)
