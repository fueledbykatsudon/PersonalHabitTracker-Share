# Navigation Flicker Fix

This update introduces `views/navigation.py`, a persistent content frame for authenticated pages. Dashboard, My Habits, Habit Tracking, Reports, Wellness Advisor, and Admin screens now replace widgets inside that frame instead of clearing the Tk root window itself. This keeps the top-level window stable during navigation and standardizes authenticated page dimensions at 1120x740 (minimum 1000x650).

## Test
1. Start XAMPP MySQL/MariaDB.
2. Run the app as usual using your existing Python environment.
3. Sign in, then switch between Dashboard, My Habits, Habit Tracking, Reports, and Wellness Advisor several times.
4. Confirm the top-level window remains the same size and the navigation sidebar/content redraws without a window resize.

This was syntax-checked. The full unit-test suite could not be completed in the build environment because `mysql-connector-python` is not installed here; the repository/database tests require that dependency.
