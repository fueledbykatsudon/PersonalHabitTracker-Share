"""Deterministic tests for the in-app reminder scheduler."""

import unittest
from datetime import datetime
from unittest.mock import Mock

from services.reminder_scheduler import ReminderScheduler, stop_window_reminder_scheduler


class ReminderSchedulerTests(unittest.TestCase):
    def setUp(self):
        self.root = Mock()
        self.root.after.return_value = "after-1"
        self.controller = Mock()
        self.controller.list_enabled_reminders.return_value = [
            {"habit_id": 6, "habit_name": "Drink Water", "reminder_time": "18:30"},
            {"habit_id": 8, "habit_name": "Exercise", "reminder_time": "07:00"},
        ]
        self.controller.record_due_reminders.side_effect = (
            lambda _user_id, reminders, _date, _time: list(reminders)
        )
        self.notifier = Mock()
        self.clock = Mock(return_value=datetime(2026, 10, 24, 18, 30, 10))
        self.scheduler = ReminderScheduler(
            self.root, 17, controller=self.controller, notifier=self.notifier,
            clock=self.clock, interval_ms=10_000,
        )

    def test_due_reminder_notifies_once(self):
        due = self.scheduler.check_due_now()
        self.assertEqual([item["habit_id"] for item in due], [6])
        self.notifier.assert_called_once_with([
            {"habit_id": 6, "habit_name": "Drink Water", "reminder_time": "18:30"}
        ])
        self.controller.record_due_reminders.assert_called_once_with(
            17,
            [{"habit_id": 6, "habit_name": "Drink Water", "reminder_time": "18:30"}],
            "2026-10-24", "18:30",
        )
        self.scheduler.check_due_now()
        self.notifier.assert_called_once()

    def test_non_due_reminder_is_not_shown(self):
        self.clock.return_value = datetime(2026, 10, 24, 12, 0)
        due = self.scheduler.check_due_now()
        self.assertEqual(due, [])
        self.notifier.assert_not_called()

    def test_multiple_due_reminders_are_grouped(self):
        self.controller.list_enabled_reminders.return_value = [
            {"habit_id": 6, "habit_name": "Drink Water", "reminder_time": "18:30"},
            {"habit_id": 9, "habit_name": "Journal", "reminder_time": "18:30"},
        ]
        due = self.scheduler.check_due_now()
        self.assertEqual(len(due), 2)
        self.notifier.assert_called_once()

    def test_persisted_duplicate_reminder_is_not_shown(self):
        self.controller.record_due_reminders.side_effect = None
        self.controller.record_due_reminders.return_value = []
        due = self.scheduler.check_due_now()
        self.assertEqual(due, [])
        self.notifier.assert_not_called()

    def test_shared_stop_helper_removes_scheduler_from_window(self):
        scheduler = Mock()
        self.root._pht_reminder_scheduler = scheduler
        stop_window_reminder_scheduler(self.root)
        scheduler.stop.assert_called_once_with()
        self.assertFalse(hasattr(self.root, "_pht_reminder_scheduler"))

    def test_stop_cancels_pending_callback(self):
        self.scheduler.start()
        self.root.after.assert_called_once_with(1_000, self.scheduler._tick)
        self.scheduler.stop()
        self.root.after_cancel.assert_called_once_with("after-1")
        self.assertFalse(self.scheduler.running)


if __name__ == "__main__":
    unittest.main()
