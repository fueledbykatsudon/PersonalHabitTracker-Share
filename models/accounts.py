"""Role-aware account models demonstrating abstraction and polymorphism."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Mapping

from core.exceptions import ValidationError


class Account(ABC):
    """Abstract account base. Raw passwords are deliberately never stored here."""

    def __init__(self, user_id: int, full_name: str, username: str, role_id: int):
        self.user_id = user_id
        self.full_name = full_name
        self.username = username
        self.role_id = role_id

    @property
    def user_id(self) -> int:
        return self.__user_id

    @user_id.setter
    def user_id(self, value: int) -> None:
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValidationError("User ID must be a positive integer.")
        self.__user_id = value

    @property
    def full_name(self) -> str:
        return self.__full_name

    @full_name.setter
    def full_name(self, value: str) -> None:
        if not isinstance(value, str) or not value.strip() or len(value.strip()) > 100:
            raise ValidationError("Full name must contain 1–100 characters.")
        self.__full_name = value.strip()

    @property
    def username(self) -> str:
        return self.__username

    @username.setter
    def username(self, value: str) -> None:
        if not isinstance(value, str) or not value.strip() or len(value.strip()) > 50:
            raise ValidationError("Username must contain 1–50 characters.")
        self.__username = value.strip()

    @property
    def role_id(self) -> int:
        return self.__role_id

    @role_id.setter
    def role_id(self, value: int) -> None:
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValidationError("Role ID must be a positive integer.")
        self.__role_id = value

    @property
    @abstractmethod
    def role_name(self) -> str:
        """Normalized role label for application-level permissions."""

    @abstractmethod
    def permissions(self) -> frozenset[str]:
        """Return the permissions assigned to this account type."""

    @abstractmethod
    def dashboard_greeting(self) -> str:
        """Return a greeting appropriate to this account type."""

    def has_permission(self, permission: str) -> bool:
        return permission in self.permissions()

    @property
    def can_manage_users(self) -> bool:
        return self.has_permission("manage_users")

    @property
    def can_view_audit_logs(self) -> bool:
        return self.has_permission("view_audit_logs")


class AdminAccount(Account):
    """Concrete administrator account with management permissions."""

    @property
    def role_name(self) -> str:
        return "Admin"

    def permissions(self) -> frozenset[str]:
        return frozenset({"manage_users", "view_audit_logs", "manage_own_habits", "view_own_reports"})

    def dashboard_greeting(self) -> str:
        return f"Welcome back, {self.full_name}. Administrator access is enabled."


class StandardUserAccount(Account):
    """Concrete standard user with access to personal habit features only."""

    @property
    def role_name(self) -> str:
        return "Standard User"

    def permissions(self) -> frozenset[str]:
        return frozenset({"manage_own_habits", "track_own_habits", "view_own_reports", "view_wellness_advice"})

    def dashboard_greeting(self) -> str:
        return f"Good day, {self.full_name}! Let's build better habits."


def account_from_user_record(record: Mapping[str, Any]) -> Account:
    """Create the correct concrete account while keeping legacy DB role names compatible."""
    role = str(record.get("role_name") or record.get("database_role_name") or "User").strip().casefold()
    cls = AdminAccount if role == "admin" else StandardUserAccount
    role_id = record.get("role_id", 2)
    user_id = record.get("user_id")
    return cls(
        user_id=int(user_id),
        full_name=str(record.get("full_name") or record.get("username") or "User"),
        username=str(record.get("username") or "user"),
        role_id=int(role_id),
    )
