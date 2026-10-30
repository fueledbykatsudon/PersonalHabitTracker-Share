"""Singleton MySQL connection manager for XAMPP/MariaDB."""

from __future__ import annotations

import logging
import os
import re

import mysql.connector

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Provide one reusable DB connection; credentials may be overridden by environment."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            instance = super().__new__(cls)
            instance._connection = None
            instance._reminder_schema_checked = False
            instance._extended_schema_checked = False
            cls._instance = instance
        return cls._instance

    @property
    def connection(self):
        return self._connection

    @connection.setter
    def connection(self, value):
        # Encapsulate the active connection so callers use connect()/close().
        self._connection = value

    def connect(self):
        """Return a live connection, reconnecting when the previous one is closed."""
        if self._connection is None or not self._is_connected(self._connection):
            try:
                self._connection = mysql.connector.connect(
                    host=os.getenv("PHT_DB_HOST", "localhost"),
                    port=int(os.getenv("PHT_DB_PORT", "3306")),
                    user=os.getenv("PHT_DB_USER", "root"),
                    password=os.getenv("PHT_DB_PASSWORD", ""),
                    database=os.getenv("PHT_DB_NAME", "personal_habit_tracker"),
                    connection_timeout=5,
                )
                logger.info("Connected to MySQL database=%s", os.getenv("PHT_DB_NAME", "personal_habit_tracker"))
                # The daily-reminder release adds two optional columns to the
                # existing habits table. Apply only those additive changes when
                # missing so an older user database continues to load habits.
                self._ensure_reminder_schema(self._connection)
                self._ensure_extended_schema(self._connection)
            except Exception:
                logger.exception("Unable to connect to MySQL or prepare the project database schema")
                # Do not keep a half-initialized connection if the schema check
                # failed; the next attempt should retry cleanly.
                try:
                    if self._connection is not None and self._is_connected(self._connection):
                        self._connection.close()
                except Exception:
                    logger.debug("Could not close failed database connection", exc_info=True)
                self._connection = None
                self._reminder_schema_checked = False
                self._extended_schema_checked = False
                raise
        return self._connection

    def _ensure_reminder_schema(self, connection) -> None:
        """Add only the optional reminder columns if they are absent.

        This compatibility migration is intentionally narrow: it never drops or
        rewrites existing data. It is needed because otherwise the new SELECT
        queries fail on older databases with "Unknown column reminder_time".
        """
        if self._reminder_schema_checked:
            return

        cursor = None
        try:
            cursor = connection.cursor()
            cursor.execute(
                """SELECT COLUMN_NAME
                   FROM INFORMATION_SCHEMA.COLUMNS
                   WHERE TABLE_SCHEMA = DATABASE()
                     AND TABLE_NAME = %s
                     AND COLUMN_NAME IN (%s, %s)""",
                ("habits", "reminder_time", "reminder_enabled"),
            )
            existing = {str(row[0]) for row in cursor.fetchall()}
            if "reminder_time" not in existing:
                cursor.execute(
                    "ALTER TABLE habits ADD COLUMN reminder_time TIME NULL DEFAULT NULL"
                )
                logger.info("Added missing habits.reminder_time column")
            if "reminder_enabled" not in existing:
                cursor.execute(
                    "ALTER TABLE habits ADD COLUMN reminder_enabled TINYINT(1) NOT NULL DEFAULT 0"
                )
                logger.info("Added missing habits.reminder_enabled column")
            if existing != {"reminder_time", "reminder_enabled"}:
                # MariaDB commits ALTER TABLE statements implicitly, but an
                # explicit commit also keeps behavior consistent with tests and
                # compatible database configurations.
                connection.commit()
            self._reminder_schema_checked = True
        except Exception as exc:
            logger.exception("Unable to prepare the habit-reminder database columns")
            raise RuntimeError(
                "The habit-reminder database setup could not be completed. "
                "Check that the 'habits' table exists and the MySQL user has "
                "ALTER permission, then retry. Your existing habit records were not deleted."
            ) from exc
        finally:
            if cursor is not None:
                try:
                    cursor.close()
                except Exception:
                    logger.debug("Could not close schema migration cursor", exc_info=True)

    def _ensure_extended_schema(self, connection) -> None:
        """Prepare category normalization and durable reminder history.

        This migration is additive: it creates the category catalog and reminder
        delivery history, links existing habits to categories, and keeps the
        legacy text category column synchronized for compatibility with older
        project backups. It never deletes user, habit, completion, or audit rows.
        """
        if self._extended_schema_checked:
            return

        cursor = None
        try:
            cursor = connection.cursor()
            cursor.execute(
                """CREATE TABLE IF NOT EXISTS habit_categories (
                       category_id INT NOT NULL AUTO_INCREMENT,
                       category_name VARCHAR(50) NOT NULL,
                       is_default TINYINT(1) NOT NULL DEFAULT 0,
                       created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                       PRIMARY KEY (category_id),
                       UNIQUE KEY uq_habit_categories_name (category_name)
                   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"""
            )

            # Read the existing columns so this works for both original and
            # already-upgraded databases.
            cursor.execute(
                """SELECT COLUMN_NAME
                   FROM INFORMATION_SCHEMA.COLUMNS
                   WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'habits'"""
            )
            habit_columns = {str(row[0]) for row in cursor.fetchall()}

            if "category_id" not in habit_columns:
                cursor.execute("ALTER TABLE habits ADD COLUMN category_id INT NULL")
                habit_columns.add("category_id")

            # Preserve existing user-created categories before seeding defaults.
            if "category" in habit_columns:
                cursor.execute(
                    """INSERT IGNORE INTO habit_categories (category_name, is_default)
                       SELECT DISTINCT TRIM(category), 0
                       FROM habits
                       WHERE category IS NOT NULL AND TRIM(category) <> ''"""
                )

            for category_name in (
                "Health", "Productivity", "Lifestyle", "Mental Wellness",
                "Finance", "Relationships", "Uncategorized",
            ):
                cursor.execute(
                    """INSERT IGNORE INTO habit_categories (category_name, is_default)
                       VALUES (%s, %s)""",
                    (category_name, 1),
                )

            if "category" in habit_columns:
                cursor.execute(
                    """UPDATE habits AS h
                       INNER JOIN habit_categories AS c
                         ON c.category_name = TRIM(COALESCE(NULLIF(h.category, ''), 'Uncategorized'))
                       SET h.category_id = c.category_id
                       WHERE h.category_id IS NULL"""
                )
                # Keep the older text field synchronized for rollback compatibility.
                cursor.execute(
                    """UPDATE habits
                       SET category = 'Uncategorized'
                       WHERE (category IS NULL OR TRIM(category) = '')
                         AND category_id IS NOT NULL"""
                )
            cursor.execute(
                """UPDATE habits AS h
                   INNER JOIN habit_categories AS c ON c.category_name = 'Uncategorized'
                   SET h.category_id = c.category_id
                   WHERE h.category_id IS NULL"""
            )

            # Ensure the category key is indexed and protected by a foreign key.
            cursor.execute(
                """SELECT INDEX_NAME FROM INFORMATION_SCHEMA.STATISTICS
                   WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'habits'
                     AND COLUMN_NAME = 'category_id' AND SEQ_IN_INDEX = 1"""
            )
            if not cursor.fetchall():
                cursor.execute("ALTER TABLE habits ADD INDEX idx_habits_category_id (category_id)")

            cursor.execute(
                """SELECT CONSTRAINT_NAME FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
                   WHERE CONSTRAINT_SCHEMA = DATABASE() AND TABLE_NAME = 'habits'
                     AND COLUMN_NAME = 'category_id'
                     AND REFERENCED_TABLE_NAME = 'habit_categories'"""
            )
            if not cursor.fetchall():
                cursor.execute(
                    """ALTER TABLE habits
                       ADD CONSTRAINT fk_habits_category
                       FOREIGN KEY (category_id) REFERENCES habit_categories(category_id)
                       ON UPDATE CASCADE ON DELETE RESTRICT"""
                )

            # Match the referenced primary-key types exactly; some existing
            # MySQL exports use UNSIGNED integer identifiers.
            cursor.execute(
                """SELECT TABLE_NAME, COLUMN_NAME, COLUMN_TYPE
                   FROM INFORMATION_SCHEMA.COLUMNS
                   WHERE TABLE_SCHEMA = DATABASE()
                     AND ((TABLE_NAME = 'users' AND COLUMN_NAME = 'user_id')
                       OR (TABLE_NAME = 'habits' AND COLUMN_NAME = 'habit_id'))"""
            )
            key_types = {(str(row[0]), str(row[1])): str(row[2]) for row in cursor.fetchall()}
            user_key_type = key_types.get(("users", "user_id"), "INT")
            habit_key_type = key_types.get(("habits", "habit_id"), "INT")
            type_pattern = re.compile(r"^[A-Za-z]+(?:\(\d+\))?(?:\s+unsigned)?$", re.IGNORECASE)
            if not type_pattern.fullmatch(user_key_type):
                user_key_type = "INT"
            if not type_pattern.fullmatch(habit_key_type):
                habit_key_type = "INT"

            # Persistent delivery history prevents a reminder being shown again
            # after restarting the app during the same scheduled minute.
            cursor.execute(
                f"""CREATE TABLE IF NOT EXISTS reminder_notifications (
                       notification_id BIGINT NOT NULL AUTO_INCREMENT,
                       user_id {user_key_type} NOT NULL,
                       habit_id {habit_key_type} NOT NULL,
                       reminder_date DATE NOT NULL,
                       reminder_time TIME NOT NULL,
                       notified_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                       PRIMARY KEY (notification_id),
                       UNIQUE KEY uq_reminder_delivery (habit_id, reminder_date, reminder_time),
                       KEY idx_reminder_notifications_user_date (user_id, reminder_date),
                       CONSTRAINT fk_reminder_notifications_user
                         FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                       CONSTRAINT fk_reminder_notifications_habit
                         FOREIGN KEY (habit_id) REFERENCES habits(habit_id) ON DELETE CASCADE
                   ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"""
            )
            connection.commit()
            self._extended_schema_checked = True
        except Exception as exc:
            logger.exception("Unable to prepare the seven-table project schema")
            raise RuntimeError(
                "The database upgrade for habit categories and reminder history failed. "
                "Check that the roles/users/habits tables exist and that the MySQL account "
                "can create tables and alter habits. Existing records were not intentionally deleted."
            ) from exc
        finally:
            if cursor is not None:
                try:
                    cursor.close()
                except Exception:
                    logger.debug("Could not close extended-schema cursor", exc_info=True)

    def close(self):
        if self._connection is not None:
            try:
                if self._is_connected(self._connection):
                    self._connection.close()
                    logger.info("MySQL connection closed")
            except mysql.connector.Error:
                logger.exception("Failed to close MySQL connection")
                raise
            finally:
                self._connection = None
                self._reminder_schema_checked = False
                self._extended_schema_checked = False

    @staticmethod
    def _is_connected(connection) -> bool:
        try:
            return bool(connection.is_connected())
        except (AttributeError, mysql.connector.Error):
            return False
