"""Tests for idempotent reminder-delivery logging."""

import unittest
from unittest.mock import Mock

from repositories.reminder_notification_repository import ReminderNotificationRepository


class ReminderNotificationRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.manager = Mock()
        self.connection = Mock()
        self.cursor = Mock()
        self.manager.connect.return_value = self.connection
        self.connection.cursor.return_value = self.cursor
        self.repository = ReminderNotificationRepository(self.manager)

    def test_records_only_newly_inserted_reminders(self):
        self.cursor.rowcount = 1
        reminders = [{"habit_id": 6, "habit_name": "Drink Water", "reminder_time": "18:30"}]
        result = self.repository.record_due_reminders(17, reminders, "2026-10-24", "18:30")
        self.assertEqual(result, reminders)
        sql, params = self.cursor.execute.call_args.args
        self.assertIn("INSERT IGNORE INTO reminder_notifications", sql)
        self.assertIn("h.reminder_enabled = 1", sql)
        self.assertEqual(params, (17, "2026-10-24", "18:30", 6, 17, "18:30"))
        self.connection.commit.assert_called_once()

    def test_duplicate_delivery_is_not_returned(self):
        self.cursor.rowcount = 0
        result = self.repository.record_due_reminders(
            17, [{"habit_id": 6, "habit_name": "Drink Water", "reminder_time": "18:30"}],
            "2026-10-24", "18:30"
        )
        self.assertEqual(result, [])
        self.connection.commit.assert_called_once()

    def test_database_failure_rolls_back_and_raises_safe_error(self):
        self.cursor.execute.side_effect = RuntimeError("DB offline")
        with self.assertRaisesRegex(Exception, "Unable to record scheduled reminder history"):
            self.repository.record_due_reminders(
                17, [{"habit_id": 6, "habit_name": "Drink Water", "reminder_time": "18:30"}],
                "2026-10-24", "18:30"
            )
        self.connection.rollback.assert_called_once()
        self.connection.commit.assert_not_called()


if __name__ == "__main__":
    unittest.main()
