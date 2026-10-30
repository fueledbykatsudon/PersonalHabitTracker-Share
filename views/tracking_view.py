"""Authenticated daily completion tracking screen."""

import tkinter as tk
from tkinter import messagebox, ttk

from controllers.progress_controller import ProgressController, ProgressRepositoryError


from views.navigation import get_page_container, clear_page

class TrackingView:
    def __init__(self, root, user):
        self.window = root
        self.root = get_page_container(root)
        self.user = user
        self.repository = ProgressController()
        self.bg = "#F3F9FA"
        self.sidebar_color = "#123B5D"
        self.primary = "#078A9B"
        self.card = "#FFFFFF"
        self.text = "#0D2D48"
        self.muted = "#58717D"
        self.rows_by_id = {}

        self.clear_window()
        self.window.title("Personal Habit Tracker - Habit Tracking")
        self.window.geometry("1120x740")
        self.window.minsize(1000, 650)
        self.window.configure(bg=self.bg)
        self._build_sidebar()
        self._build_content()
        self.refresh()

    def clear_window(self):
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
        self._nav(sidebar, "Habit Tracking", self.refresh, active=True)
        self._nav(sidebar, "Reports", self.open_reports)
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
        tk.Label(content, text="Habit Tracking", font=("Arial", 22, "bold"),
                 fg=self.text, bg=self.bg).pack(anchor="w", padx=30, pady=(24, 3))
        tk.Label(content, text="Record each habit's status for today.", font=("Arial", 10),
                 fg=self.muted, bg=self.bg).pack(anchor="w", padx=30, pady=(0, 17))

        cards = tk.Frame(content, bg=self.bg)
        cards.pack(fill="x", padx=30, pady=(0, 17))
        self.summary_values = {}
        for col, key, title in [
            (0, "total", "My Habits"),
            (1, "completed", "Completed Today"),
            (2, "remaining", "Remaining Today"),
            (3, "rate", "Today's Progress"),
        ]:
            cards.grid_columnconfigure(col, weight=1)
            box = tk.Frame(cards, bg=self.card, highlightbackground="#DCE8EC", highlightthickness=1)
            box.grid(row=0, column=col, sticky="nsew", padx=(0, 9))
            tk.Label(box, text=title, font=("Arial", 9), fg=self.muted, bg=self.card).pack(
                anchor="w", padx=12, pady=(12, 3))
            value = tk.Label(box, text="0", font=("Arial", 20, "bold"), fg=self.text, bg=self.card)
            value.pack(anchor="w", padx=12, pady=(0, 12))
            self.summary_values[key] = value

        from views.wellness_panel import WellnessPanel
        self.wellness_panel = WellnessPanel(
            content, self.user, bg_color=self.bg, card_color=self.card,
            text_color=self.text, muted_color=self.muted, primary_color=self.primary,
        )

        panel = tk.Frame(content, bg=self.card, highlightbackground="#DCE8EC", highlightthickness=1)
        panel.pack(fill="both", expand=True, padx=30, pady=(0, 24))
        top = tk.Frame(panel, bg=self.card)
        top.pack(fill="x", padx=18, pady=(15, 8))
        tk.Label(top, text="Today's Habits", font=("Arial", 14, "bold"), fg=self.text,
                 bg=self.card).pack(side="left")
        tk.Button(top, text="Refresh", command=self.refresh, bg="#EDF4F5", fg=self.text,
                  relief="flat", cursor="hand2").pack(side="right", ipadx=8, ipady=4)

        table_frame = tk.Frame(panel, bg=self.card)
        table_frame.pack(fill="both", expand=True, padx=18, pady=(0, 10))
        columns = ("habit_name", "category", "status")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("habit_name", text="Habit")
        self.tree.heading("category", text="Category")
        self.tree.heading("status", text="Today's Status")
        self.tree.column("habit_name", width=300, anchor="w")
        self.tree.column("category", width=190, anchor="w")
        self.tree.column("status", width=170, anchor="center")
        self.tree.tag_configure("completed", foreground="#047857")
        self.tree.tag_configure("pending", foreground="#92400E")
        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        buttons = tk.Frame(panel, bg=self.card)
        buttons.pack(fill="x", padx=18, pady=(0, 15))
        tk.Button(buttons, text="Mark Selected Complete", command=lambda: self.change_status(True),
                  bg=self.primary, fg="white", activebackground="#067784", relief="flat",
                  cursor="hand2").pack(side="left", ipadx=10, ipady=7)
        tk.Button(buttons, text="Reset Selected", command=lambda: self.change_status(False),
                  bg="#EDF4F5", fg=self.text, relief="flat", cursor="hand2").pack(
                      side="left", padx=8, ipadx=10, ipady=7)
        self.status = tk.Label(buttons, text="", font=("Arial", 9), bg=self.card, fg=self.muted)
        self.status.pack(side="right")

    def refresh(self):
        try:
            rows = self.repository.list_today(self.user["user_id"])
            self.rows_by_id = {int(row["habit_id"]): row for row in rows}
            for item in self.tree.get_children():
                self.tree.delete(item)
            for row in rows:
                done = bool(row["completed"])
                self.tree.insert(
                    "", "end", iid=str(row["habit_id"]),
                    values=(row["habit_name"], row.get("category") or "—",
                            "Completed" if done else "Not Completed"),
                    tags=("completed" if done else "pending",),
                )
            total = len(rows)
            completed = sum(1 for row in rows if row["completed"])
            remaining = total - completed
            rate = round(completed * 100 / total) if total else 0
            self.summary_values["total"].configure(text=str(total))
            self.summary_values["completed"].configure(text=str(completed))
            self.summary_values["remaining"].configure(text=str(remaining))
            self.summary_values["rate"].configure(text=f"{rate}%")
            self.status.configure(text=f"{total} habit(s) loaded")
        except ProgressRepositoryError as exc:
            self.status.configure(text="Could not load tracking data")
            messagebox.showerror("Tracking Error", str(exc), parent=self.root)

    def change_status(self, completed):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Select a Habit", "Select a habit first.", parent=self.root)
            return
        habit_id = int(selection[0])
        try:
            self.repository.set_status(self.user["user_id"], habit_id, completed)
            messagebox.showinfo(
                "Tracking Updated",
                "Habit marked completed for today." if completed else "Today's completion was reset.",
                parent=self.root,
            )
            self.refresh()
        except ProgressRepositoryError as exc:
            messagebox.showerror("Tracking Error", str(exc), parent=self.root)

    def open_dashboard(self):
        from views.dashboard_window import DashboardWindow
        DashboardWindow(self.window, self.user)

    def open_habits(self):
        from views.dashboard_window import DashboardWindow
        dashboard = DashboardWindow(self.window, self.user)
        self.window.after(100, dashboard.focus_search)

    def open_reports(self):
        from views.reports_view import ReportsView
        ReportsView(self.window, self.user)

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
