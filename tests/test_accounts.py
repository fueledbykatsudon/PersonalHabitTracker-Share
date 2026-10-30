"""Tests for the abstract account hierarchy and polymorphic role behavior."""

import unittest

from core.exceptions import ValidationError
from models.accounts import Account, AdminAccount, StandardUserAccount, account_from_user_record


class AccountModelTests(unittest.TestCase):
    def test_base_account_is_abstract(self):
        with self.assertRaises(TypeError):
            Account(1, "Test User", "testuser", 2)

    def test_admin_and_standard_accounts_override_permissions(self):
        accounts = [
            AdminAccount(1, "Admin Person", "admin", 1),
            StandardUserAccount(2, "Regular Person", "regular", 2),
        ]
        self.assertEqual([account.role_name for account in accounts], ["Admin", "Standard User"])
        self.assertTrue(accounts[0].can_manage_users)
        self.assertFalse(accounts[1].can_manage_users)
        self.assertTrue(accounts[1].has_permission("track_own_habits"))
        self.assertNotEqual(accounts[0].permissions(), accounts[1].permissions())

    def test_greeting_is_polymorphic(self):
        accounts = [AdminAccount(1, "Alex Admin", "admin", 1), StandardUserAccount(2, "Sam User", "sam", 2)]
        greetings = [account.dashboard_greeting() for account in accounts]
        self.assertIn("Administrator", greetings[0])
        self.assertIn("build better habits", greetings[1])

    def test_factory_accepts_legacy_user_role_name(self):
        account = account_from_user_record({
            "user_id": 4, "full_name": "Mark", "username": "mark123",
            "role_id": 2, "role_name": "User",
        })
        self.assertIsInstance(account, StandardUserAccount)
        self.assertEqual(account.role_name, "Standard User")

    def test_encapsulated_identity_validation(self):
        account = StandardUserAccount(2, "Mark", "mark123", 2)
        with self.assertRaises(ValidationError):
            account.username = " "
        with self.assertRaises(ValidationError):
            account.user_id = 0


if __name__ == "__main__":
    unittest.main()
