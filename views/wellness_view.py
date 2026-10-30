"""Wellness Advisor screen using the signed-in user's recorded progress."""

import logging
import tkinter as tk
from controllers.progress_controller import ProgressController, ProgressRepositoryError
from services.wellness_advisor import RuleBasedWellnessAdvisor

logger = logging.getLogger(__name__)


from views.navigation import get_page_container, clear_page

class WellnessView:
    """Show simple, explainable suggestions based on the user's last 30 days."""

    def __init__(self, root, user):
        self.window = root
        self.root = get_page_container(root)
        self.user = dict(user) if isinstance(user, dict) else {}
        self.advisor = RuleBasedWellnessAdvisor()
        self.report_data = None
        self.recommendations = []
        self.refresh_count = 0
        self.pattern_label = None
        self.advice_frame = None

        self.window.title("Personal Habit Tracker - Wellness Advisor")
        self.window.geometry("1120x740")
        self.window.minsize(1000, 650)
        self.window.resizable(True, True)
        self.window.configure(bg="#F3F9FA")

        self.show_wellness()

    def clear_screen(self):
        clear_page(self.root)

    def _load_advice(self):
        """Load this user's report and convert it into transparent rule-based advice."""
        user_id = self.user.get("user_id")
        if user_id is None:
            self.report_data = None
            self.recommendations = [{
                "title": "Personalized advice unavailable",
                "message": "Sign in to view suggestions based on your own habit history.",
            }]
            return

        try:
            self.report_data = ProgressController().get_report(int(user_id))
            self.recommendations = self.advisor.recommend(self.report_data)
        except (ProgressRepositoryError, TypeError, ValueError) as exc:
            logger.exception("Unable to load wellness advice for user_id=%s", user_id)
            self.report_data = None
            self.recommendations = [{
                "title": "Your activity could not be loaded",
                "message": (
                    "We could not read your recent habit records. Check that MySQL "
                    "is running, then select Refresh Suggestions to try again."
                ),
            }]

    def show_wellness(self):
        self._load_advice()
        self.clear_screen()
        self.create_sidebar()

        content = tk.Frame(self.root, bg="#F3F9FA")
        content.pack(side="right", fill="both", expand=True)

        tk.Label(
            content,
            text="Wellness Advisor",
            font=("Arial", 27, "bold"),
            bg="#F3F9FA",
            fg="#123B5D",
        ).pack(anchor="w", padx=40, pady=(35, 5))

        tk.Label(
            content,
            text="Practical suggestions based on your recorded habit progress.",
            font=("Arial", 11),
            bg="#F3F9FA",
            fg="#58717D",
        ).pack(anchor="w", padx=40, pady=(0, 25))

        pattern = tk.Frame(content, bg="white", height=150)
        pattern.pack(fill="x", padx=40)
        pattern.pack_propagate(False)

        pattern_header = tk.Frame(pattern, bg="white")
        pattern_header.pack(fill="x", padx=25, pady=(20, 8))
        tk.Label(
            pattern_header,
            text="Your Recent Habit Pattern",
            font=("Arial", 17, "bold"),
            bg="white",
            fg="#123B5D",
        ).pack(side="left")
        tk.Button(
            pattern_header,
            text="Refresh Suggestions",
            command=self.refresh_suggestions,
            font=("Arial", 9, "bold"),
            bg="#123B5D",
            fg="white",
            activebackground="#1B4B69",
            activeforeground="white",
            relief="flat",
            cursor="hand2",
        ).pack(side="right", ipadx=7, ipady=4)

        if self.report_data is None:
            pattern_text = "Your recent activity is currently unavailable. Refresh after checking the database connection."
        elif self.report_data["total_habits"] == 0:
            pattern_text = "You have not added any habits yet. Start with one realistic habit that supports a goal you care about."
        elif self.report_data["recorded_days"] == 0:
            pattern_text = (
                f"You have {self.report_data['total_habits']} habit(s), but no "
                "recorded habit-days in the last 30 days. Record today's status "
                "in Habit Tracking to build a useful baseline."
            )
        else:
            report = self.report_data
            pattern_text = (
                f"Last 30 days: {report['total_habits']} habit(s), "
                f"{report['completed_days']} completed out of {report['recorded_days']} "
                f"recorded habit-days ({report['completion_rate']}%)."
            )

        self.pattern_label = tk.Label(
            pattern,
            text=pattern_text,
            font=("Arial", 11),
            bg="white",
            fg="#58717D",
            wraplength=710,
            justify="left",
        )
        self.pattern_label.pack(anchor="w", padx=25, pady=(0, 14))

        tk.Label(
            content,
            text="Suggestions for You",
            font=("Arial", 18, "bold"),
            bg="#F3F9FA",
            fg="#123B5D",
        ).pack(anchor="w", padx=40, pady=(25, 15))

        self.advice_frame = tk.Frame(content, bg="#F3F9FA")
        self.advice_frame.pack(fill="x", padx=40)
        self._render_advice_cards()

        note = tk.Frame(content, bg="white", height=83)
        note.pack(fill="x", padx=40, pady=25)
        note.pack_propagate(False)
        tk.Label(
            note,
            text=(
                "How it works: these suggestions use transparent rules and your "
                "last 30 days of recorded habit data. They are general habit-building "
                "ideas, not medical advice."
            ),
            font=("Arial", 9),
            bg="white",
            fg="#58717D",
            wraplength=720,
            justify="left",
        ).pack(anchor="w", padx=25, pady=23)

    def _get_pattern_text(self):
        """Build the recent-pattern summary from the latest database report."""
        report = self.report_data
        if report is None:
            return "Your recent activity is currently unavailable. Check the database connection, then refresh suggestions."
        if report.get("total_habits", 0) == 0:
            return "You have not added any habits yet. Start with one realistic habit that supports a goal you care about."
        if report.get("recorded_days", 0) == 0:
            return (
                f"You have {report.get('total_habits', 0)} habit(s), but no "
                "recorded habit-days in the last 30 days. Record today's status "
                "in Habit Tracking to build a useful baseline."
            )
        return (
            f"Last 30 days: {report.get('total_habits', 0)} habit(s), "
            f"{report.get('completed_days', 0)} completed out of "
            f"{report.get('recorded_days', 0)} recorded habit-days "
            f"({report.get('completion_rate', 0)}%)."
        )

    def _visible_recommendations(self):
        """Keep advice grounded in the report while rotating practical next steps."""
        recommendations = list(self.recommendations)
        report = self.report_data or {}
        total_habits = int(report.get("total_habits", 0) or 0)
        recorded_days = int(report.get("recorded_days", 0) or 0)
        try:
            completion_rate = int(report.get("completion_rate", 0) or 0)
        except (TypeError, ValueError):
            completion_rate = 0

        if total_habits == 0:
            alternatives = [
                ("Choose a tiny starting point", "Pick an action that takes two minutes or less. Making the first step easy helps you begin."),
                ("Attach it to an existing routine", "Connect your new habit to something you already do, such as after breakfast or before bed."),
                ("Keep your first goal realistic", "Start with one habit you genuinely want to build. Add more only when the first feels manageable."),
            ]
        elif recorded_days == 0:
            alternatives = [
                ("Make tracking part of your day", "Choose a regular time to record whether you completed each habit. A quick daily check-in builds a useful history."),
                ("Start with today's record", "Open Habit Tracking and record the status of one habit today. You do not need a perfect streak to begin."),
                ("Use a simple reminder", "Set a reminder at a time you are usually available, then record your habit soon after the planned activity."),
            ]
        elif completion_rate >= 80:
            alternatives = [
                ("Protect the routine that works", "Notice the time and situation that help you stay consistent, and try to keep that cue in place."),
                ("Increase difficulty gradually", "If your current routine feels comfortable, make only a small increase rather than changing several habits at once."),
                ("Review your wins weekly", "Look back at the habits you completed most often and identify what made them easier to maintain."),
            ]
        elif completion_rate < 50:
            alternatives = [
                ("Shrink the next step", "Make the habit easier to start—for example, read one page instead of a whole chapter or take a short walk."),
                ("Choose a more reliable cue", "Tie the habit to a specific event in your day, such as after lunch, instead of relying on memory alone."),
                ("Prepare before the moment", "Put what you need in a visible, convenient place so there are fewer steps between you and starting."),
            ]
        else:
            alternatives = [
                ("Spot what helps you follow through", "Think about which days or routines make completion easier, then repeat those conditions when possible."),
                ("Plan a minimum version", "Decide on a small version of your habit for busy days so you can keep the routine flexible."),
                ("Make the cue specific", "Choose a clear time or daily event for your habit to make it easier to remember and repeat."),
            ]

        if not recommendations:
            recommendations = []
        # Keep the first two data-driven recommendations and rotate the third card.
        # This changes the practical advice on each refresh without inventing new data.
        rotation = (self.refresh_count - 1) % len(alternatives)
        title, message = alternatives[rotation]
        dynamic = {"title": title, "message": message}
        if len(recommendations) >= 3:
            recommendations[2] = dynamic
        else:
            recommendations.append(dynamic)
        return recommendations[:3]

    def _render_advice_cards(self):
        if self.advice_frame is None or not self.advice_frame.winfo_exists():
            return
        for widget in self.advice_frame.winfo_children():
            widget.destroy()
        for column, recommendation in enumerate(self._visible_recommendations()):
            self.create_advice_card(
                self.advice_frame,
                recommendation["title"],
                recommendation["message"],
                column,
            )

    def refresh_suggestions(self):
        """Refresh data and update only the advice area, avoiding a full-screen blink."""
        self.refresh_count += 1
        self._load_advice()
        if self.pattern_label is not None and self.pattern_label.winfo_exists():
            self.pattern_label.configure(text=self._get_pattern_text())
        self._render_advice_cards()

    def open_wellness(self):
        """If already on this page, refresh it in place instead of rebuilding the window."""
        if self.advice_frame is not None and self.advice_frame.winfo_exists():
            self.refresh_suggestions()
        else:
            self.show_wellness()

    def create_sidebar(self):
        sidebar = tk.Frame(self.root, bg="#123B5D", width=220)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # Use the same aspect-preserving logo as other authenticated screens.
        from pathlib import Path
        logo_path = Path(__file__).resolve().parent.parent / "assets" / "pht_logo_sidebar.png"
        self.logo_image = tk.PhotoImage(file=str(logo_path))
        tk.Label(sidebar, image=self.logo_image, bg="#123B5D",
                 borderwidth=0).pack(pady=(18, 18))

        self.menu_button(sidebar, "Dashboard", self.go_dashboard)
        self.menu_button(sidebar, "My Habits", self.go_habits)
        self.menu_button(sidebar, "Habit Tracking", self.go_tracking)
        self.menu_button(sidebar, "Reports", self.go_reports)
        self.menu_button(sidebar, "Wellness Advisor", self.open_wellness, active=True)

        tk.Button(
            sidebar,
            text="Logout",
            font=("Arial", 11, "bold"),
            bg="#123B5D",
            fg="white",
            activebackground="#1B4B69",
            activeforeground="white",
            relief="flat",
            anchor="w",
            padx=25,
            cursor="hand2",
            command=self.logout,
        ).pack(side="bottom", fill="x", ipady=10, pady=20, padx=12)

    def menu_button(self, parent, text, command, active=False):
        """Use the same restrained active-state styling as other app pages."""
        tk.Button(
            parent,
            text=text,
            font=("Arial", 11, "bold" if active else "normal"),
            bg="#1B4B69" if active else "#123B5D",
            fg="white",
            activebackground="#24617D",
            activeforeground="white",
            relief="flat",
            anchor="w",
            padx=25,
            cursor="hand2",
            command=command,
        ).pack(fill="x", ipady=10, padx=(8, 0) if active else 0)

    @staticmethod
    def create_advice_card(parent, title, text, column):
        card = tk.Frame(parent, bg="white", width=225, height=160)
        card.grid(row=0, column=column, padx=(0, 15), sticky="n")
        card.grid_propagate(False)

        tk.Label(
            card,
            text=title,
            font=("Arial", 13, "bold"),
            bg="white",
            fg="#078A9B",
            wraplength=190,
            justify="left",
        ).pack(anchor="w", padx=16, pady=(16, 8))
        tk.Label(
            card,
            text=text,
            font=("Arial", 9),
            bg="white",
            fg="#58717D",
            wraplength=190,
            justify="left",
        ).pack(anchor="w", padx=16)

    def go_dashboard(self):
        from views.dashboard_window import DashboardWindow
        DashboardWindow(self.window, self.user)

    def go_habits(self):
        from views.dashboard_window import DashboardWindow
        dashboard = DashboardWindow(self.window, self.user)
        self.window.after(100, dashboard.focus_search)

    def go_tracking(self):
        from views.tracking_view import TrackingView
        TrackingView(self.window, self.user)

    def go_reports(self):
        from views.reports_view import ReportsView
        ReportsView(self.window, self.user)

    def logout(self):
        from services.reminder_scheduler import stop_window_reminder_scheduler
        stop_window_reminder_scheduler(self.window if hasattr(self, "window") else self.root)
        from views.login_window import LoginWindow
        self.clear_screen()
        LoginWindow(self.window)
