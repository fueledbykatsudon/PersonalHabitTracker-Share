import unittest
from unittest.mock import Mock

from repositories.progress_repository import ProgressRepository, ProgressRepositoryError


class ProgressRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.manager = Mock()
        self.connection = Mock()
        self.cursor = Mock()
        self.manager.connect.return_value = self.connection
        self.connection.cursor.return_value = self.cursor
        self.repository = ProgressRepository(self.manager)

    def test_list_today_returns_user_scoped_habit_statuses(self):
        self.cursor.fetchall.return_value = [
            {"habit_id": 3, "habit_name": "Read", "category": "Learning", "completed": 1},
            {"habit_id": 4, "habit_name": "Walk", "category": "Health", "completed": 0},
        ]
        result = self.repository.list_today(12)
        self.assertEqual(len(result), 2)
        self.assertTrue(result[0]["completed"])
        self.assertFalse(result[1]["completed"])
        self.assertEqual(self.cursor.execute.call_args.args[1], (12,))
        self.assertIn("WHERE h.user_id = %s", self.cursor.execute.call_args.args[0])

    def test_mark_completed_inserts_daily_status_and_audit(self):
        self.cursor.fetchone.side_effect = [{"habit_name": "Read"}, None]
        self.repository.set_status(12, 3, True)
        statements = [call.args[0] for call in self.cursor.execute.call_args_list]
        self.assertTrue(any("INSERT INTO habit_completions" in sql for sql in statements))
        self.assertTrue(any("INSERT INTO audit_logs" in sql for sql in statements))
        self.connection.commit.assert_called_once()
        self.connection.rollback.assert_not_called()

    def test_reset_updates_existing_daily_status(self):
        self.cursor.fetchone.side_effect = [
            {"habit_name": "Read"}, {"completion_id": 44}
        ]
        self.repository.set_status(12, 3, False)
        statements = [call.args[0] for call in self.cursor.execute.call_args_list]
        self.assertTrue(any("UPDATE habit_completions SET completed" in sql for sql in statements))
        self.assertTrue(any("INSERT INTO audit_logs" in sql for sql in statements))
        self.connection.commit.assert_called_once()

    def test_cannot_track_habit_owned_by_another_user(self):
        self.cursor.fetchone.return_value = None
        with self.assertRaises(ProgressRepositoryError):
            self.repository.set_status(12, 999, True)
        self.connection.commit.assert_not_called()
        self.connection.rollback.assert_called_once()

    def test_database_connection_failure_is_wrapped(self):
        self.manager.connect.side_effect = RuntimeError("DB offline")
        with self.assertRaises(ProgressRepositoryError):
            self.repository.list_today(12)

    def test_report_summarizes_recorded_habit_days(self):
        self.cursor.fetchall.return_value = [
            {"habit_id": 1, "habit_name": "Read", "category": "Learning",
             "recorded_days": 4, "completed_days": 3, "last_tracked": None},
            {"habit_id": 2, "habit_name": "Walk", "category": "Health",
             "recorded_days": 1, "completed_days": 1, "last_tracked": None},
        ]
        result = self.repository.get_report(12)
        self.assertEqual(result["total_habits"], 2)
        self.assertEqual(result["recorded_days"], 5)
        self.assertEqual(result["completed_days"], 4)
        self.assertEqual(result["completion_rate"], 80)
        self.assertEqual(len(result["rows"]), 2)


if __name__ == "__main__":
    unittest.main()
