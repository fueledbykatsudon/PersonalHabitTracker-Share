"""MySQL repository for habit records and habit-related audit events."""

from __future__ import annotations

from typing import Any
import logging

from core.exceptions import DatabaseError
from models.habit import Habit
from repositories.audit_log_repository import AuditLogRepository
from validators.habit_validator import HabitValidationError, validate_reminder_settings

logger = logging.getLogger(__name__)


class HabitRepositoryError(DatabaseError):
    """Raised when a habit database operation cannot be completed."""


class HabitRepository:
    """Parameterized MySQL CRUD operations scoped to the owning user."""

    def __init__(self, database_manager=None):
        if database_manager is None:
            from database.database_manager import DatabaseManager
            database_manager = DatabaseManager()
        self.database_manager = database_manager

    def list_for_user(self, user_id: int, search: str = "") -> list[dict[str, Any]]:
        connection = None
        cursor = None
        try:
            connection = self.database_manager.connect()
            cursor = connection.cursor(dictionary=True)
            clean_search = (search or "").strip()
            if clean_search:
                pattern = f"%{clean_search}%"
                cursor.execute(
                    """SELECT h.habit_id, h.habit_name,
                              COALESCE(c.category_name, h.category, 'Uncategorized') AS category,
                              h.description, h.target_frequency,
                              TIME_FORMAT(h.reminder_time, '%H:%i') AS reminder_time,
                              COALESCE(h.reminder_enabled, 0) AS reminder_enabled, h.created_at
                       FROM habits AS h
                       LEFT JOIN habit_categories AS c ON c.category_id = h.category_id
                       WHERE h.user_id = %s
                         AND (h.habit_name LIKE %s
                              OR COALESCE(c.category_name, h.category, '') LIKE %s
                              OR COALESCE(h.description, '') LIKE %s
                              OR COALESCE(h.target_frequency, '') LIKE %s)
                       ORDER BY h.created_at DESC, h.habit_id DESC""",
                    (user_id, pattern, pattern, pattern, pattern),
                )
            else:
                cursor.execute(
                    """SELECT h.habit_id, h.habit_name,
                              COALESCE(c.category_name, h.category, 'Uncategorized') AS category,
                              h.description, h.target_frequency,
                              TIME_FORMAT(h.reminder_time, '%H:%i') AS reminder_time,
                              COALESCE(h.reminder_enabled, 0) AS reminder_enabled, h.created_at
                       FROM habits AS h
                       LEFT JOIN habit_categories AS c ON c.category_id = h.category_id
                       WHERE h.user_id = %s
                       ORDER BY h.created_at DESC, h.habit_id DESC""",
                    (user_id,),
                )
            return cursor.fetchall()
        except Exception as exc:
            logger.exception("Failed to list habits for user_id=%s", user_id)
            raise HabitRepositoryError("Unable to load habits from the database.") from exc
        finally:
            if cursor is not None:
                cursor.close()

    def get_summary(self, user_id: int) -> dict[str, int]:
        connection = None
        cursor = None
        try:
            connection = self.database_manager.connect()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """SELECT
                       COUNT(DISTINCT h.habit_id) AS active_habits,
                       COUNT(DISTINCT CASE
                           WHEN hc.completion_date = CURDATE() AND hc.completed = 1
                           THEN h.habit_id END) AS completed_today
                   FROM habits AS h
                   LEFT JOIN habit_completions AS hc ON hc.habit_id = h.habit_id
                   WHERE h.user_id = %s""",
                (user_id,),
            )
            result = cursor.fetchone() or {}
            return {
                "active_habits": int(result.get("active_habits") or 0),
                "completed_today": int(result.get("completed_today") or 0),
            }
        except Exception as exc:
            logger.exception("Failed to load habit statistics for user_id=%s", user_id)
            raise HabitRepositoryError("Unable to load habit statistics from the database.") from exc
        finally:
            if cursor is not None:
                cursor.close()

    @staticmethod
    def _ensure_category(cursor, category_name: str) -> int:
        """Get or create the normalized category row, returning its primary key."""
        cursor.execute(
            """INSERT INTO habit_categories (category_name, is_default)
               VALUES (%s, 0)
               ON DUPLICATE KEY UPDATE category_id = LAST_INSERT_ID(category_id)""",
            (category_name,),
        )
        raw_category_id = getattr(cursor, "lastrowid", 0)
        try:
            category_id = int(raw_category_id or 0)
        except (TypeError, ValueError):
            category_id = 0
        if category_id > 0:
            return category_id
        cursor.execute(
            "SELECT category_id FROM habit_categories WHERE category_name = %s LIMIT 1",
            (category_name,),
        )
        row = cursor.fetchone()
        if not row:
            raise HabitRepositoryError("The selected habit category could not be saved.")
        value = row.get("category_id") if isinstance(row, dict) else row[0]
        return int(value)

    def create(
        self,
        user_id: int,
        habit_name: str,
        category: str,
        description: str,
        target_frequency: str,
        reminder_time: str | None = None,
        reminder_enabled: bool = False,
    ) -> int:
        habit = Habit(user_id, habit_name, category, description, target_frequency)
        reminder = validate_reminder_settings(reminder_time, reminder_enabled)
        data = habit.to_record()
        connection = None
        cursor = None
        try:
            connection = self.database_manager.connect()
            cursor = connection.cursor()
            category_id = self._ensure_category(cursor, data["category"])
            cursor.execute(
                """INSERT INTO habits
                       (user_id, habit_name, category_id, category, description, target_frequency,
                        reminder_time, reminder_enabled)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (user_id, data["habit_name"], category_id, data["category"], data["description"],
                 data["target_frequency"], reminder["reminder_time"], int(reminder["reminder_enabled"])),
            )
            habit_id = int(cursor.lastrowid)
            self._insert_audit(
                cursor,
                user_id,
                "CREATE_HABIT",
                f"Created habit #{habit_id}: {data['habit_name']}",
            )
            connection.commit()
            return habit_id
        except Exception as exc:
            self._safe_rollback(connection)
            if isinstance(exc, HabitValidationError):
                raise
            logger.exception("Failed to create habit for user_id=%s", user_id)
            raise HabitRepositoryError("Unable to create the habit. No changes were saved.") from exc
        finally:
            if cursor is not None:
                cursor.close()

    def update(
        self,
        user_id: int,
        habit_id: int,
        habit_name: str,
        category: str,
        description: str,
        target_frequency: str,
        reminder_time: str | None = None,
        reminder_enabled: bool = False,
    ) -> None:
        habit = Habit(user_id, habit_name, category, description, target_frequency, habit_id=habit_id)
        reminder = validate_reminder_settings(reminder_time, reminder_enabled)
        data = habit.to_record()
        connection = None
        cursor = None
        try:
            connection = self.database_manager.connect()
            cursor = connection.cursor()
            cursor.execute(
                "SELECT habit_name FROM habits WHERE habit_id = %s AND user_id = %s",
                (habit_id, user_id),
            )
            current = cursor.fetchone()
            if current is None:
                raise HabitRepositoryError("That habit was not found in your account.")

            category_id = self._ensure_category(cursor, data["category"])
            cursor.execute(
                """UPDATE habits
                   SET habit_name = %s, category_id = %s, category = %s,
                       description = %s, target_frequency = %s,
                       reminder_time = %s, reminder_enabled = %s
                   WHERE habit_id = %s AND user_id = %s""",
                (data["habit_name"], category_id, data["category"], data["description"],
                 data["target_frequency"], reminder["reminder_time"],
                 int(reminder["reminder_enabled"]), habit_id, user_id),
            )
            self._insert_audit(
                cursor,
                user_id,
                "UPDATE_HABIT",
                f"Updated habit #{habit_id}: {data['habit_name']}",
            )
            connection.commit()
        except Exception as exc:
            self._safe_rollback(connection)
            if isinstance(exc, HabitRepositoryError):
                raise
            logger.exception("Failed to update habit_id=%s for user_id=%s", habit_id, user_id)
            raise HabitRepositoryError("Unable to update the habit. No changes were saved.") from exc
        finally:
            if cursor is not None:
                cursor.close()

    def list_enabled_reminders(self, user_id: int) -> list[dict[str, Any]]:
        """Return the signed-in user's enabled reminders in local-time text format."""
        connection = None
        cursor = None
        try:
            connection = self.database_manager.connect()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """SELECT habit_id, habit_name,
                          TIME_FORMAT(reminder_time, '%H:%i') AS reminder_time
                   FROM habits
                   WHERE user_id = %s AND reminder_enabled = 1 AND reminder_time IS NOT NULL
                   ORDER BY habit_name ASC, habit_id ASC""",
                (user_id,),
            )
            return cursor.fetchall()
        except Exception as exc:
            logger.exception("Failed to load reminders for user_id=%s", user_id)
            raise HabitRepositoryError("Unable to check scheduled habit reminders.") from exc
        finally:
            if cursor is not None:
                cursor.close()

    def delete(self, user_id: int, habit_id: int) -> None:
        connection = None
        cursor = None
        try:
            connection = self.database_manager.connect()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                "SELECT habit_name FROM habits WHERE habit_id = %s AND user_id = %s",
                (habit_id, user_id),
            )
            habit = cursor.fetchone()
            if habit is None:
                raise HabitRepositoryError("That habit was not found in your account.")

            # The current schema does not declare ON DELETE CASCADE. Remove the
            # dependent completion rows first so the foreign key remains valid.
            cursor.execute("DELETE FROM habit_completions WHERE habit_id = %s", (habit_id,))
            cursor.execute("DELETE FROM habits WHERE habit_id = %s AND user_id = %s", (habit_id, user_id))
            self._insert_audit(
                cursor,
                user_id,
                "DELETE_HABIT",
                f"Deleted habit #{habit_id}.",
            )
            connection.commit()
        except Exception as exc:
            self._safe_rollback(connection)
            if isinstance(exc, HabitRepositoryError):
                raise
            logger.exception("Failed to delete habit_id=%s for user_id=%s", habit_id, user_id)
            raise HabitRepositoryError("Unable to delete the habit. No changes were saved.") from exc
        finally:
            if cursor is not None:
                cursor.close()

    @staticmethod
    def _insert_audit(cursor, user_id: int, action: str, description: str) -> None:
        AuditLogRepository.insert_with_cursor(cursor, user_id, action, description)

    @staticmethod
    def _safe_rollback(connection) -> None:
        try:
            if connection is not None:
                connection.rollback()
        except Exception:
            # Preserve the original operation error; the UI will receive a safe message.
            pass
