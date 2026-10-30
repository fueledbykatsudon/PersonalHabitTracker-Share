"""Database-backed progress report with CSV export."""

import csv
from datetime import datetime
from tkinter import filedialog, messagebox, ttk
import tkinter as tk

from controllers.progress_controller import ProgressController, ProgressRepositoryError


from views.navigation import get_page_container, clear_page

class ReportsView:
    def __init__(self, root, user):
        self.window = root
        self.root = get_page_container(root)
        self.user = user
        self.repository = ProgressController()
        self.report_data = None
        self.bg = "#F3F9FA"
        self.sidebar_color = "#123B5D"
        self.primary = "#078A9B"
        self.card = "#FFFFFF"
        self.text = "#0D2D48"
        self.muted = "#58717D"

        self._clear_window()
        self.window.title("Personal Habit Tracker - Reports")
        self.window.geometry("1120x740")
        self.window.minsize(1000, 650)
        self.window.configure(bg=self.bg)
        self._build_sidebar()
        self._build_content()
        self.refresh()

    def _clear_window(self):
        clear_page(self.root)

    def _build_sidebar(self):
        sidebar = tk.Frame(self.root, bg=self.sidebar_color, width=220)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        from pathlib import Path
        logo_path = Path(__file__).resolve().parent.parent / "assets" / "pht_logo_sidebar.png"
        self.logo_image = tk.PhotoImage(file=str(logo_path))
        tk.Label(sidebar, image=self.logo_image, bg=self.sidebar_color,
                 borderwidth=0).pack(pady=(18, 18))
        self._nav(sidebar, "Dashboard", self.open_dashboard)
        self._nav(sidebar, "My Habits", self.open_habits)
        self._nav(sidebar, "Habit Tracking", self.open_tracking)
        self._nav(sidebar, "Reports", self.refresh, active=True)
        self._nav(sidebar, "Wellness Advisor", self.open_wellness)
        if self.user.get("role_name") == "Admin":
            self._nav(sidebar, "User & Audit Logs", self.open_admin)
        tk.Frame(sidebar, bg=self.sidebar_color).pack(fill="both", expand=True)
        info = tk.Frame(sidebar, bg="#0D2D48")
        info.pack(fill="x", padx=12, pady=(0, 10))
        tk.Label(info, text=self.user.get("full_name", "User"), font=("Arial", 10, "bold"),
                 fg="white", bg="#0D2D48", wraplength=180, justify="left").pack(
                     anchor="w", padx=10, pady=(10, 2))
        tk.Label(info, text=f"@{self.user.get('username', '')}", font=("Arial", 9),
                 fg="#A9C4CC", bg="#0D2D48").pack(anchor="w", padx=10, pady=(0, 10))
        tk.Button(sidebar, text="Logout", command=self.logout, font=("Arial", 10, "bold"),
                  fg="white", bg="#1B4B69", activebackground="#24617D", relief="flat",
                  bd=0, cursor="hand2").pack(fill="x", padx=18, pady=(0, 20), ipady=8)

    def _nav(self, parent, text, command, active=False):
        """Build a consistent sidebar link and identify the current section."""
        background = "#1B4B69" if active else self.sidebar_color
        foreground = "white" if active else "#D9F0F0"
        tk.Button(
            parent, text=text, command=command,
            font=("Arial", 10, "bold" if active else "normal"), anchor="w",
            fg=foreground, bg=background, activebackground="#24617D",
            activeforeground="white", relief="flat", bd=0, cursor="hand2",
            padx=20,
        ).pack(fill="x", padx=12, pady=3, ipady=9)

    def _build_content(self):
        content = tk.Frame(self.root, bg=self.bg)
        content.pack(side="left", fill="both", expand=True)
        tk.Label(content, text="Reports & Progress", font=("Arial", 22, "bold"),
                 fg=self.text, bg=self.bg).pack(anchor="w", padx=30, pady=(24, 3))
        tk.Label(content, text="Your recorded habit activity over the last 30 days.",
                 font=("Arial", 10), fg=self.muted, bg=self.bg).pack(
                     anchor="w", padx=30, pady=(0, 17))

        cards = tk.Frame(content, bg=self.bg)
        cards.pack(fill="x", padx=30, pady=(0, 17))
        self.metric_values = {}
        for col, key, title in [
            (0, "total_habits", "Total Habits"),
            (1, "completed_days", "Recorded Completed Days"),
            (2, "recorded_days", "Recorded Habit-Days"),
            (3, "completion_rate", "Recorded Completion Rate"),
        ]:
            cards.grid_columnconfigure(col, weight=1)
            box = tk.Frame(cards, bg=self.card, highlightbackground="#DCE8EC", highlightthickness=1)
            box.grid(row=0, column=col, sticky="nsew", padx=(0, 9))
            tk.Label(box, text=title, font=("Arial", 8), fg=self.muted, bg=self.card,
                     wraplength=155).pack(anchor="w", padx=11, pady=(12, 3))
            value = tk.Label(box, text="—", font=("Arial", 19, "bold"), fg=self.text, bg=self.card)
            value.pack(anchor="w", padx=11, pady=(0, 12))
            self.metric_values[key] = value

        from views.wellness_panel import WellnessPanel
        self.wellness_panel = WellnessPanel(
            content, self.user, bg_color=self.bg, card_color=self.card,
            text_color=self.text, muted_color=self.muted, primary_color=self.primary,
        )

        panel = tk.Frame(content, bg=self.card, highlightbackground="#DCE8EC", highlightthickness=1)
        panel.pack(fill="both", expand=True, padx=30, pady=(0, 24))
        toolbar = tk.Frame(panel, bg=self.card)
        toolbar.pack(fill="x", padx=18, pady=(15, 10))
        tk.Label(toolbar, text="Per-Habit Summary", font=("Arial", 14, "bold"), fg=self.text,
                 bg=self.card).pack(side="left")
        tk.Button(toolbar, text="Refresh", command=self.refresh, bg="#EDF4F5", fg=self.text,
                  relief="flat", cursor="hand2").pack(side="right", padx=(8, 0), ipadx=8, ipady=5)
        tk.Button(toolbar, text="Export CSV", command=self.export_csv, bg=self.primary, fg="white",
                  activebackground="#067784", relief="flat", cursor="hand2").pack(
                      side="right", ipadx=10, ipady=5)

        frame = tk.Frame(panel, bg=self.card)
        frame.pack(fill="both", expand=True, padx=18, pady=(0, 10))
        columns = ("habit_name", "category", "recorded_days", "completed_days", "last_tracked")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")
        headers = {
            "habit_name": ("Habit", 230, "w"),
            "category": ("Category", 135, "w"),
            "recorded_days": ("Recorded Days", 105, "center"),
            "completed_days": ("Completed", 100, "center"),
            "last_tracked": ("Last Tracked", 140, "center"),
        }
        for key, (label, width, anchor) in headers.items():
            self.tree.heading(key, text=label)
            self.tree.column(key, width=width, minwidth=80, anchor=anchor)
        scroll = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.note = tk.Label(panel,
            text="Completion rate = completed recorded habit-days ÷ all recorded habit-days in the last 30 days. Unrecorded days are excluded.",
            font=("Arial", 8), fg=self.muted, bg=self.card, wraplength=810, justify="left")
        self.note.pack(anchor="w", padx=18, pady=(0, 13))
        self.status = tk.Label(content, text="", font=("Arial", 9), fg=self.muted, bg=self.bg)
        self.status.pack(anchor="w", padx=30, pady=(0, 8))

    def refresh(self):
        try:
            report = self.repository.get_report(self.user["user_id"])
            self.report_data = report
            for key in ("total_habits", "completed_days", "recorded_days"):
                self.metric_values[key].configure(text=str(report[key]))
            self.metric_values["completion_rate"].configure(text=f"{report['completion_rate']}%")
            for item in self.tree.get_children():
                self.tree.delete(item)
            for row in report["rows"]:
                last_tracked = row.get("last_tracked")
                if hasattr(last_tracked, "strftime"):
                    last_tracked = last_tracked.strftime("%Y-%m-%d")
                else:
                    last_tracked = str(last_tracked or "—")
                self.tree.insert("", "end", iid=str(row["habit_id"]), values=(
                    row["habit_name"], row["category"] or "—", row["recorded_days"],
                    row["completed_days"], last_tracked,
                ))
            self.status.configure(text=f"Report refreshed. {report['total_habits']} habit(s) included.")
        except ProgressRepositoryError as exc:
            self.status.configure(text="Could not load report")
            messagebox.showerror("Report Error", str(exc), parent=self.root)

    def export_csv(self):
        if self.report_data is None:
            self.refresh()
        if self.report_data is None:
            return
        path = filedialog.asksaveasfilename(
            parent=self.root,
            title="Export Habit Report",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile=f"habit_report_{datetime.now():%Y%m%d}.csv",
        )
        if not path:
            return
        try:
            with open(path, "w", newline="", encoding="utf-8-sig") as file:
                writer = csv.writer(file)
                writer.writerow(["Personal Habit Tracker & Wellness Advisor"])
                writer.writerow(["Generated At", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
                writer.writerow(["Period", "Last 30 days"])
                writer.writerow(["Total Habits", self.report_data["total_habits"]])
                writer.writerow(["Completed Recorded Days", self.report_data["completed_days"]])
                writer.writerow(["Recorded Habit-Days", self.report_data["recorded_days"]])
                writer.writerow(["Recorded Completion Rate", f"{self.report_data['completion_rate']}%"])
                writer.writerow([])
                # Use an export row number for people reading the report.
                # Database IDs are internal keys and are intentionally not
                # exposed as list numbering because deleted rows leave gaps.
                writer.writerow(["No.", "Habit", "Category", "Recorded Days",
                                 "Completed Days", "Last Tracked"])
                for number, row in enumerate(self.report_data["rows"], start=1):
                    last_tracked = row.get("last_tracked") or ""
                    if hasattr(last_tracked, "strftime"):
                        last_tracked = last_tracked.strftime("%Y-%m-%d")
                    writer.writerow([
                        number, row["habit_name"], row["category"],
                        row["recorded_days"], row["completed_days"], last_tracked,
                    ])
            messagebox.showinfo("Export Complete", f"Report exported successfully to:\n{path}", parent=self.root)
        except OSError as exc:
            messagebox.showerror("Export Failed", f"Could not write the report file.\n{exc}", parent=self.root)

    def open_dashboard(self):
        from views.dashboard_window import DashboardWindow
        DashboardWindow(self.window, self.user)

    def open_habits(self):
        from views.dashboard_window import DashboardWindow
        dashboard = DashboardWindow(self.window, self.user)
        self.window.after(100, dashboard.focus_search)

    def open_tracking(self):
        from views.tracking_view import TrackingView
        TrackingView(self.window, self.user)

    def open_wellness(self):
        from views.wellness_view import WellnessView
        WellnessView(self.window, self.user)

    def open_admin(self):
        if self.user.get("role_name") != "Admin":
            messagebox.showerror("Access Denied", "Administrator permission is required.", parent=self.root)
            return
        from views.admin_users_view import AdminUsersView
        AdminUsersView(self.window, self.user)

    def logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to logout?", parent=self.root):
            from services.reminder_scheduler import stop_window_reminder_scheduler
            stop_window_reminder_scheduler(self.window)
            from views.login_window import LoginWindow
            LoginWindow(self.window)
