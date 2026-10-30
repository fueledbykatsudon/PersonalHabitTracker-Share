
"""Create the first Admin account for Personal Habit Tracker."""

from getpass import getpass
import sys

import mysql.connector

from database.database_manager import DatabaseManager
from repositories.audit_log_repository import AuditLogRepository
from security.passwords import hash_password


def main():
    print("Personal Habit Tracker - Create First Admin Account\n")

    full_name = input("Admin full name: ").strip()
    username = input("Admin username: ").strip()

    if not full_name or len(full_name) > 100:
        print("Please enter a name of 1-100 characters.")
        return 1

    if not username or len(username) > 50:
        print("Please enter a username of 1-50 characters.")
        return 1

    password = input("Admin password (minimum 12 characters): ")
    confirm = input("Confirm admin password: ")

    if len(password) < 12:
        print("Password must be at least 12 characters.")
        return 1

    if password != confirm:
        print("Passwords do not match.")
        return 1

    manager = DatabaseManager()
    connection = None
    cursor = None

    try:
        connection = manager.connect()
        cursor = connection.cursor(dictionary=True)

        cursor.execute(
            "SELECT role_id FROM roles "
            "WHERE LOWER(TRIM(role_name)) = %s LIMIT 1",
            ("admin",)
        )
        role = cursor.fetchone()

        if not role:
            print("The Admin role is missing from the roles table.")
            connection.rollback()
            return 1

        admin_role_id = role["role_id"]

        cursor.execute(
            "SELECT user_id FROM users WHERE role_id = %s LIMIT 1",
            (admin_role_id,)
        )
        if cursor.fetchone():
            print("An Admin account already exists. No new account created.")
            connection.rollback()
            return 1

        cursor.execute(
            "SELECT user_id FROM users WHERE username = %s LIMIT 1",
            (username,)
        )
        if cursor.fetchone():
            print("That username already exists. Choose another.")
            connection.rollback()
            return 1

        cursor.execute(
            """
            INSERT INTO users
                (full_name, username, password_hash, role_id)
            VALUES (%s, %s, %s, %s)
            """,
            (full_name, username, hash_password(password), admin_role_id)
        )

        admin_id = cursor.lastrowid

        AuditLogRepository.insert_with_cursor(
            cursor,
            admin_id,
            "CREATE_ADMIN_USER",
            f"Initial administrator account '{username}' created."
        )

        connection.commit()

        print("\nAdmin account created successfully!")
        print(f"User ID: {admin_id}")
        print("You can now log in using the new Admin credentials.")
        return 0

    except mysql.connector.Error as exc:
        if connection is not None:
            connection.rollback()
        print(f"\nDatabase error: {exc}")
        return 1

    except Exception as exc:
        if connection is not None:
            connection.rollback()
        print(f"\nUnexpected error: {type(exc).__name__}: {exc}")
        return 1

    finally:
        if cursor is not None:
            cursor.close()


if __name__ == "__main__":
    sys.exit(main())
