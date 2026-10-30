"""DAO for audit trail writes and administrative audit-log reads."""

import logging

from core.exceptions import DatabaseError
from database.database_manager import DatabaseManager

logger = logging.getLogger(__name__)


class AuditLogRepository:
    def __init__(self, database_manager=None):
        self.database_manager = database_manager or DatabaseManager()

    @staticmethod
    def insert_with_cursor(cursor, user_id: int | None, action: str, description: str) -> None:
        """Insert into the caller's transaction; caller controls commit/rollback."""
        cursor.execute(
            "INSERT INTO audit_logs (user_id, action, description) VALUES (%s, %s, %s)",
            (user_id, action, description),
        )

    def list_recent(self, limit: int = 200) -> list[dict]:
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 1000:
            raise ValueError("Audit log limit must be between 1 and 1000.")
        connection = None
        cursor = None
        try:
            connection = self.database_manager.connect()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """SELECT a.log_id, COALESCE(u.username, 'System') AS username,
                          a.action, a.description, a.created_at
                   FROM audit_logs AS a
                   LEFT JOIN users AS u ON u.user_id = a.user_id
                   ORDER BY a.log_id DESC LIMIT %s""",
                (limit,),
            )
            return cursor.fetchall()
        except Exception as exc:
            logger.exception("Failed to list audit logs")
            raise DatabaseError("Unable to load audit logs from the database.") from exc
        finally:
            if cursor is not None:
                try:
                    cursor.close()
                except Exception:
                    logger.exception("Failed to close audit-log cursor")
