# Personal Habit Tracker & Wellness Advisor

Python desktop application using Tkinter and MySQL/MariaDB through XAMPP.

## Requirements

- Python 3.10 or later
- XAMPP with MySQL/MariaDB running
- The `personal_habit_tracker` database and its tables created/imported in phpMyAdmin

## Existing database migration and backups

Before launching an updated copy against your real `personal_habit_tracker` database, export a backup in phpMyAdmin. On its first successful connection, the application checks for the reminder columns and applies the additive seven-table extension: it creates `habit_categories`, links existing habits by `category_id`, and creates `reminder_notifications`. It preserves existing account, habit, completion, and audit records. The old text category field is retained for compatibility with older project copies. See `docs/DATABASE_SCHEMA_7_TABLES.md` for the table list and relationships. The app's database user must have permission to create tables and alter `habits`.

After verifying the updated application, export the database again from phpMyAdmin so your submission contains the current seven-table schema.

## Install and run (Windows PowerShell)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

To run automated tests:

```powershell
python -m unittest discover -s tests -v
```

## Database connection options

Defaults are compatible with a basic local XAMPP installation: host `localhost`, port `3306`, user `root`, blank password, database `personal_habit_tracker`. These can be overridden with environment variables:

- `PHT_DB_HOST`
- `PHT_DB_PORT`
- `PHT_DB_USER`
- `PHT_DB_PASSWORD`
- `PHT_DB_NAME`

Do not commit real database passwords or other secrets into source control.

## Project layers

- `models/` — account hierarchy and encapsulated domain entities.
- `views/` — Tkinter screens.
- `controllers/` — coordinates requests from the GUI.
- `repositories/` — parameterized MySQL queries for users, roles, habits, categories, completions, audit events, and reminder history.
- `database/` — Singleton connection manager and additive schema-upgrade logic.
- `security/` — password hashing and legacy-hash migration support.
- `validators/` — user-input validation.
- `tests/` — automated unit tests; repository tests mock database connections.
- `logs/` — rotating diagnostic log created when the program runs.

The existing database may use `Admin` and `User` in `roles`. The application maps the `User` label to `Standard User` for display/permissions without requiring a table rename.

## Daily habit reminders

The app supports optional daily reminders for each habit. In Add Habit or Edit Habit, enable **Enable reminder** and enter a time using 24-hour `HH:MM` format (for example, `18:30`). When that time arrives, the app shows an in-app reminder popup. The app must remain open and the user must remain signed in; reminders do not run as Windows notifications while the app is closed. The scheduler polls every 15 seconds and shows each habit reminder at most once per day/time. Delivery events are stored in `reminder_notifications`, allowing the system to suppress duplicate delivery records after a restart.

## Wellness Advisor

The Wellness Advisor reads the signed-in user's last-30-days progress report from MySQL. `services/wellness_advisor.py` applies simple Python rules to provide suggestions for starting a habit, building a tracking baseline, maintaining consistency, or adjusting a habit. It does not call an AI service or provide medical advice. The rules are covered by `tests/test_wellness_advisor.py`.


### Wellness Advisor navigation fix
- The Wellness Advisor remains available as a compact panel on the Dashboard, Habit Tracking, and Reports screens.
- Added a direct **Wellness Advisor** sidebar link to Habit Tracking and Reports, so users can open the full advisor without first returning to the Dashboard.
- This is a navigation/UI fix only; it does not change the MySQL schema or stored data.

## Seven-table database design

The seven core tables are `roles`, `users`, `habits`, `habit_categories`, `habit_completions`, `audit_logs`, and `reminder_notifications`. See `docs/DATABASE_SCHEMA_7_TABLES.md` for their purpose and relationships.
