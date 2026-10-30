# Phase 2.1 — Login / Dashboard Diagnostics

This incremental update does not change the MySQL schema. It improves visibility when login or dashboard startup fails.

- The login form displays `Checking account...` when the button callback runs.
- Invalid credentials and database connection errors display user-facing messages.
- Unexpected authentication or dashboard initialization exceptions are logged and displayed instead of failing silently.
- A rotating log is created at `logs/app.log` after launching `python main.py`.
- If dashboard creation fails after credentials are accepted, the login form is restored.

## Run from the correct folder

Open the extracted project folder containing `main.py`, then use the VS Code terminal:

```powershell
python -m pip install -r requirements.txt
python main.py
```

The Windows folder name may contain spaces; that alone does not prevent the imports in this project. Launching from the project folder is important so Python loads this copy's files.
