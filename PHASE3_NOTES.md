# Phase 3 — Habit Tracking, Reports, and Wellness Suggestions

## Implemented in this package

- `ProgressRepository` retrieves user-scoped daily tracking, records completion/reset transactions, and generates a last-30-days report.
- Completion/reset operations update `habit_completions` and write matching audit records in the same transaction.
- The active dashboard displays MySQL-backed habit records and summary metrics.
- Reports show a per-habit summary and can be exported to CSV.
- The Wellness Advisor now reads the signed-in user's report data and produces three explainable rule-based suggestions. Examples include starting with one habit when none exist, building a baseline when few records exist, celebrating strong recorded consistency, and simplifying a habit with a lower recorded completion rate.
- The advisor intentionally uses ordinary Python rules rather than an AI model. Its output can be traced back to the report values and is general habit-building guidance, not medical advice.
- Unit tests cover the recommendation rules, including no habits, no tracking history, strong completion, low completion, limited observations, and malformed report values.

## Report metric definition

The report's completion rate is completed recorded habit-days divided by all recorded habit-days in the last 30 days. Days with no `habit_completions` row are excluded from the denominator. The UI labels this metric as a recorded completion rate to avoid implying that untracked days were failures.

## Manual validation still required

On the local XAMPP database, verify that the Wellness Advisor displays advice derived from the currently signed-in user's own habits, that Refresh Suggestions reloads the data, and that the screen reports a clear message if the database is unavailable. Also repeat the report/CSV check after tracking a completion and after resetting it.
