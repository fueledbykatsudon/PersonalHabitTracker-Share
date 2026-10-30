# Personal Habit Tracker — Phase 2 Notes

This is an incremental update on top of the Phase 1 authentication repair. It is not the complete SDF04 capstone submission yet.

## Included in this phase

- Replaced the active `DashboardWindow` habit list with a `ttk.Treeview` records display.
- Added database-backed search across habit name, category, description, and frequency.
- Added working repository methods for listing, summary counts, create, update, and delete operations using parameterized MySQL statements.
- Scoped each habit list/update/delete operation to the authenticated owner's `user_id`.
- Logged `CREATE_HABIT`, `UPDATE_HABIT`, and `DELETE_HABIT` actions in `audit_logs` in the same transaction as each habit mutation.
- Added input validation and clear repository error messages.
- Improved the dashboard's summary values based on the MySQL `habits` and `habit_completions` tables.
- Added automated tests for habit validation and repository behaviors. Together with the Phase 1 password tests, 18 unit tests pass in the development environment.
- Python syntax compilation succeeds for all project files.

## Important behavior

The current SQL schema does not specify `ON DELETE CASCADE` for `habit_completions.habit_id`. Therefore, deleting a habit first deletes its dependent completion history, then the habit, and then records the audit event, all before committing the transaction. The UI warns the user about deletion of completion history.

The database currently has roles named `Admin` and `User`. The authentication repair treats `User` as the Standard User permission set without requiring a database rename.

## How to run

1. Start MySQL in XAMPP and ensure database `personal_habit_tracker` exists.
2. Activate the project virtual environment.
3. Install packages with `python -m pip install -r requirements.txt`.
4. Run tests with `python -m unittest discover -s tests -v`.
5. Launch with `python main.py`.

The current development environment ran the automated tests using mocks for repository database interactions; live MySQL CRUD/audit behavior still needs to be confirmed on the user's XAMPP setup.

## Still incomplete for SDF04

- Database-backed habit completion UI and operations.
- Real reports and CSV export.
- Rule-based wellness recommendations based on recorded progress.
- Dedicated repositories for each major entity and a fuller MVC/controller separation.
- Required abstract base class and at least two concrete subclasses overriding methods, with exercised polymorphism.
- Property-based encapsulation for sensitive model attributes.
- Custom exceptions used consistently and rotating file logging.
- Broader end-to-end and database integration tests.
- Git commit history, final SQL export/sample data, flowchart, DFD L0-L2, UML class diagram, ERD, user manual, screenshots, and final ZIP package.

## Phase 2.1 verification (user-tested)
The user reported that login opened the dashboard successfully and manually tested the core habit CRUD and audit logging flow, confirming that it worked on their XAMPP installation.
