# Change Log

## Wellness Advisor update

- Added `RuleBasedWellnessAdvisor` to derive up to three suggestions from a user's last-30-days MySQL progress report.
- Connected the active Wellness Advisor screen to the authenticated user's report and added a Refresh Suggestions control.
- Added six focused unit tests for the recommendation rules.
- Added a walkthrough to help the student explain the implementation during the project defense.
- No database schema or existing habit records were changed.

## Compact Wellness Advisor panel
- Added a reusable, compact Wellness Advisor panel to Dashboard, Habit Tracking, and Reports.
- Each panel shows the user's recent 30-day habit pattern and a data-driven suggestion.
- Added an in-place Refresh Advice action so suggestions can be refreshed without navigating away or rebuilding the page.
- Kept the full Wellness Advisor page available from the Dashboard sidebar.

## UI/UX finishing pass
- Added a subtle active-state highlight to the Dashboard, Habit Tracking, Reports, and Wellness Advisor sidebar links so users can tell which section is open.
- Kept the existing desktop layout, logo, colors, and feature behavior; no database schema or stored data changes.

## CSV numbering and Add Habit form fix
- Changed CSV export numbering to a user-facing sequence (`No. 1` through `No. N`) instead of exposing internal MySQL habit IDs that can contain gaps after deletions.
- Fixed Add/Edit Habit navigation to use the real top-level Tk window for window settings and the shared page container for UI widgets.
- Ensured the Cancel and successful Save/Update actions return to the dashboard without leaving a blank page.
- No MySQL primary keys, completion records, or database schema were changed.

## Delete Habit and CSV fixes
- Added a safe focused-row fallback for Delete Selected and validation that the target row still exists.
- Included the underlying database error detail in the Delete Failed dialog to support troubleshooting.
- Kept delete audit records concise while retaining the audit trail.
- CSV report rows use sequential display numbering (1..N), independently of MySQL primary keys.
- Fixed Add Habit page/window handling in the form view.

## Delete button visibility and delete-flow regression fix
- Reordered Dashboard panel layout so the bottom action bar is reserved before the habit table expands; Edit Selected and Delete Selected now remain visible at the supported minimum window size.
- Added regression tests for confirmed deletion, cancellation, focused-row fallback, and missing selection.
- Verified the action bar coordinates under a virtual display at 1120×740. The previous layout placed both action buttons at 1×1 pixels and unmapped; the corrected layout maps both buttons at the bottom of the panel.
- No database schema or stored data changed.


## Optional daily reminder feature
- Added persistent reminder time and enabled settings to habits (requires the included one-time MariaDB migration).
- Added a small Add/Edit Habit control for enabling a daily reminder and entering local 24-hour time.
- Added a single per-window scheduler that checks every 15 seconds, groups simultaneous due reminders, and avoids repeating the same habit reminder during the same day/minute.
- Reminders are in-app only and require the app to remain open and a user to remain signed in; no background or OS-level notifications are claimed.
- Added automated validation, repository, and deterministic scheduler tests.
