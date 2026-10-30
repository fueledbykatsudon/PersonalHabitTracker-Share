# Personal Habit Tracker — Phase 1 Repair Notes

This package is an incremental repair of the uploaded project, not the complete SDF04 submission yet.

## Included in this phase

- Login checks the MySQL `users` and `roles` tables rather than opening the dashboard unconditionally.
- User registration writes to the existing `users` table using its `full_name`, `username`, `password_hash`, and `role_id` columns.
- New passwords use salted PBKDF2-HMAC-SHA256 hashes.
- Existing 64-character legacy SHA-256 hashes are accepted for a successful login and upgraded to PBKDF2 on that login.
- The existing database uses role names `Admin` and `User`; `User` is treated as the Standard User permission set in the GUI.
- The authenticated user dictionary is passed to the database-backed dashboard.
- An Admin-only screen can view registered accounts and the latest audit records, without displaying password hashes.
- Six unit tests cover password hashing and legacy-hash behavior.
- `requirements.txt` lists `mysql-connector-python`.

## Run locally

1. Start MySQL in XAMPP and verify the database name `personal_habit_tracker` exists.
2. Open a terminal in this folder.
3. Create/activate a virtual environment if needed.
4. Install dependencies: `python -m pip install -r requirements.txt`.
5. Run unit tests: `python -m unittest discover -s tests -v`.
6. Start the app: `python main.py`.

The database manager currently uses the default local XAMPP configuration (`localhost`, `root`, blank password). Change those settings only if your own MySQL credentials differ.

## Still incomplete — do not consider the project finished

The remaining SDF04 work includes wiring all GUI modules, persistent habit CRUD and search in the main flow, completion tracking, real reports and CSV export, wellness logic, audit logging for every add/edit/delete, explicit role-based admin actions, abstract base class and two concrete overriding subclasses, property-based encapsulation, exercised polymorphism, repository/DAO classes, custom exceptions, rotating file logs, broader unit tests, Git history, final diagram consistency, user manual, and SQL/sample-data export.

Live database behavior must be verified on the user's XAMPP installation. The automated tests in this package do not require a MySQL server.
