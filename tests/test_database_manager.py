"""Basic Singleton behavior test for the database connection manager."""

import unittest
from unittest.mock import Mock, call

from database.database_manager import DatabaseManager


class DatabaseManagerTests(unittest.TestCase):
    def setUp(self):
        self.original_instance = DatabaseManager._instance
        DatabaseManager._instance = None

    def tearDown(self):
        instance = DatabaseManager._instance
        if instance is not None:
            instance._connection = None
            instance._extended_schema_checked = False
        DatabaseManager._instance = self.original_instance

    def test_only_one_manager_instance_is_created(self):
        first = DatabaseManager()
        second = DatabaseManager()
        self.assertIs(first, second)

    def test_missing_reminder_columns_are_added_without_replacing_existing_data(self):
        manager = DatabaseManager()
        manager._reminder_schema_checked = False
        connection = Mock()
        cursor = Mock()
        connection.cursor.return_value = cursor
        cursor.fetchall.return_value = []

        manager._ensure_reminder_schema(connection)

        statements = [call.args[0] for call in cursor.execute.call_args_list]
        self.assertIn(
            "ALTER TABLE habits ADD COLUMN reminder_time TIME NULL DEFAULT NULL",
            statements,
        )
        self.assertIn(
            "ALTER TABLE habits ADD COLUMN reminder_enabled TINYINT(1) NOT NULL DEFAULT 0",
            statements,
        )
        connection.commit.assert_called_once()
        self.assertTrue(manager._reminder_schema_checked)

    def test_existing_reminder_columns_are_not_added_again(self):
        manager = DatabaseManager()
        manager._reminder_schema_checked = False
        connection = Mock()
        cursor = Mock()
        connection.cursor.return_value = cursor
        cursor.fetchall.return_value = [("reminder_time",), ("reminder_enabled",)]

        manager._ensure_reminder_schema(connection)

        self.assertEqual(cursor.execute.call_count, 1)
        connection.commit.assert_not_called()
        self.assertTrue(manager._reminder_schema_checked)

    def test_extended_schema_creates_categories_and_reminder_history(self):
        manager = DatabaseManager()
        manager._extended_schema_checked = False
        connection = Mock()
        cursor = Mock()
        connection.cursor.return_value = cursor
        cursor.fetchall.return_value = []

        manager._ensure_extended_schema(connection)

        statements = [call.args[0] for call in cursor.execute.call_args_list]
        combined = "\n".join(statements)
        self.assertIn("CREATE TABLE IF NOT EXISTS habit_categories", combined)
        self.assertIn("ALTER TABLE habits ADD COLUMN category_id INT NULL", statements)
        self.assertIn("CREATE TABLE IF NOT EXISTS reminder_notifications", combined)
        self.assertIn("FOREIGN KEY (category_id)", combined)
        connection.commit.assert_called_once()
        self.assertTrue(manager._extended_schema_checked)

    def test_failed_reminder_schema_migration_has_actionable_error(self):
        manager = DatabaseManager()
        manager._reminder_schema_checked = False
        connection = Mock()
        cursor = Mock()
        connection.cursor.return_value = cursor
        cursor.execute.side_effect = RuntimeError("permission denied")

        with self.assertRaisesRegex(RuntimeError, "ALTER permission"):
            manager._ensure_reminder_schema(connection)
        self.assertFalse(manager._reminder_schema_checked)


if __name__ == "__main__":
    unittest.main()
