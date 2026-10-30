# OOP Architecture Notes for Defense

## Abstraction, inheritance, and polymorphism

`models/accounts.py` defines abstract class `Account`. It requires each concrete account type to implement `role_name`, `permissions()`, and `dashboard_greeting()`.

- `AdminAccount` overrides those methods to provide administrative permissions and an administrator greeting.
- `StandardUserAccount` overrides those methods to provide personal habit/tracking/report permissions and a standard-user greeting.
- `DashboardWindow` creates the concrete account with `account_from_user_record()` and uses `dashboard_greeting()` and `can_manage_users`, so both account types are used through the shared base-class contract.

## Encapsulation

`Account`, `Habit`, and `HabitCompletion` store fields in private attributes and expose validated `@property` accessors and setters. Passwords are not stored in account objects; `security/passwords.py` hashes passwords and verifies them before authentication.

## Design patterns and layers

- **Singleton:** `database/database_manager.py` allows a single `DatabaseManager` instance to manage the active connection.
- **Repository/DAO:** classes in `repositories/` contain parameterized SQL for users, roles, habits, tracking/report data, and audit events.
- **MVC-inspired separation:** `views/` handles Tkinter UI; `controllers/` coordinates application requests; `models/` represents domain objects; `repositories/` performs persistence.
- **Custom exceptions:** `core/exceptions.py`, `validators/habit_validator.py`, and the repository-specific error types produce application-level errors that views can show safely.
- **Rotating log:** `main.py` configures `logging.handlers.RotatingFileHandler`; the log is a text file separate from MySQL audit entries.

## Data flow example

1. `LoginWindow` passes entered values to `UserController`.
2. `UserController` delegates to `UserRepository`.
3. `UserRepository` performs parameterized SQL, verifies the password hash, and returns a safe user record without `password_hash`.
4. `DashboardWindow` uses `account_from_user_record()` to select the correct concrete account class.
5. Habit and tracking screens call controllers; controllers call repositories; repositories use `DatabaseManager` and write related audit events in the same transaction.
