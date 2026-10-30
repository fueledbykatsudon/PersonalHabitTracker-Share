# Daily Reminder Demonstration

## Purpose
The optional reminder helps a user remember a planned habit by displaying an in-app message at a chosen time.

## Setup
1. Back up the `personal_habit_tracker` database using phpMyAdmin.
2. Select `personal_habit_tracker` in phpMyAdmin, open **Import**, choose `database/migrations/001_add_habit_reminder_columns.sql`, and click **Go**. You can instead paste the statements from the file into the **SQL** tab.
3. Launch the app and sign in.
4. Open **+ Add Habit** or select a habit and choose **Edit Selected**.
5. Enable **Enable reminder** and set a time in 24-hour `HH:MM` format.
6. Save the habit. The dashboard shows the reminder time in the **REMINDER** column.

## Live presentation
Choose a reminder time about one to two minutes ahead of the current computer time. Keep the app open and the account signed in. The scheduler checks every 15 seconds; at the scheduled minute, a **Habit Reminder** popup displays the habit name and time. To demonstrate persistence, edit the habit again and show that the reminder setting is still saved.

## Limitations to explain honestly
- The app must remain open and the user must remain signed in.
- The reminder is a daily time reminder, not a weekday-specific or monthly calendar schedule.
- This implementation does not generate Windows notifications when the app is closed.
- If MySQL is temporarily unavailable, the scheduler logs the check failure and retries on a later poll rather than crashing the app.
