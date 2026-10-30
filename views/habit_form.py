"""Create and edit habits using the MySQL repository layer."""

import tkinter as tk
from tkinter import messagebox, ttk

from controllers.habit_controller import HabitController, HabitRepositoryError
from validators.habit_validator import HabitValidationError, validate_reminder_settings
from views.navigation import get_page_container, clear_page


class HabitForm:
    def __init__(self, root, user, habit=None):
        # The caller may provide either the Tk window or an inner frame.
        # Window-only methods must target the actual top-level window, while
        # page widgets must be rendered inside the shared authenticated host.
        self.window = root.winfo_toplevel()
        self.root = get_page_container(self.window)
        self.user = user
        self.habit = habit
        self.repository = HabitController()
        self.bg_color = "#F3F9FA"
        self.card_color = "#FFFFFF"
        self.text_color = "#0D2D48"
        self.secondary_text = "#58717D"
        self.primary_color = "#078A9B"

        self.clear_window()
        self.window.title("Edit Habit" if habit else "Add New Habit")
        self.window.geometry("620x740")
        self.window.minsize(560, 680)
        self.window.configure(bg=self.bg_color)
        self._build_form()

    def clear_window(self):
        clear_page(self.root)

    def _build_form(self):
        container = tk.Frame(self.root, bg=self.bg_color)
        container.pack(fill="both", expand=True, padx=45, pady=28)
        tk.Label(container, text="Edit Habit" if self.habit else "Add New Habit",
                 font=("Arial", 23, "bold"), fg=self.text_color,
                 bg=self.bg_color).pack(anchor="w")
        tk.Label(container, text="Update your details or create a habit to track.",
                 font=("Arial", 10), fg=self.secondary_text,
                 bg=self.bg_color).pack(anchor="w", pady=(5, 18))

        card = tk.Frame(container, bg=self.card_color, highlightbackground="#DCE8EC", highlightthickness=1)
        card.pack(fill="both", expand=True)
        form = tk.Frame(card, bg=self.card_color)
        form.pack(fill="both", expand=True, padx=28, pady=22)

        tk.Label(form, text="Habit Name *", font=("Arial", 10, "bold"),
                 bg=self.card_color, fg=self.text_color).pack(anchor="w")
        self.habit_name_entry = tk.Entry(form, font=("Arial", 11))
        self.habit_name_entry.pack(fill="x", pady=(5, 13), ipady=6)

        tk.Label(form, text="Category *", font=("Arial", 10, "bold"),
                 bg=self.card_color, fg=self.text_color).pack(anchor="w")
        self.category_options = [
            "Health", "Productivity", "Lifestyle", "Learning", "Fitness",
            "Mental Wellness", "Finance", "Relationships", "Custom category…",
        ]
        self.category_combo = ttk.Combobox(
            form, font=("Arial", 10), state="readonly", values=self.category_options
        )
        self.category_combo.pack(fill="x", pady=(5, 4), ipady=4)
        self.category_combo.bind("<<ComboboxSelected>>", self._on_category_selected)

        self.custom_category_frame = tk.Frame(form, bg=self.card_color)
        tk.Label(
            self.custom_category_frame, text="Your category", font=("Arial", 9, "bold"),
            bg=self.card_color, fg=self.text_color,
        ).pack(anchor="w")
        self.custom_category_entry = tk.Entry(self.custom_category_frame, font=("Arial", 10))
        self.custom_category_entry.pack(fill="x", pady=(3, 3), ipady=4)
        tk.Label(
            self.custom_category_frame,
            text="Use a short name, e.g. Hobbies or Spirituality (max 50 characters).",
            font=("Arial", 8), bg=self.card_color, fg=self.secondary_text,
            wraplength=440, justify="left",
        ).pack(anchor="w", pady=(0, 8))

        tk.Label(form, text="Description", font=("Arial", 10, "bold"),
                 bg=self.card_color, fg=self.text_color).pack(anchor="w")
        self.description_text = tk.Text(form, font=("Arial", 10), height=4, wrap="word")
        self.description_text.pack(fill="x", pady=(5, 13))

        tk.Label(form, text="Target Frequency *", font=("Arial", 10, "bold"),
                 bg=self.card_color, fg=self.text_color).pack(anchor="w")
        self.frequency_combo = ttk.Combobox(form, font=("Arial", 10), state="readonly",
                                            values=["Daily", "Weekly", "Monthly"])
        self.frequency_combo.pack(fill="x", pady=(5, 12), ipady=4)

        reminder_title = tk.Label(
            form, text="Daily Reminder (optional)", font=("Arial", 10, "bold"),
            bg=self.card_color, fg=self.text_color,
        )
        reminder_title.pack(anchor="w")
        reminder_row = tk.Frame(form, bg=self.card_color)
        reminder_row.pack(fill="x", pady=(4, 2))
        existing_reminder_enabled = bool(int((self.habit or {}).get("reminder_enabled") or 0))
        self.reminder_enabled_var = tk.BooleanVar(value=existing_reminder_enabled)
        self.reminder_check = tk.Checkbutton(
            reminder_row, text="Enable reminder", variable=self.reminder_enabled_var,
            command=self._toggle_reminder_time, bg=self.card_color, fg=self.text_color,
            activebackground=self.card_color, selectcolor=self.card_color,
            font=("Arial", 9),
        )
        self.reminder_check.pack(side="left")
        tk.Label(reminder_row, text="Time (24-hour)", font=("Arial", 9),
                 bg=self.card_color, fg=self.secondary_text).pack(side="left", padx=(12, 6))
        self.reminder_time_entry = tk.Entry(reminder_row, font=("Arial", 10), width=8, justify="center")
        self.reminder_time_entry.pack(side="left", ipady=4)
        self.reminder_time_entry.insert(0, (self.habit or {}).get("reminder_time") or "09:00")
        tk.Label(
            form, text="Example: 18:30. The app must remain open for reminders to appear.",
            font=("Arial", 8), bg=self.card_color, fg=self.secondary_text,
        ).pack(anchor="w", pady=(0, 13))
        self._toggle_reminder_time()

        buttons = tk.Frame(form, bg=self.card_color)
        buttons.pack(fill="x", side="bottom")
        tk.Button(buttons, text="Cancel", command=self.go_back, font=("Arial", 10, "bold"),
                  fg="#1B4B69", bg="#DCE8EC", activebackground="#D9F0F0",
                  relief="flat", cursor="hand2").pack(side="right", ipadx=17, ipady=8)
        tk.Button(buttons, text="Update Habit" if self.habit else "Save Habit",
                  command=self.save_habit, font=("Arial", 10, "bold"),
                  fg="white", bg=self.primary_color, activebackground="#067784",
                  relief="flat", cursor="hand2").pack(side="right", padx=(0, 9), ipadx=16, ipady=8)

        if self.habit:
            self.habit_name_entry.insert(0, self.habit.get("habit_name", ""))
            existing_category = (self.habit.get("category") or "").strip()
            if existing_category in self.category_options[:-1]:
                self.category_combo.set(existing_category)
            elif existing_category:
                self.category_combo.set("Custom category…")
                self.custom_category_entry.insert(0, existing_category)
                self.custom_category_frame.pack(fill="x", pady=(0, 8), after=self.category_combo)
            self.description_text.insert("1.0", self.habit.get("description") or "")
            self.frequency_combo.set(self.habit.get("target_frequency") or "")
        else:
            self.category_combo.set("Health")
        self.habit_name_entry.focus_set()

    def _on_category_selected(self, _event=None):
        if self.category_combo.get() == "Custom category…":
            if not self.custom_category_frame.winfo_manager():
                self.custom_category_frame.pack(fill="x", pady=(0, 8), after=self.category_combo)
            self.custom_category_entry.focus_set()
        else:
            self.custom_category_frame.pack_forget()

    def _toggle_reminder_time(self):
        state = "normal" if self.reminder_enabled_var.get() else "disabled"
        self.reminder_time_entry.configure(state=state)

    def save_habit(self):
        selected_category = self.category_combo.get()
        category = (
            self.custom_category_entry.get()
            if selected_category == "Custom category…"
            else selected_category
        )
        fields = {
            "habit_name": self.habit_name_entry.get(),
            "category": category,
            "description": self.description_text.get("1.0", "end-1c"),
            "target_frequency": self.frequency_combo.get(),
            "reminder_enabled": bool(self.reminder_enabled_var.get()),
            "reminder_time": self.reminder_time_entry.get().strip() if self.reminder_enabled_var.get() else None,
        }
        try:
            validate_reminder_settings(fields["reminder_time"], fields["reminder_enabled"])
        except HabitValidationError as exc:
            messagebox.showwarning("Invalid Reminder Time", str(exc), parent=self.window)
            self.reminder_time_entry.focus_set()
            return
        try:
            if self.habit:
                self.repository.update(
                    self.user["user_id"], self.habit["habit_id"],
                    fields["habit_name"], fields["category"],
                    fields["description"], fields["target_frequency"],
                    fields["reminder_time"], fields["reminder_enabled"],
                )
                messagebox.showinfo("Habit Updated", "Your habit was updated and saved.", parent=self.window)
            else:
                self.repository.create(
                    self.user["user_id"], fields["habit_name"], fields["category"],
                    fields["description"], fields["target_frequency"],
                    fields["reminder_time"], fields["reminder_enabled"],
                )
                messagebox.showinfo("Habit Created", "Your new habit was saved to the database.", parent=self.window)
            self.go_back()
        except HabitValidationError as exc:
            messagebox.showwarning("Check Habit Details", str(exc), parent=self.window)
        except HabitRepositoryError as exc:
            messagebox.showerror("Database Error", str(exc), parent=self.window)

    def go_back(self):
        from views.dashboard_window import DashboardWindow
        DashboardWindow(self.window, self.user)
