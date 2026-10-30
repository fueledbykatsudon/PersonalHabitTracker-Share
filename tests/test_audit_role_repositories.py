"""Tests for role lookup and audit repository SQL helpers."""

import unittest
from unittest.mock import Mock

from core.exceptions import DatabaseError
from repositories.audit_log_repository import AuditLogRepository
from repositories.role_repository import RoleRepository


class RoleRepositoryTests(unittest.TestCase):
    def test_prefers_standard_user_role_name(self):
        cursor = Mock()
        cursor.fetchone.side_effect = [{"role_id": 5}]
        self.assertEqual(RoleRepository.standard_user_role_id(cursor), 5)
        self.assertEqual(cursor.execute.call_args.args[1], ("Standard User",))

    def test_supports_existing_legacy_user_role_name(self):
        cursor = Mock()
        cursor.fetchone.side_effect = [None, {"role_id": 2}]
        self.assertEqual(RoleRepository.standard_user_role_id(cursor), 2)
        self.assertEqual(cursor.execute.call_count, 2)

    def test_missing_standard_role_raises_database_error(self):
        cursor = Mock()
        cursor.fetchone.side_effect = [None, None]
        with self.assertRaises(DatabaseError):
            RoleRepository.standard_user_role_id(cursor)


class AuditLogRepositoryTests(unittest.TestCase):
    def test_insert_helper_uses_parameterized_statement(self):
        cursor = Mock()
        AuditLogRepository.insert_with_cursor(cursor, 3, "CREATE_HABIT", "Created test habit")
        sql, params = cursor.execute.call_args.args
        self.assertIn("VALUES (%s, %s, %s)", sql)
        self.assertEqual(params, (3, "CREATE_HABIT", "Created test habit"))

    def test_invalid_limit_rejected_before_db_connection(self):
        manager = Mock()
        repo = AuditLogRepository(manager)
        with self.assertRaises(ValueError):
            repo.list_recent(5000)
        manager.connect.assert_not_called()


if __name__ == "__main__":
    unittest.main()
