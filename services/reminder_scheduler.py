"""In-app daily reminder scheduler for the signed-in user.

Reminders are checked only while the Tkinter application is running. A reminder
is shown once per habit/time/date, even though the scheduler polls repeatedly.
"""

from __future__ import annotations

from datetime import datetime
import logging
from tkinter import messagebox

from controllers.habit_controller import HabitController, HabitRepositoryError

logger = logging.getLogger(__name__)


class ReminderScheduler:
    """Poll enabled reminder records and display due reminders using Tkinter."""

    def __init__(
        self,
        root,
        user_id: int,
        controller=None,
        notifier=None,
        clock=None,
        interval_ms: int = 15_000,
    ):
        self.root = root
        self.user_id = int(user_id)
        self.controller = controller or HabitController()
        self.notifier = notifier or self._show_notification
        self.clock = clock or datetime.now
        self.interval_ms = max(1_000, int(interval_ms))
        self._running = False
        self._after_id = None
        self._notified: set[tuple[str, int, str]] = set()

    @property
    def running(self) -> bool:
        return self._running

    def start(self) -> None:
        """Start polling unless already running."""
        if self._running:
            return
        self._running = True
        self._schedule(1_000)

    def stop(self) -> None:
        """Cancel the pending Tk callback, usually on logout."""
        self._running = False
        if self._after_id is not None:
            try:
                self.root.after_cancel(self._after_id)
            except Exception:
                # The window may already be closing; stop should remain safe.
                pass
            self._after_id = None

    def check_due_now(self) -> list[dict]:
        """Check the current minute and notify once for each matching reminder.

        Public to allow deterministic tests without running Tk's event loop.
        """
        now = self.clock()
        today = now.date().isoformat()
        current_time = now.strftime("%H:%M")
        # Keep deduplication memory bounded to the current day.
        self._notified = {key for key in self._notified if key[0] == today}
        rows = self.controller.list_enabled_reminders(self.user_id)
        candidates = []
        for row in rows:
            reminder_time = str(row.get("reminder_time") or "")[:5]
            if reminder_time != current_time:
                continue
            habit_id = int(row["habit_id"])
            key = (today, habit_id, reminder_time)
            if key in self._notified:
                continue
            candidates.append({**row, "reminder_time": reminder_time})

        if not candidates:
            return []

        # Persist first, then notify only newly recorded events. The database's
        # unique key also prevents duplicates after the application restarts.
        due = self.controller.record_due_reminders(
            self.user_id, candidates, today, current_time
        )
        for row in due:
            self._notified.add((today, int(row["habit_id"]), current_time))
        if due:
            self.notifier(due)
        return due

    def _schedule(self, delay_ms: int) -> None:
        if not self._running:
            return
        try:
            self._after_id = self.root.after(delay_ms, self._tick)
        except Exception:
            self._running = False
            self._after_id = None
            logger.debug("Reminder scheduler stopped because its Tk window is unavailable.", exc_info=True)

    def _tick(self) -> None:
        self._after_id = None
        if not self._running:
            return
        try:
            self.check_due_now()
        except HabitRepositoryError:
            # A temporary DB outage should not crash the app or flood the user
            # with modal errors. The scheduler will retry on the next poll.
            logger.exception("Could not check scheduled reminders for user_id=%s", self.user_id)
        except Exception:
            logger.exception("Unexpected reminder scheduler error for user_id=%s", self.user_id)
        finally:
            if self._running:
                self._schedule(self.interval_ms)

    def _show_notification(self, reminders: list[dict]) -> None:
        lines = [
            f"• {item['habit_name']}  ({item['reminder_time']})"
            for item in reminders
        ]
        count = len(lines)
        title = "Habit Reminder" if count == 1 else "Habit Reminders"
        message = "It's time for your scheduled habit:" if count == 1 else "It's time for your scheduled habits:"
        messagebox.showinfo(title, message + "\n\n" + "\n".join(lines), parent=self.root)


def stop_window_reminder_scheduler(window) -> None:
    """Stop and remove the active per-window scheduler, especially on logout."""
    scheduler = getattr(window, "_pht_reminder_scheduler", None)
    if scheduler is None:
        return
    scheduler.stop()
    try:
        delattr(window, "_pht_reminder_scheduler")
    except AttributeError:
        pass
