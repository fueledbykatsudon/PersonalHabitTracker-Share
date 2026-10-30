import tkinter as tk


class Dashboard:
    def __init__(self, root, username="User"):
        self.root = root
        self.username = username

        self.root.title("Personal Habit Tracker - Dashboard")
        self.root.geometry("1100x700")
        self.root.resizable(False, False)
        self.root.configure(bg="#F3F9FA")

        self.show_dashboard()

    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def show_dashboard(self):
        self.clear_screen()

        self.create_sidebar()

        content = tk.Frame(
            self.root,
            bg="#F3F9FA"
        )
        content.pack(
            side="right",
            fill="both",
            expand=True
        )

        heading = tk.Label(
            content,
            text=f"Good day, {self.username}!",
            font=("Arial", 27, "bold"),
            bg="#F3F9FA",
            fg="#123B5D"
        )
        heading.pack(
            anchor="w",
            padx=45,
            pady=(40, 5)
        )

        subheading = tk.Label(
            content,
            text="Here's an overview of your habits and progress.",
            font=("Arial", 11),
            bg="#F3F9FA",
            fg="#58717D"
        )
        subheading.pack(
            anchor="w",
            padx=45,
            pady=(0, 30)
        )

        cards_frame = tk.Frame(
            content,
            bg="#F3F9FA"
        )
        cards_frame.pack(
            fill="x",
            padx=45
        )

        self.create_card(
            cards_frame,
            "Active Habits",
            "0",
            0
        )

        self.create_card(
            cards_frame,
            "Completed Today",
            "0",
            1
        )

        self.create_card(
            cards_frame,
            "Current Streak",
            "0 days",
            2
        )

        quick_title = tk.Label(
            content,
            text="Quick Actions",
            font=("Arial", 18, "bold"),
            bg="#F3F9FA",
            fg="#123B5D"
        )
        quick_title.pack(
            anchor="w",
            padx=45,
            pady=(35, 15)
        )

        quick_frame = tk.Frame(
            content,
            bg="#F3F9FA"
        )
        quick_frame.pack(
            fill="x",
            padx=45
        )

        self.create_action_button(
            quick_frame,
            "＋ Add Habit",
            0,
            self.open_habits
        )

        self.create_action_button(
            quick_frame,
            "✓ Track Habit",
            1,
            self.open_tracking
        )

        self.create_action_button(
            quick_frame,
            "▣ View Reports",
            2,
            self.open_reports
        )

        panel = tk.Frame(
            content,
            bg="white",
            height=180
        )
        panel.pack(
            fill="x",
            padx=45,
            pady=30
        )
        panel.pack_propagate(False)

        panel_title = tk.Label(
            panel,
            text="Start Building Better Habits",
            font=("Arial", 18, "bold"),
            bg="white",
            fg="#123B5D"
        )
        panel_title.pack(
            anchor="w",
            padx=25,
            pady=(25, 8)
        )

        panel_text = tk.Label(
            panel,
            text=(
                "Create habits, track your daily progress, "
                "and build consistency over time."
            ),
            font=("Arial", 11),
            bg="white",
            fg="#58717D"
        )
        panel_text.pack(
            anchor="w",
            padx=25
        )

    def create_sidebar(self):
        sidebar = tk.Frame(
            self.root,
            bg="#0797A5",
            width=230
        )
        sidebar.pack(
            side="left",
            fill="y"
        )
        sidebar.pack_propagate(False)

        logo_label = tk.Label(
            sidebar,
            text="PH",
            font=("Arial", 32, "bold"),
            bg="#0797A5",
            fg="white"
        )
        logo_label.pack(
            pady=(35, 5)
        )

        app_label = tk.Label(
            sidebar,
            text="Personal Habit\nTracker",
            font=("Arial", 16, "bold"),
            bg="#0797A5",
            fg="white",
            justify="center"
        )
        app_label.pack(
            pady=(0, 35)
        )

        self.create_menu_button(
            sidebar,
            "Dashboard",
            self.show_dashboard
        )

        self.create_menu_button(
            sidebar,
            "My Habits",
            self.open_habits
        )

        self.create_menu_button(
            sidebar,
            "Habit Tracking",
            self.open_tracking
        )

        self.create_menu_button(
            sidebar,
            "Reports",
            self.open_reports
        )

        self.create_menu_button(
            sidebar,
            "Wellness Advisor",
            self.open_wellness
        )

        logout_button = tk.Button(
            sidebar,
            text="Logout",
            font=("Arial", 11, "bold"),
            bg="#0797A5",
            fg="white",
            activebackground="#067784",
            activeforeground="white",
            relief="flat",
            anchor="w",
            padx=25,
            cursor="hand2",
            command=self.logout
        )
        logout_button.pack(
            side="bottom",
            fill="x",
            ipady=10,
            pady=20
        )

    def create_menu_button(self, parent, text, command):
        button = tk.Button(
            parent,
            text=text,
            font=("Arial", 11),
            bg="#0797A5",
            fg="white",
            activebackground="#067784",
            activeforeground="white",
            relief="flat",
            anchor="w",
            padx=25,
            cursor="hand2",
            command=command
        )
        button.pack(
            fill="x",
            ipady=10
        )

    def create_card(self, parent, title, value, column):
        card = tk.Frame(
            parent,
            bg="white",
            width=220,
            height=115
        )
        card.grid(
            row=0,
            column=column,
            padx=(0, 15),
            sticky="nsew"
        )
        card.grid_propagate(False)

        title_label = tk.Label(
            card,
            text=title,
            font=("Arial", 10),
            bg="white",
            fg="#58717D"
        )
        title_label.pack(
            anchor="w",
            padx=18,
            pady=(18, 5)
        )

        value_label = tk.Label(
            card,
            text=value,
            font=("Arial", 23, "bold"),
            bg="white",
            fg="#0797A5"
        )
        value_label.pack(
            anchor="w",
            padx=18
        )

    def create_action_button(self, parent, text, column, command):
        button = tk.Button(
            parent,
            text=text,
            font=("Arial", 11, "bold"),
            bg="white",
            fg="#0797A5",
            activebackground="#E5F5F5",
            activeforeground="#0797A5",
            width=20,
            height=2,
            relief="solid",
            borderwidth=1,
            cursor="hand2",
            command=command
        )
        button.grid(
            row=0,
            column=column,
            padx=(0, 15)
        )

    def open_habits(self):
        from views.habit_view import HabitView

        self.clear_screen()
        HabitView(
            self.root,
            self.username
        )

    def open_tracking(self):
        from views.tracking_view import TrackingView

        self.clear_screen()
        TrackingView(
            self.root,
            self.username
        )

    def open_reports(self):
        from views.reports_view import ReportsView

        self.clear_screen()
        ReportsView(
            self.root,
            self.username
        )

    def open_wellness(self):
        from views.wellness_view import WellnessView

        self.clear_screen()
        WellnessView(
            self.root,
            self.username
        )

    def logout(self):
        from services.reminder_scheduler import stop_window_reminder_scheduler
        stop_window_reminder_scheduler(self.window if hasattr(self, "window") else self.root)
        from views.login_window import LoginWindow

        self.clear_screen()
        LoginWindow(self.root)