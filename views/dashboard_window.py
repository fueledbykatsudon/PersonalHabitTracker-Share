"""Authenticated dashboard with persistent, searchable MySQL habit CRUD."""

import tkinter as tk
from datetime import date
from tkinter import messagebox, ttk

from models.accounts import account_from_user_record
from controllers.habit_controller import HabitController, HabitRepositoryError


from views.navigation import get_page_container, clear_page

class DashboardWindow:
    def __init__(self, root, user):
        self.window = root
        self.root = get_page_container(root)
        self.user = dict(user)
        self.account = account_from_user_record(self.user)
        # Normalize the legacy DB role label for every view's display logic.
        self.user["role_name"] = self.account.role_name
        self.repository = HabitController()
        self.habits_by_id = {}

        self.bg_color = "#F3F9FA"
        self.sidebar_color = "#123B5D"
        self.primary_color = "#078A9B"
        self.card_color = "#FFFFFF"
        self.text_color = "#0D2D48"
        self.secondary_text = "#58717D"
        self.border_color = "#DCE8EC"
        self.success_color = "#21A67A"
        self.soft_teal = "#E6F6F5"

        self.clear_window()
        self.window.title("Personal Habit Tracker - Dashboard")
        self.window.geometry("1120x740")
        self.window.minsize(1000, 650)
        self.window.configure(bg=self.bg_color)
        self._build_sidebar()
        self._build_content()
        self.refresh_data()
        self._ensure_reminder_scheduler()

    def clear_window(self):
        clear_page(self.root)

    def _build_sidebar(self):
        sidebar = tk.Frame(self.root, bg=self.sidebar_color, width=220)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # Text-only brand until the final logo is approved.
        from pathlib import Path
        logo_path = Path(__file__).resolve().parent.parent / "assets" / "pht_logo_sidebar.png"
        self.logo_image = tk.PhotoImage(file=str(logo_path))
        tk.Label(sidebar, image=self.logo_image, bg=self.sidebar_color,
                 borderwidth=0).pack(pady=(18, 18))
        self._nav_button(sidebar, "Dashboard", self.refresh_data, active=True)
        self._nav_button(sidebar, "My Habits", self.focus_search)
        self._nav_button(sidebar, "Habit Tracking", self.open_tracking)
        self._nav_button(sidebar, "Reports", self.open_reports)
        self._nav_button(sidebar, "Wellness Advisor", self.open_wellness)

        if self.account.can_manage_users:
            self._nav_button(sidebar, "User & Audit Logs", self.show_admin_users)

        spacer = tk.Frame(sidebar, bg=self.sidebar_color)
        spacer.pack(fill="both", expand=True)
        user_card = tk.Frame(sidebar, bg="#0D2D48")
        user_card.pack(fill="x", padx=12, pady=(0, 10))
        tk.Label(user_card, text=self.user.get("full_name", "User"),
                 font=("Arial", 10, "bold"), fg="white", bg="#0D2D48",
                 wraplength=180, justify="left").pack(anchor="w", padx=10, pady=(10, 2))
        tk.Label(user_card, text=f"@{self.user.get('username', '')}",
                 font=("Arial", 9), fg="#A9C4CC", bg="#0D2D48").pack(
                     anchor="w", padx=10, pady=(0, 10))
        tk.Button(sidebar, text="Logout", command=self.logout, font=("Arial", 10, "bold"),
                  fg="white", bg="#1B4B69", activebackground="#24617D",
                  relief="flat", bd=0, cursor="hand2").pack(
                      fill="x", padx=18, pady=(0, 20), ipady=8)

    def _nav_button(self, parent, text, command, active=False):
        """Build a consistent sidebar link and identify the current section."""
        background = "#1B4B69" if active else self.sidebar_color
        foreground = "white" if active else "#D9F0F0"
        tk.Button(
            parent, text=text, command=command,
            font=("Arial", 10, "bold" if active else "normal"), anchor="w",
            fg=foreground, bg=background, activebackground="#24617D",
            activeforeground="white", relief="flat", bd=0,
            cursor="hand2", padx=20,
        ).pack(fill="x", padx=12, pady=3, ipady=9)

    def _build_content(self):
        content = tk.Frame(self.root, bg=self.bg_color)
        content.pack(side="left", fill="both", expand=True)
        self.content = content

        # A compact header keeps the page friendly without wasting vertical space.
        header = tk.Frame(content, bg=self.bg_color)
        header.pack(fill="x", padx=30, pady=(22, 15))
        title_block = tk.Frame(header, bg=self.bg_color)
        title_block.pack(side="left", fill="x", expand=True)
        tk.Label(title_block, text=self.account.dashboard_greeting(),
                 font=("Arial", 22, "bold"), fg=self.text_color,
                 bg=self.bg_color).pack(anchor="w")
        tk.Label(title_block, text="Build better habits, one day at a time.",
                 font=("Arial", 10), fg=self.secondary_text,
                 bg=self.bg_color).pack(anchor="w", pady=(4, 0))
        date_chip = tk.Frame(header, bg=self.soft_teal)
        date_chip.pack(side="right", anchor="n", padx=(12, 0), pady=(3, 0))
        tk.Label(date_chip, text=date.today().strftime("%a, %b %d, %Y"),
                 font=("Arial", 9, "bold"), fg=self.primary_color,
                 bg=self.soft_teal).pack(padx=12, pady=8)

        # Summary cards are data-driven; values are refreshed from MySQL below.
        stats = tk.Frame(content, bg=self.bg_color)
        stats.pack(fill="x", padx=30, pady=(0, 14))
        self.stat_values = {}
        self.progress_bar = None
        stat_specs = [
            (0, "active_habits", "Active Habits", "habits in your account", "#078A9B"),
            (1, "completed_today", "Completed Today", "habits done today", "#21A67A"),
            (2, "progress", "Today's Progress", "daily completion rate", "#5278D0"),
        ]
        for column, key, title, caption, accent in stat_specs:
            stats.grid_columnconfigure(column, weight=1, uniform="summary")
            card = tk.Frame(stats, bg=self.card_color, highlightbackground=self.border_color,
                            highlightthickness=1, height=108)
            card.grid(row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 8, 0))
            card.grid_propagate(False)
            accent_line = tk.Frame(card, bg=accent, height=4)
            accent_line.pack(fill="x", side="top")
            tk.Label(card, text=title, font=("Arial", 9, "bold"), bg=self.card_color,
                     fg=self.secondary_text).pack(anchor="w", padx=14, pady=(9, 0))
            value_label = tk.Label(card, text="—", font=("Arial", 22, "bold"),
                                   bg=self.card_color, fg=self.text_color)
            value_label.pack(anchor="w", padx=14, pady=(0, 0))
            tk.Label(card, text=caption, font=("Arial", 8), bg=self.card_color,
                     fg=self.secondary_text).pack(anchor="w", padx=14, pady=(0, 7))
            self.stat_values[key] = value_label
            if key == "progress":
                self.progress_bar = ttk.Progressbar(card, mode="determinate", maximum=100,
                                                     style="PHT.Horizontal.TProgressbar")
                self.progress_bar.pack(fill="x", padx=14, pady=(0, 9))

        style = ttk.Style(self.root)
        try:
            style.configure("PHT.Treeview", background="#FFFFFF", foreground=self.text_color,
                            fieldbackground="#FFFFFF", rowheight=30, font=("Arial", 10), borderwidth=0)
            style.configure("PHT.Treeview.Heading", background="#EAF2F4", foreground=self.text_color,
                            font=("Arial", 9, "bold"), relief="flat")
            style.map("PHT.Treeview", background=[("selected", "#D7F1EE")],
                      foreground=[("selected", self.text_color)])
            style.configure("PHT.Horizontal.TProgressbar", troughcolor="#E7EFF1",
                            background=self.success_color, bordercolor="#E7EFF1", lightcolor=self.success_color,
                            darkcolor=self.success_color)
        except tk.TclError:
            pass

        from views.wellness_panel import WellnessPanel
        self.wellness_panel = WellnessPanel(
            content, self.user, bg_color=self.bg_color, card_color=self.card_color,
            text_color=self.text_color, muted_color=self.secondary_text,
            primary_color=self.primary_color,
        )

        panel = tk.Frame(content, bg=self.card_color, highlightbackground=self.border_color,
                         highlightthickness=1)
        panel.pack(fill="both", expand=True, padx=30, pady=(0, 22))
        top = tk.Frame(panel, bg=self.card_color)
        top.pack(fill="x", padx=18, pady=(13, 8))
        title_area = tk.Frame(top, bg=self.card_color)
        title_area.pack(side="left", fill="x", expand=True)
        tk.Label(title_area, text="My Habits", font=("Arial", 15, "bold"), bg=self.card_color,
                 fg=self.text_color).pack(side="left")
        tk.Label(title_area, text="YOUR ROUTINE", font=("Arial", 8, "bold"),
                 bg=self.card_color, fg=self.primary_color).pack(side="left", padx=(10, 0), pady=(3, 0))
        tk.Button(top, text="+ Add Habit", command=self.add_habit,
                  bg=self.primary_color, fg="white", activebackground="#067784",
                  activeforeground="white", relief="flat", bd=0,
                  font=("Arial", 9, "bold"), cursor="hand2").pack(side="right", ipady=6, ipadx=12)

        toolbar = tk.Frame(panel, bg=self.card_color)
        toolbar.pack(fill="x", padx=18, pady=(0, 9))
        self.search_var = tk.StringVar()
        self.search_entry = tk.Entry(toolbar, textvariable=self.search_var,
                                     font=("Arial", 10), relief="solid", bd=1,
                                     highlightthickness=1, highlightbackground=self.border_color,
                                     highlightcolor=self.primary_color)
        self.search_entry.pack(side="left", fill="x", expand=True, ipady=7)
        self.search_entry.bind("<Return>", lambda _event: self.refresh_habits())
        tk.Button(toolbar, text="Search", command=self.refresh_habits,
                  bg=self.soft_teal, fg=self.primary_color, relief="flat", bd=0,
                  cursor="hand2", font=("Arial", 9, "bold")).pack(side="left", padx=(8, 4), ipady=6, ipadx=10)
        tk.Button(toolbar, text="Clear", command=self.clear_search,
                  bg="#EDF4F5", fg=self.text_color, relief="flat", bd=0,
                  cursor="hand2", font=("Arial", 9)).pack(side="left", padx=4, ipady=6, ipadx=10)

        # Build the table first, but pack it only after the action bar below.
        # An expanding widget packed before the action bar can consume the
        # remaining height and push Edit/Delete outside the visible panel.
        table_frame = tk.Frame(panel, bg=self.card_color)
        columns = ("habit_name", "category", "frequency", "reminder", "created_at")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="browse",
                                 style="PHT.Treeview")
        self.tree.heading("habit_name", text="HABIT NAME")
        self.tree.heading("category", text="CATEGORY")
        self.tree.heading("frequency", text="FREQUENCY")
        self.tree.heading("reminder", text="REMINDER")
        self.tree.heading("created_at", text="CREATED")
        self.tree.column("habit_name", width=230, minwidth=150, anchor="w")
        self.tree.column("category", width=115, minwidth=90, anchor="w")
        self.tree.column("frequency", width=100, minwidth=80, anchor="center")
        self.tree.column("reminder", width=115, minwidth=95, anchor="center")
        self.tree.column("created_at", width=120, minwidth=100, anchor="center")
        vertical = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vertical.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vertical.pack(side="right", fill="y")
        self.empty_state = tk.Label(
            table_frame, text="No habits yet\nStart small — add your first habit to begin building consistency.",
            font=("Arial", 10), fg=self.secondary_text, bg=self.card_color,
            justify="center", pady=20,
        )
        self.tree.bind("<Double-1>", lambda _event: self.edit_selected())

        # Reserve the bottom strip for row actions before allowing the table
        # to expand. This keeps both buttons visible on the minimum window size.
        buttons = tk.Frame(panel, bg=self.card_color)
        buttons.pack(side="bottom", fill="x", padx=18, pady=(0, 12))
        tk.Button(
            buttons, text="Edit Selected", command=self.edit_selected,
            bg=self.soft_teal, fg=self.primary_color, activebackground="#D5EFED",
            relief="flat", bd=0, cursor="hand2", font=("Arial", 9, "bold"),
        ).pack(side="left", ipadx=9, ipady=6)
        tk.Button(
            buttons, text="Delete Selected", command=self.delete_selected,
            bg="#FEF2F2", fg="#B91C1C", activebackground="#FEE2E2",
            relief="flat", bd=0, cursor="hand2", font=("Arial", 9, "bold"),
        ).pack(side="left", padx=8, ipadx=9, ipady=6)
        self.status_label = tk.Label(buttons, text="", font=("Arial", 9),
                                     bg=self.card_color, fg=self.secondary_text)
        self.status_label.pack(side="right")

        # Pack the table last so it takes only the space left above the actions.
        table_frame.pack(side="top", fill="both", expand=True, padx=18, pady=(0, 7))

    def refresh_data(self):
        try:
            summary = self.repository.get_summary(self.user["user_id"])
            active = summary["active_habits"]
            completed = summary["completed_today"]
            progress = round((completed / active) * 100) if active else 0
            self.stat_values["active_habits"].configure(text=str(active))
            self.stat_values["completed_today"].configure(text=str(completed))
            self.stat_values["progress"].configure(text=f"{progress}%")
            if self.progress_bar is not None:
                self.progress_bar.configure(value=progress)
            self.refresh_habits()
        except HabitRepositoryError as exc:
            messagebox.showerror("Database Error", str(exc), parent=self.root)
            self.status_label.configure(text="Could not load summary")

    def refresh_habits(self):
        try:
            search = self.search_var.get().strip()
            habits = self.repository.list_for_user(self.user["user_id"], search)
            self.habits_by_id = {int(habit["habit_id"]): habit for habit in habits}
            for item in self.tree.get_children():
                self.tree.delete(item)
            for habit in habits:
                created = habit.get("created_at")
                created_text = created.strftime("%Y-%m-%d") if hasattr(created, "strftime") else str(created or "")
                self.tree.insert(
                    "", "end", iid=str(habit["habit_id"]),
                    values=(
                        habit["habit_name"], habit.get("category") or "—",
                        habit.get("target_frequency") or "—",
                        (f"On · {habit.get('reminder_time')}"
                         if int(habit.get("reminder_enabled") or 0) and habit.get("reminder_time")
                         else "Off"),
                        created_text,
                    ),
                )
            if habits:
                self.empty_state.place_forget()
            else:
                if search:
                    self.empty_state.configure(
                        text="No matching habits\nTry another search or clear the search field."
                    )
                else:
                    self.empty_state.configure(
                        text="No habits yet\nStart small — add your first habit to begin building consistency."
                    )
                self.empty_state.place(relx=0.5, rely=0.42, anchor="center")
            self.status_label.configure(text=f"{len(habits)} habit(s) found")
        except HabitRepositoryError as exc:
            self.status_label.configure(text="Unable to load habits")
            messagebox.showerror("Database Error", str(exc), parent=self.root)

    def clear_search(self):
        self.search_var.set("")
        self.refresh_habits()

    def focus_search(self):
        self.search_entry.focus_set()
        self.search_entry.select_range(0, tk.END)

    def add_habit(self):
        from views.habit_form import HabitForm
        HabitForm(self.window, self.user)

    def edit_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select a Habit", "Select a habit to edit first.", parent=self.root)
            return
        habit = self.habits_by_id.get(int(selected[0]))
        if habit is None:
            self.refresh_habits()
            return
        from views.habit_form import HabitForm
        HabitForm(self.window, self.user, habit=habit)

    def delete_selected(self):
        # Clicking a button can leave Treeview focus set even when selection is
        # temporarily empty. Prefer the selection, then use a valid focused row.
        selected = self.tree.selection()
        item_id = selected[0] if selected else self.tree.focus()
        if not item_id or not self.tree.exists(item_id):
            messagebox.showwarning("Select a Habit", "Select a habit to delete first.", parent=self.root)
            return
        try:
            habit_id = int(item_id)
        except (TypeError, ValueError):
            messagebox.showwarning("Select a Habit", "Please select a valid habit row.", parent=self.root)
            return
        habit = self.habits_by_id.get(habit_id)
        if habit is None:
            self.refresh_habits()
            return
        confirmed = messagebox.askyesno(
            "Delete Habit",
            f"Delete '{habit['habit_name']}'? Its completion history will also be deleted.",
            parent=self.root,
        )
        if not confirmed:
            return
        try:
            self.repository.delete(self.user["user_id"], habit_id)
            messagebox.showinfo("Habit Deleted", "The habit and its completion history were deleted.", parent=self.root)
            self.refresh_data()
        except HabitRepositoryError as exc:
            # Keep the main message understandable while making the database
            # reason visible for troubleshooting when the operation is rejected.
            cause = exc.__cause__
            detail = f"\n\nDatabase detail: {cause}" if cause else ""
            messagebox.showerror("Delete Failed", f"{exc}{detail}", parent=self.root)

    def _ensure_reminder_scheduler(self):
        """Keep a single scheduler per Tk window across page navigation."""
        scheduler = getattr(self.window, "_pht_reminder_scheduler", None)
        if scheduler is not None and scheduler.user_id != int(self.user["user_id"]):
            scheduler.stop()
            scheduler = None
        if scheduler is None or not scheduler.running:
            from services.reminder_scheduler import ReminderScheduler
            scheduler = ReminderScheduler(self.window, int(self.user["user_id"]))
            setattr(self.window, "_pht_reminder_scheduler", scheduler)
            scheduler.start()

    def _stop_reminder_scheduler(self):
        from services.reminder_scheduler import stop_window_reminder_scheduler
        stop_window_reminder_scheduler(self.window)

    def open_tracking(self):
        from views.tracking_view import TrackingView
        TrackingView(self.window, self.user)

    def open_reports(self):
        from views.reports_view import ReportsView
        ReportsView(self.window, self.user)

    def open_wellness(self):
        from views.wellness_view import WellnessView
        WellnessView(self.window, self.user)

    def show_admin_users(self):
        if not self.account.can_manage_users:
            messagebox.showerror("Access Denied", "Administrator permission is required.", parent=self.root)
            return
        from views.admin_users_view import AdminUsersView
        AdminUsersView(self.window, self.user)

    def logout(self):
        if messagebox.askyesno("Logout", "Are you sure you want to logout?", parent=self.root):
            self._stop_reminder_scheduler()
            from views.login_window import LoginWindow
            LoginWindow(self.window)
