"""DAO for user authentication, registration, and administrative user listings."""

from __future__ import annotations

import logging

import mysql.connector

from core.exceptions import AuthenticationError, DatabaseError, ValidationError
from database.database_manager import DatabaseManager
from repositories.audit_log_repository import AuditLogRepository
from repositories.role_repository import RoleRepository
from security.passwords import hash_password, verify_password

logger = logging.getLogger(__name__)


class InvalidCredentialsError(AuthenticationError):
    """Raised for any invalid username/password combination."""


class UserRepository:
    def __init__(self, database_manager=None, role_repository=None):
        self.database_manager = database_manager or DatabaseManager()
        self.role_repository = role_repository or RoleRepository()

    def authenticate(self, username: str, password: str) -> dict:
        username = self._validate_username(username)
        if not isinstance(password, str) or not password:
            raise InvalidCredentialsError("Invalid username or password.")
        connection = None
        cursor = None
        try:
            connection = self.database_manager.connect()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """SELECT u.user_id, u.full_name, u.username, u.password_hash,
                          u.role_id, r.role_name
                   FROM users AS u
                   INNER JOIN roles AS r ON r.role_id = u.role_id
                   WHERE u.username = %s LIMIT 1""",
                (username,),
            )
            account = cursor.fetchone()
            if not account:
                raise InvalidCredentialsError("Invalid username or password.")
            valid, needs_upgrade = verify_password(password, account["password_hash"])
            if not valid:
                raise InvalidCredentialsError("Invalid username or password.")
            if needs_upgrade:
                cursor.execute(
                    "UPDATE users SET password_hash = %s WHERE user_id = %s",
                    (hash_password(password), account["user_id"]),
                )
                connection.commit()
            database_role = str(account.get("role_name") or "User")
            normalized_role = "Admin" if database_role.strip().casefold() == "admin" else "Standard User"
            logger.info("Account authenticated username=%s role=%s", username, normalized_role)
            return {
                "user_id": int(account["user_id"]),
                "full_name": account["full_name"],
                "username": account["username"],
                "role_id": int(account["role_id"]),
                "role_name": normalized_role,
                "database_role_name": database_role,
            }
        except InvalidCredentialsError:
            logger.warning("Authentication rejected username=%s", username)
            raise
        except mysql.connector.Error as exc:
            logger.exception("Database failure during user authentication")
            raise DatabaseError("Could not connect to the account database. Check XAMPP and database settings.") from exc
        except Exception as exc:
            if isinstance(exc, (DatabaseError, ValidationError)):
                raise
            logger.exception("Unexpected failure during user authentication")
            raise DatabaseError("An unexpected error interrupted login.") from exc
        finally:
            self._close_cursor(cursor)

    def register(self, full_name: str, username: str, password: str) -> int:
        full_name = self._validate_full_name(full_name)
        username = self._validate_username(username)
        if not isinstance(password, str) or len(password) < 8:
            raise ValidationError("Password must be at least 8 characters long.")
        if any(ord(char) < 32 for char in username):
            raise ValidationError("Username contains unsupported control characters.")

        connection = None
        cursor = None
        try:
            connection = self.database_manager.connect()
            cursor = connection.cursor(dictionary=True)
            cursor.execute("SELECT user_id FROM users WHERE username = %s LIMIT 1", (username,))
            if cursor.fetchone():
                raise ValidationError("That username is already registered.")
            role_id = self.role_repository.standard_user_role_id(cursor)
            cursor.execute(
                "INSERT INTO users (full_name, username, password_hash, role_id) VALUES (%s, %s, %s, %s)",
                (full_name, username, hash_password(password), role_id),
            )
            new_user_id = int(cursor.lastrowid)
            AuditLogRepository.insert_with_cursor(
                cursor, new_user_id, "CREATE_USER", f"Account registered for username '{username}'."
            )
            connection.commit()
            logger.info("User registered username=%s user_id=%s", username, new_user_id)
            return new_user_id
        except ValidationError:
            self._safe_rollback(connection)
            raise
        except mysql.connector.IntegrityError as exc:
            self._safe_rollback(connection)
            logger.warning("Duplicate or constrained user registration username=%s", username)
            raise ValidationError("That username already exists or account data violates a database constraint.") from exc
        except Exception as exc:
            self._safe_rollback(connection)
            logger.exception("Failed to register user username=%s", username)
            if isinstance(exc, DatabaseError):
                raise
            raise DatabaseError("The account could not be created. Check the database connection and role setup.") from exc
        finally:
            self._close_cursor(cursor)

    def list_users(self) -> list[dict]:
        connection = None
        cursor = None
        try:
            connection = self.database_manager.connect()
            cursor = connection.cursor(dictionary=True)
            cursor.execute(
                """SELECT u.user_id, u.full_name, u.username, r.role_name, u.created_at
                   FROM users AS u INNER JOIN roles AS r ON r.role_id = u.role_id
                   ORDER BY u.user_id DESC"""
            )
            return cursor.fetchall()
        except Exception as exc:
            logger.exception("Failed to list users")
            raise DatabaseError("Unable to load registered users from the database.") from exc
        finally:
            self._close_cursor(cursor)

    @staticmethod
    def _validate_full_name(value: str) -> str:
        if not isinstance(value, str) or not value.strip() or len(value.strip()) > 100:
            raise ValidationError("Full name must contain 1–100 characters.")
        if any(ord(char) < 32 for char in value.strip()):
            raise ValidationError("Full name contains unsupported control characters.")
        return value.strip()

    @staticmethod
    def _validate_username(value: str) -> str:
        if not isinstance(value, str) or not value.strip() or len(value.strip()) > 50:
            raise ValidationError("Username must contain 1–50 characters.")
        return value.strip()

    @staticmethod
    def _close_cursor(cursor) -> None:
        if cursor is not None:
            try:
                cursor.close()
            except Exception:
                logger.exception("Failed to close user repository cursor")

    @staticmethod
    def _safe_rollback(connection) -> None:
        try:
            if connection is not None:
                connection.rollback()
        except Exception:
            logger.exception("Rollback failed during user repository operation")
