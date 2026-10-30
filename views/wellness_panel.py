"""Reusable compact Wellness Advisor panel for authenticated app screens."""

import logging
import tkinter as tk

from controllers.progress_controller import ProgressController, ProgressRepositoryError
from services.wellness_advisor import RuleBasedWellnessAdvisor

logger = logging.getLogger(__name__)


class WellnessPanel:
    """Show a small, refreshable wellness summary without replacing the page."""

    def __init__(self, parent, user, *, bg_color="#F3F9FA", card_color="#FFFFFF",
                 text_color="#0D2D48", muted_color="#58717D", primary_color="#078A9B"):
        self.user = dict(user) if isinstance(user, dict) else {}
        self.bg_color = bg_color
        self.card_color = card_color
        self.text_color = text_color
        self.muted_color = muted_color
        self.primary_color = primary_color
        self.advisor = RuleBasedWellnessAdvisor()
        self.panel = tk.Frame(parent, bg=card_color, highlightbackground="#DCE8EC",
                              highlightthickness=1)
        self.panel.pack(fill="x", padx=30, pady=(0, 14))

        header = tk.Frame(self.panel, bg=card_color)
        header.pack(fill="x", padx=15, pady=(9, 3))
        tk.Label(header, text="Wellness Advisor", font=("Arial", 12, "bold"),
                 fg=text_color, bg=card_color).pack(side="left")
        tk.Button(header, text="Refresh Advice", command=self.refresh,
                  bg="#E0F5F4", fg=primary_color, activebackground="#D2EEEE",
                  relief="flat", cursor="hand2", font=("Arial", 9)).pack(side="right", ipady=2, ipadx=7)

        body = tk.Frame(self.panel, bg=card_color)
        body.pack(fill="x", padx=15, pady=(0, 10))
        self.pattern_label = tk.Label(body, text="Loading recent habit pattern…",
                                      font=("Arial", 9, "bold"), fg=text_color,
                                      bg=card_color, anchor="w", justify="left",
                                      wraplength=330)
        self.pattern_label.pack(side="left", fill="x", expand=True, padx=(0, 15))
        self.advice_label = tk.Label(body, text="Loading a suggestion…", font=("Arial", 9),
                                     fg=muted_color, bg=card_color, anchor="w", justify="left",
                                     wraplength=450)
        self.advice_label.pack(side="left", fill="x", expand=True)
        self.refresh()

    @staticmethod
    def _pattern_text(report):
        if report is None:
            return "Recent habit pattern is unavailable. Check MySQL and refresh."
        total = int(report.get("total_habits", 0) or 0)
        recorded = int(report.get("recorded_days", 0) or 0)
        completed = int(report.get("completed_days", 0) or 0)
        rate = report.get("completion_rate", 0)
        if total == 0:
            return "No habits yet — start with one small, realistic habit."
        if recorded == 0:
            return f"{total} habit(s) saved, but no tracking records yet."
        return f"Last 30 days: {completed}/{recorded} recorded days completed ({rate}%)."

    def refresh(self):
        """Reload advice and update the panel in place."""
        try:
            user_id = self.user.get("user_id")
            if user_id is None:
                raise ValueError("No signed-in user is available.")
            report = ProgressController().get_report(int(user_id))
            recommendations = self.advisor.recommend(report)
            self.pattern_label.configure(text=self._pattern_text(report))
            if recommendations:
                item = recommendations[0]
                title = str(item.get("title", "A small next step"))
                message = str(item.get("message", "Keep your next habit step realistic and repeatable."))
                self.advice_label.configure(text=f"{title}: {message}")
            else:
                self.advice_label.configure(text="Choose one small habit and track it consistently.")
        except (ProgressRepositoryError, TypeError, ValueError) as exc:
            logger.warning("Unable to refresh compact wellness panel: %s", exc)
            self.pattern_label.configure(text="Recent habit pattern is unavailable.")
            self.advice_label.configure(text="Check that MySQL is running, then refresh advice.")
