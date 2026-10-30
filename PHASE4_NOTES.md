# Phase 4 — OOP and Layered Architecture

## Implemented in this phase

- Added `models.accounts.Account`, an abstract base class with concrete `AdminAccount` and `StandardUserAccount` subclasses that override `permissions()` and `dashboard_greeting()`.
- Added `account_from_user_record()` so the active dashboard uses polymorphic role behavior and normalizes the database's existing `User` role name to `Standard User` in the application.
- Added encapsulated `Habit` and `HabitCompletion` domain models with private attributes and `@property` setters for validation.
- Added `UserRepository`, `RoleRepository`, and `AuditLogRepository`; authentication, registration, user listing, role lookup, and audit listing now live outside their Tkinter screens.
- Added `HabitController`, `ProgressController`, `UserController`, and `AuditLogController`; the UI now calls controllers for those workflows, while the repositories contain parameterized SQL.
- Habit and completion repositories now use the domain models and centralized audit-log insertion helper.
- Kept the Singleton `DatabaseManager`, added environment-variable overrides for connection settings, and retained rotating-file logging configured at startup.
- Added a Wellness Advisor entry to the active dashboard and updated its navigation so it returns to the authenticated dashboard rather than the old prototype dashboard.
- Added tests for the account hierarchy, polymorphism, model validation, role lookup, audit SQL, repository workflows, and Singleton creation.

## Current role/database compatibility

The exported database has `roles` values named `Admin` and `User`. The account factory and role repository intentionally support this existing schema and present `User` as `Standard User` in the application. This phase does not require SQL migration.

## Verification status

- Python syntax compilation: checked.
- Unit tests: checked with mocked database access (the development container did not have `mysql-connector-python` installed; the project's `requirements.txt` lists it). Install dependencies inside the application's virtual environment before running locally.
- GUI and live MariaDB integration: must be retested on the user's PC before declaring this phase complete.
