import tkinter as tk
from tkinter import ttk, messagebox


from views.navigation import get_page_container, clear_page

class HabitView:
    def __init__(self, root, username="User"):
        self.window = root
        self.root = get_page_container(root)
        self.username = username

        self.habits = []

        self.window.title("Personal Habit Tracker - My Habits")
        self.window.geometry("1100x700")
        self.window.resizable(False, False)
        self.window.configure(bg="#F3F9FA")

        self.show_habits()

    def clear_screen(self):
        clear_page(self.root)

    def show_habits(self):
        self.clear_screen()

        sidebar = self.create_sidebar()

        content = tk.Frame(
            self.root,
            bg="#F3F9FA"
        )
        content.pack(
            side="right",
            fill="both",
            expand=True
        )

        title = tk.Label(
            content,
            text="My Habits",
            font=("Arial", 27, "bold"),
            bg="#F3F9FA",
            fg="#123B5D"
        )
        title.pack(
            anchor="w",
            padx=40,
            pady=(35, 5)
        )

        subtitle = tk.Label(
            content,
            text="Create, manage, and organize your habits.",
            font=("Arial", 11),
            bg="#F3F9FA",
            fg="#58717D"
        )
        subtitle.pack(
            anchor="w",
            padx=40,
            pady=(0, 25)
        )

        toolbar = tk.Frame(
            content,
            bg="#F3F9FA"
        )
        toolbar.pack(
            fill="x",
            padx=40
        )

        search_label = tk.Label(
            toolbar,
            text="Search:",
            font=("Arial", 10, "bold"),
            bg="#F3F9FA",
            fg="#444444"
        )
        search_label.pack(
            side="left"
        )

        self.search_entry = tk.Entry(
            toolbar,
            font=("Arial", 11),
            width=30,
            relief="solid",
            borderwidth=1
        )
        self.search_entry.pack(
            side="left",
            padx=10,
            ipady=5
        )

        search_button = tk.Button(
            toolbar,
            text="Search",
            font=("Arial", 10, "bold"),
            bg="#0797A5",
            fg="white",
            relief="flat",
            cursor="hand2",
            command=self.search_habits
        )
        search_button.pack(
            side="left",
            padx=5,
            ipadx=10,
            ipady=5
        )

        add_button = tk.Button(
            toolbar,
            text="＋ Add Habit",
            font=("Arial", 10, "bold"),
            bg="#0797A5",
            fg="white",
            relief="flat",
            cursor="hand2",
            command=self.add_habit
        )
        add_button.pack(
            side="right",
            ipadx=10,
            ipady=5
        )

        table_frame = tk.Frame(
            content,
            bg="white"
        )
        table_frame.pack(
            fill="both",
            expand=True,
            padx=40,
            pady=25
        )

        columns = (
            "name",
            "category",
            "frequency",
            "description"
        )

        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            height=18
        )

        self.tree.heading(
            "name",
            text="Habit Name"
        )
        self.tree.heading(
            "category",
            text="Category"
        )
        self.tree.heading(
            "frequency",
            text="Frequency"
        )
        self.tree.heading(
            "description",
            text="Description"
        )

        self.tree.column(
            "name",
            width=190
        )
        self.tree.column(
            "category",
            width=130
        )
        self.tree.column(
            "frequency",
            width=130
        )
        self.tree.column(
            "description",
            width=350
        )

        scrollbar = ttk.Scrollbar(
            table_frame,
            orient="vertical",
            command=self.tree.yview
        )

        self.tree.configure(
            yscrollcommand=scrollbar.set
        )

        self.tree.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar.pack(
            side="right",
            fill="y"
        )

        action_frame = tk.Frame(
            content,
            bg="#F3F9FA"
        )
        action_frame.pack(
            fill="x",
            padx=40,
            pady=(0, 20)
        )

        edit_button = tk.Button(
            action_frame,
            text="Edit Selected",
            font=("Arial", 10, "bold"),
            bg="white",
            fg="#0797A5",
            relief="solid",
            borderwidth=1,
            cursor="hand2",
            command=self.edit_habit
        )
        edit_button.pack(
            side="left",
            padx=(0, 10),
            ipadx=10,
            ipady=5
        )

        delete_button = tk.Button(
            action_frame,
            text="Delete Selected",
            font=("Arial", 10, "bold"),
            bg="white",
            fg="#A94442",
            relief="solid",
            borderwidth=1,
            cursor="hand2",
            command=self.delete_habit
        )
        delete_button.pack(
            side="left",
            ipadx=10,
            ipady=5
        )

        self.refresh_table()

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

        tk.Label(
            sidebar,
            text="PH",
            font=("Arial", 32, "bold"),
            bg="#0797A5",
            fg="white"
        ).pack(pady=(35, 5))

        tk.Label(
            sidebar,
            text="Personal Habit\nTracker",
            font=("Arial", 16, "bold"),
            bg="#0797A5",
            fg="white",
            justify="center"
        ).pack(pady=(0, 35))

        self.menu_button(
            sidebar,
            "Dashboard",
            self.go_dashboard
        )

        self.menu_button(
            sidebar,
            "My Habits",
            self.show_habits
        )

        self.menu_button(
            sidebar,
            "Habit Tracking",
            self.go_tracking
        )

        self.menu_button(
            sidebar,
            "Reports",
            self.go_reports
        )

        self.menu_button(
            sidebar,
            "Wellness Advisor",
            self.go_wellness
        )

        tk.Button(
            sidebar,
            text="Logout",
            font=("Arial", 11, "bold"),
            bg="#0797A5",
            fg="white",
            relief="flat",
            anchor="w",
            padx=25,
            cursor="hand2",
            command=self.logout
        ).pack(
            side="bottom",
            fill="x",
            ipady=10,
            pady=20
        )

    def menu_button(self, parent, text, command):
        tk.Button(
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
        ).pack(
            fill="x",
            ipady=10
        )

    def add_habit(self):
        self.habit_form()

    def habit_form(self, selected_index=None):
        window = tk.Toplevel(self.root)
        window.title("Add Habit")
        window.geometry("430x500")
        window.resizable(False, False)
        window.configure(bg="white")

        tk.Label(
            window,
            text="Add Habit",
            font=("Arial", 22, "bold"),
            bg="white",
            fg="#123B5D"
        ).pack(pady=(25, 20))

        tk.Label(
            window,
            text="Habit Name",
            font=("Arial", 10, "bold"),
            bg="white"
        ).pack(anchor="w", padx=50)

        name_entry = tk.Entry(
            window,
            font=("Arial", 11),
            width=35
        )
        name_entry.pack(
            padx=50,
            pady=(5, 15),
            ipady=5
        )

        tk.Label(
            window,
            text="Category",
            font=("Arial", 10, "bold"),
            bg="white"
        ).pack(anchor="w", padx=50)

        category_entry = tk.Entry(
            window,
            font=("Arial", 11),
            width=35
        )
        category_entry.pack(
            padx=50,
            pady=(5, 15),
            ipady=5
        )

        tk.Label(
            window,
            text="Target Frequency",
            font=("Arial", 10, "bold"),
            bg="white"
        ).pack(anchor="w", padx=50)

        frequency_entry = tk.Entry(
            window,
            font=("Arial", 11),
            width=35
        )
        frequency_entry.pack(
            padx=50,
            pady=(5, 15),
            ipady=5
        )

        tk.Label(
            window,
            text="Description",
            font=("Arial", 10, "bold"),
            bg="white"
        ).pack(anchor="w", padx=50)

        description_entry = tk.Entry(
            window,
            font=("Arial", 11),
            width=35
        )
        description_entry.pack(
            padx=50,
            pady=(5, 20),
            ipady=5
        )

        def save():
            name = name_entry.get().strip()

            if not name:
                messagebox.showwarning(
                    "Validation",
                    "Please enter a habit name."
                )
                return

            data = {
                "name": name,
                "category": category_entry.get().strip(),
                "frequency": frequency_entry.get().strip(),
                "description": description_entry.get().strip()
            }

            if selected_index is None:
                self.habits.append(data)
            else:
                self.habits[selected_index] = data

            self.refresh_table()
            window.destroy()

        tk.Button(
            window,
            text="Save Habit",
            font=("Arial", 11, "bold"),
            bg="#0797A5",
            fg="white",
            relief="flat",
            cursor="hand2",
            width=20,
            command=save
        ).pack(
            pady=5,
            ipady=6
        )

        tk.Button(
            window,
            text="Cancel",
            font=("Arial", 10),
            bg="white",
            fg="#555555",
            relief="solid",
            borderwidth=1,
            cursor="hand2",
            width=20,
            command=window.destroy
        ).pack(
            pady=5,
            ipady=5
        )

    def refresh_table(self, habits=None):
        for item in self.tree.get_children():
            self.tree.delete(item)

        data = self.habits if habits is None else habits

        for habit in data:
            self.tree.insert(
                "",
                "end",
                values=(
                    habit["name"],
                    habit["category"],
                    habit["frequency"],
                    habit["description"]
                )
            )

    def search_habits(self):
        query = self.search_entry.get().strip().lower()

        if not query:
            self.refresh_table()
            return

        results = [
            habit
            for habit in self.habits
            if query in habit["name"].lower()
            or query in habit["category"].lower()
            or query in habit["description"].lower()
        ]

        self.refresh_table(results)

    def edit_habit(self):
        selected = self.tree.selection()

        if not selected:
            messagebox.showinfo(
                "Edit Habit",
                "Please select a habit first."
            )
            return

        item = self.tree.item(selected[0])
        name = item["values"][0]

        index = next(
            (
                i
                for i, habit in enumerate(self.habits)
                if habit["name"] == name
            ),
            None
        )

        if index is not None:
            self.habit_form(index)

    def delete_habit(self):
        selected = self.tree.selection()

        if not selected:
            messagebox.showinfo(
                "Delete Habit",
                "Please select a habit first."
            )
            return

        item = self.tree.item(selected[0])
        name = item["values"][0]

        confirmed = messagebox.askyesno(
            "Delete Habit",
            f"Delete '{name}'?"
        )

        if confirmed:
            self.habits = [
                habit
                for habit in self.habits
                if habit["name"] != name
            ]

            self.refresh_table()

    def go_dashboard(self):
        from views.dashboard import Dashboard

        self.clear_screen()
        Dashboard(
            self.root,
            self.username
        )

    def go_tracking(self):
        from views.tracking_view import TrackingView

        self.clear_screen()
        TrackingView(
            self.window,
            self.username
        )

    def go_reports(self):
        from views.reports_view import ReportsView

        self.clear_screen()
        ReportsView(
            self.window,
            self.username
        )

    def go_wellness(self):
        from views.wellness_view import WellnessView

        self.clear_screen()
        WellnessView(
            self.window,
            self.username
        )

    def logout(self):
        from services.reminder_scheduler import stop_window_reminder_scheduler
        stop_window_reminder_scheduler(self.window if hasattr(self, "window") else self.root)
        from views.login_window import LoginWindow

        self.clear_screen()
        LoginWindow(self.window)