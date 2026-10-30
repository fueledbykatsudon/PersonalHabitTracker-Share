"""Application entry point for Personal Habit Tracker."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import tkinter as tk

from views.login_window import LoginWindow


def configure_logging():
    """Write diagnostic logs to a rotating file inside the project folder."""
    log_dir = Path(__file__).resolve().parent / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / "app.log"

    root_logger = logging.getLogger()
    if not any(
        isinstance(handler, RotatingFileHandler)
        and getattr(handler, "baseFilename", None) == str(log_file.resolve())
        for handler in root_logger.handlers
    ):
        handler = RotatingFileHandler(
            log_file, maxBytes=1_000_000, backupCount=3, encoding="utf-8"
        )
        handler.setFormatter(logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        ))
        root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)


def main():
    configure_logging()
    logger = logging.getLogger(__name__)
    root = tk.Tk()
    try:
        LoginWindow(root)
        root.mainloop()
    except Exception:
        logger.exception("Unhandled application startup/runtime exception")
        raise


if __name__ == "__main__":
    main()
