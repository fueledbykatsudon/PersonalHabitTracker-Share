"""DAO for role lookup and compatibility with the existing roles table."""

import logging

from core.exceptions import DatabaseError

logger = logging.getLogger(__name__)


class RoleRepository:
    """Role-specific SQL helpers; accepts a caller cursor to share transactions."""

    @staticmethod
    def standard_user_role_id(cursor) -> int:
        for role_name in ("Standard User", "User"):
            cursor.execute("SELECT role_id FROM roles WHERE role_name = %s LIMIT 1", (role_name,))
            row = cursor.fetchone()
            if row:
                value = row.get("role_id") if isinstance(row, dict) else row[0]
                return int(value)
        raise DatabaseError("The standard user role is missing from the roles table.")

    @staticmethod
    def role_id_for_name(cursor, role_name: str) -> int | None:
        cursor.execute("SELECT role_id FROM roles WHERE role_name = %s LIMIT 1", (role_name,))
        row = cursor.fetchone()
        if not row:
            return None
        value = row.get("role_id") if isinstance(row, dict) else row[0]
        return int(value)
