import unittest
from unittest.mock import Mock, call

from repositories.habit_repository import HabitRepository, HabitRepositoryError


class HabitRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.manager = Mock()
        self.connection = Mock()
        self.cursor = Mock()
        self.manager.connect.return_value = self.connection
        self.connection.cursor.return_value = self.cursor
        self.repository = HabitRepository(self.manager)

    def test_create_uses_parameterized_sql_and_writes_audit(self):
        self.cursor.lastrowid = 23
        habit_id = self.repository.create(7, "Drink Water", "Health", "8 glasses", "Daily")

        self.assertEqual(habit_id, 23)
        self.assertEqual(self.cursor.execute.call_count, 3)
        category_sql, category_params = self.cursor.execute.call_args_list[0].args
        self.assertIn("INSERT INTO habit_categories", category_sql)
        self.assertEqual(category_params, ("Health",))
        insert_sql, insert_params = self.cursor.execute.call_args_list[1].args
        self.assertIn("category_id, category", insert_sql)
        self.assertIn("VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", insert_sql)
        self.assertEqual(insert_params, (7, "Drink Water", 23, "Health", "8 glasses", "Daily", None, 0))
        audit_sql, audit_params = self.cursor.execute.call_args_list[2].args
        self.assertIn("INSERT INTO audit_logs", audit_sql)
        self.assertEqual(audit_params[0:2], (7, "CREATE_HABIT"))
        self.connection.commit.assert_called_once()

    def test_create_maintains_normalized_category_catalog(self):
        self.cursor.lastrowid = 45
        self.repository.create(7, "Read", "Custom Category", "", "Daily")
        category_sql, params = self.cursor.execute.call_args_list[0].args
        self.assertIn("INSERT INTO habit_categories", category_sql)
        self.assertIn("ON DUPLICATE KEY UPDATE", category_sql)
        self.assertEqual(params, ("Custom Category",))
        insert_sql, insert_params = self.cursor.execute.call_args_list[1].args
        self.assertEqual(insert_params[2], 45)
        self.assertEqual(insert_params[3], "Custom Category")

    def test_create_persists_enabled_reminder(self):
        self.cursor.lastrowid = 24
        self.repository.create(7, "Drink Water", "Health", "8 glasses", "Daily", "18:30", True)
        insert_sql, insert_params = self.cursor.execute.call_args_list[1].args
        self.assertIn("reminder_time, reminder_enabled", insert_sql)
        self.assertEqual(insert_params[-2:], ("18:30", 1))

    def test_create_rejects_invalid_reminder_before_database_access(self):
        from validators.habit_validator import HabitValidationError
        with self.assertRaises(HabitValidationError):
            self.repository.create(7, "Drink Water", "Health", "8 glasses", "Daily", "25:00", True)
        self.manager.connect.assert_not_called()

    def test_list_enabled_reminders_is_scoped_to_user(self):
        self.cursor.fetchall.return_value = [{"habit_id": 4, "habit_name": "Read", "reminder_time": "18:30"}]
        result = self.repository.list_enabled_reminders(7)
        self.assertEqual(result[0]["habit_id"], 4)
        sql, params = self.cursor.execute.call_args.args
        self.assertIn("reminder_enabled = 1", sql)
        self.assertEqual(params, (7,))

    def test_update_checks_ownership_and_writes_audit(self):
        self.cursor.fetchone.return_value = ("Read",)
        self.cursor.lastrowid = 12
        self.repository.update(7, 4, "Read Daily", "Productivity", "Book", "Daily")

        self.assertEqual(self.cursor.execute.call_count, 4)
        update_sql, params = self.cursor.execute.call_args_list[2].args
        self.assertIn("WHERE habit_id = %s AND user_id = %s", update_sql)
        self.assertEqual(params[-2:], (4, 7))
        self.assertIn("INSERT INTO audit_logs", self.cursor.execute.call_args_list[3].args[0])
        self.connection.commit.assert_called_once()

    def test_update_persists_reminder_settings(self):
        self.cursor.fetchone.return_value = ("Read",)
        self.cursor.lastrowid = 12
        self.repository.update(7, 4, "Read", "Productivity", "Book", "Daily", "07:15", True)
        update_sql, params = self.cursor.execute.call_args_list[2].args
        self.assertIn("reminder_time = %s, reminder_enabled = %s", update_sql)
        self.assertEqual(params[5:7], ("07:15", 1))
        self.assertEqual(params[-2:], (4, 7))

    def test_update_rejects_habit_not_owned_by_user(self):
        self.cursor.fetchone.return_value = None
        with self.assertRaises(HabitRepositoryError):
            self.repository.update(7, 4, "Read Daily", "Productivity", "Book", "Daily")
        self.connection.commit.assert_not_called()
        self.connection.rollback.assert_called_once()

    def test_delete_removes_completion_rows_before_habit_and_writes_audit(self):
        self.cursor.fetchone.return_value = {"habit_name": "Read"}
        self.repository.delete(7, 4)

        statements = [item.args[0] for item in self.cursor.execute.call_args_list]
        self.assertIn("DELETE FROM habit_completions", statements[1])
        self.assertIn("DELETE FROM habits", statements[2])
        self.assertIn("INSERT INTO audit_logs", statements[3])
        self.connection.commit.assert_called_once()

    def test_database_connection_failure_is_wrapped(self):
        self.manager.connect.side_effect = RuntimeError("connection unavailable")
        with self.assertRaises(HabitRepositoryError):
            self.repository.list_for_user(7)

    def test_invalid_input_does_not_connect_to_database(self):
        with self.assertRaises(ValueError):
            self.repository.create(7, "", "Health", "", "Daily")
        self.manager.connect.assert_not_called()


if __name__ == "__main__":
    unittest.main()
