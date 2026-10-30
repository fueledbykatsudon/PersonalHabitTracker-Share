"""Database operations for daily habit completion and progress reports."""

from __future__ import annotations

from typing import Any
from datetime import date
import logging

from core.exceptions import DatabaseError
from models.habit_completion import HabitCompletion
from repositories.audit_log_repository import AuditLogRepository

logger = logging.getLogger(__name__)


class ProgressRepositoryError(DatabaseError):
    """Raised when tracking or report data cannot be accessed or changed."""


class ProgressRepository:
    """Parameterised MySQL operations, restricted to the authenticated user."""

    def __init__(self, database_manager=None):
        if database_manager is None:
            from database.database_manager import DatabaseManager
            database_manager = DatabaseManager()
        self.database_manager = database_manager

    def list_today(self, user_id: int) -> list[dict[str, Any]]:
        connection = None
        cursor = None
        try:
            connection = self.database_manager.connect()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """SELECT h.habit_id, h.habit_name,
                          COALESCE(c.category_name, h.category, 'Uncategorized') AS category,
                          COALESCE(today.completed, 0) AS completed
                   FROM habits AS h
                   LEFT JOIN habit_categories AS c ON c.category_id = h.category_id
                   LEFT JOIN (
                       SELECT habit_id, MAX(completed) AS completed
                       FROM habit_completions
                       WHERE completion_date = CURDATE()
                       GROUP BY habit_id
                   ) AS today ON today.habit_id = h.habit_id
                   WHERE h.user_id = %s
                   ORDER BY h.created_at DESC, h.habit_id DESC""",
                (user_id,),
            )
            rows = cursor.fetchall()
            return [
                {**row, "completed": bool(row.get("completed"))}
                for row in rows
            ]
        except Exception as exc:
            logger.exception("Failed to load daily tracking for user_id=%s", user_id)
            raise ProgressRepositoryError(
                "Unable to load today's habit tracking records."
            ) from exc
        finally:
            self._close_cursor(cursor)

    def set_status(self, user_id: int, habit_id: int, completed: bool) -> None:
        """Set today's status, creating or updating its single daily record."""
        connection = None
        cursor = None
        completion = HabitCompletion(habit_id=habit_id, completion_date=date.today(), completed=completed)
        desired_status = 1 if completion.completed else 0
        action = "MARK_COMPLETED" if completion.completed else "RESET_COMPLETION"
        status_label = "completed" if completion.completed else "not completed"
        try:
            connection = self.database_manager.connect()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                "SELECT habit_name FROM habits WHERE habit_id = %s AND user_id = %s LIMIT 1",
                (habit_id, user_id),
            )
            habit = cursor.fetchone()
            if habit is None:
                raise ProgressRepositoryError(
                    "That habit was not found in your account. Refresh the list and try again."
                )

            cursor.execute(
                """SELECT completion_id FROM habit_completions
                   WHERE habit_id = %s AND completion_date = CURDATE()
                   ORDER BY completion_id LIMIT 1""",
                (habit_id,),
            )
            existing = cursor.fetchone()
            if existing:
                # Update all matching same-day rows to heal any duplicate legacy rows.
                cursor.execute(
                    """UPDATE habit_completions SET completed = %s
                       WHERE habit_id = %s AND completion_date = CURDATE()""",
                    (desired_status, habit_id),
                )
            else:
                cursor.execute(
                    """INSERT INTO habit_completions
                           (habit_id, completion_date, completed)
                       VALUES (%s, CURDATE(), %s)""",
                    (habit_id, desired_status),
                )

            AuditLogRepository.insert_with_cursor(
                cursor,
                user_id,
                action,
                f"Marked habit #{habit_id} '{habit['habit_name']}' as {status_label} for today.",
            )
            connection.commit()
        except Exception as exc:
            self._safe_rollback(connection)
            if isinstance(exc, ProgressRepositoryError):
                raise
            logger.exception("Failed to update completion for habit_id=%s user_id=%s", habit_id, user_id)
            raise ProgressRepositoryError(
                "Unable to update today's habit status. No changes were saved."
            ) from exc
        finally:
            self._close_cursor(cursor)

    def get_report(self, user_id: int) -> dict[str, Any]:
        """Return each habit's recorded results over the most recent 30 days.

        Completion rate is based on recorded habit-days, not on unrecorded days.
        This metric is labelled accordingly in the UI and exported CSV.
        """
        connection = None
        cursor = None
        try:
            connection = self.database_manager.connect()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """SELECT h.habit_id, h.habit_name,
                          COALESCE(c.category_name, h.category, 'Uncategorized') AS category,
                          COUNT(d.completion_date) AS recorded_days,
                          COALESCE(SUM(d.completed), 0) AS completed_days,
                          MAX(d.completion_date) AS last_tracked
                   FROM habits AS h
                   LEFT JOIN habit_categories AS c ON c.category_id = h.category_id
                   LEFT JOIN (
                       SELECT habit_id, completion_date, MAX(completed) AS completed
                       FROM habit_completions
                       WHERE completion_date >= DATE_SUB(CURDATE(), INTERVAL 29 DAY)
                       GROUP BY habit_id, completion_date
                   ) AS d ON d.habit_id = h.habit_id
                   WHERE h.user_id = %s
                   GROUP BY h.habit_id, h.habit_name, c.category_name, h.category
                   ORDER BY h.habit_name ASC, h.habit_id ASC""",
                (user_id,),
            )
            rows = cursor.fetchall()
            normalized_rows = []
            for row in rows:
                normalized_rows.append({
                    "habit_id": int(row["habit_id"]),
                    "habit_name": row["habit_name"],
                    "category": row.get("category") or "",
                    "recorded_days": int(row.get("recorded_days") or 0),
                    "completed_days": int(row.get("completed_days") or 0),
                    "last_tracked": row.get("last_tracked"),
                })
            total_recorded = sum(row["recorded_days"] for row in normalized_rows)
            total_completed = sum(row["completed_days"] for row in normalized_rows)
            rate = round(total_completed * 100 / total_recorded) if total_recorded else 0
            return {
                "total_habits": len(normalized_rows),
                "recorded_days": total_recorded,
                "completed_days": total_completed,
                "completion_rate": rate,
                "rows": normalized_rows,
            }
        except Exception as exc:
            logger.exception("Failed to generate progress report for user_id=%s", user_id)
            raise ProgressRepositoryError(
                "Unable to generate your habit progress report."
            ) from exc
        finally:
            self._close_cursor(cursor)

    @staticmethod
    def _close_cursor(cursor) -> None:
        if cursor is not None:
            try:
                cursor.close()
            except Exception:
                # Avoid masking the more useful error from the operation itself.
                pass

    @staticmethod
    def _safe_rollback(connection) -> None:
        try:
            if connection is not None:
                connection.rollback()
        except Exception:
            pass
