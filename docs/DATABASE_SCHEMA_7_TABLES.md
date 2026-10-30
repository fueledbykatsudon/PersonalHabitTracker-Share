# Personal Habit Tracker — Seven-Table Database Design

The application uses MySQL/MariaDB through XAMPP. On the first successful database connection, `DatabaseManager` performs an additive schema upgrade for older project databases. Back up the database in phpMyAdmin before launching an updated copy.

## Core tables

| Table | Purpose | Primary relationships |
|---|---|---|
| `roles` | Stores available account roles. | One role can be assigned to many users. |
| `users` | Stores full name, username, password hash, and role reference. | References `roles`; owns habits and audit records. |
| `habits` | Stores habit name, description, frequency, reminder settings, owner, and category reference. | References `users` and `habit_categories`; has completion and reminder history. |
| `habit_categories` | Normalized catalog of standard and custom category names. | Referenced by `habits.category_id`. |
| `habit_completions` | Records completion status by habit and date. | References `habits`. |
| `audit_logs` | Records key user and habit actions for accountability. | May reference `users`; system events may have a null user. |
| `reminder_notifications` | Stores each reminder delivery by habit, date, and scheduled time. | References `users` and `habits`; unique delivery key prevents duplicate notifications. |

## Migration behavior

- Existing role, account, habit, completion, and audit rows are preserved.
- Existing category labels are copied into `habit_categories` and linked by `habits.category_id`.
- The legacy `habits.category` label is retained and synchronized for compatibility with older backups.
- The application creates `reminder_notifications` and records reminders when they are delivered. A unique key on `(habit_id, reminder_date, reminder_time)` prevents the same scheduled reminder from firing twice for the same day and time after a restart.
- The application does not delete existing habit completion history as part of this schema upgrade.

## Important submission note

After launching and verifying the updated project, export the live `personal_habit_tracker` database from phpMyAdmin and include that export in the final submission ZIP. The exported schema should show all seven tables and the new foreign-key relationship for `habits.category_id`.
