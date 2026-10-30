"""Unit tests for user DAO methods with mock MySQL objects."""

import unittest
from unittest.mock import Mock

from core.exceptions import AuthenticationError, ValidationError
from repositories.user_repository import UserRepository
from security.passwords import hash_password


class UserRepositoryTests(unittest.TestCase):
    def setUp(self):
        self.manager = Mock()
        self.connection = Mock()
        self.cursor = Mock()
        self.manager.connect.return_value = self.connection
        self.connection.cursor.return_value = self.cursor
        self.roles = Mock()
        self.roles.standard_user_role_id.return_value = 2
        self.repo = UserRepository(self.manager, self.roles)

    def test_authentication_returns_normalized_user_role(self):
        self.cursor.fetchone.return_value = {
            "user_id": 9, "full_name": "Test Person", "username": "tester",
            "password_hash": hash_password("password123"), "role_id": 2, "role_name": "User",
        }
        user = self.repo.authenticate("tester", "password123")
        self.assertEqual(user["role_name"], "Standard User")
        self.assertEqual(user["user_id"], 9)
        self.assertNotIn("password_hash", user)

    def test_authentication_rejects_wrong_password(self):
        self.cursor.fetchone.return_value = {
            "user_id": 9, "full_name": "Test Person", "username": "tester",
            "password_hash": hash_password("password123"), "role_id": 2, "role_name": "User",
        }
        with self.assertRaises(AuthenticationError):
            self.repo.authenticate("tester", "badpassword")

    def test_registration_inserts_user_and_audit_record(self):
        self.cursor.fetchone.side_effect = [None]
        self.cursor.lastrowid = 14
        user_id = self.repo.register("Test Person", "tester", "password123")
        self.assertEqual(user_id, 14)
        self.roles.standard_user_role_id.assert_called_once_with(self.cursor)
        executed = [call.args[0] for call in self.cursor.execute.call_args_list]
        self.assertTrue(any("INSERT INTO users" in sql for sql in executed))
        self.assertTrue(any("INSERT INTO audit_logs" in sql for sql in executed))
        self.connection.commit.assert_called_once()

    def test_registration_rejects_short_password_before_database(self):
        with self.assertRaises(ValidationError):
            self.repo.register("Test Person", "tester", "short")
        self.manager.connect.assert_not_called()

    def test_username_validation_rejects_blank(self):
        with self.assertRaises(ValidationError):
            self.repo.authenticate("  ", "password123")
        self.manager.connect.assert_not_called()


if __name__ == "__main__":
    unittest.main()
