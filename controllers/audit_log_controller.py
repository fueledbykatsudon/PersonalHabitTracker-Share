"""Controller for administrator audit-log queries."""

from repositories.audit_log_repository import AuditLogRepository


class AuditLogController:
    def __init__(self, repository=None):
        self.repository = repository or AuditLogRepository()

    def list_recent(self, limit: int = 200) -> list[dict]:
        return self.repository.list_recent(limit)
