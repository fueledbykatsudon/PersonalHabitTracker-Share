"""Welcome, login, and account registration screens."""

import logging
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

from core.exceptions import AuthenticationError, DatabaseError, ValidationError
from controllers.user_controller import UserController


class LoginWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Personal Habit Tracker")
        self.root.geometry("900x600")
        self.root.resizable(False, False)
        self.root.configure(bg="#F3F9FA")
        self.show_welcome()

    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def show_welcome(self):
        self.clear_screen()
        main_frame = tk.Frame(self.root, bg="white", width=760, height=480)
        main_frame.place(relx=0.5, rely=0.5, anchor="center")
        main_frame.pack_propagate(False)

        branding_frame = tk.Frame(main_frame, bg="#0797A5", width=350, height=480)
        branding_frame.pack(side="left", fill="y")
        branding_frame.pack_propagate(False)
        # Logo is pre-sized with its original aspect ratio; no stretching at runtime.
        logo_path = Path(__file__).resolve().parent.parent / "assets" / "pht_logo_login.png"
        self.logo_image = tk.PhotoImage(file=str(logo_path))
        tk.Label(branding_frame, image=self.logo_image, bg="#0797A5",
                 borderwidth=0).pack(pady=(70, 10))
        tk.Label(branding_frame, text="Build better habits.\nTrack your progress.",
                 font=("Arial", 13), bg="#0797A5", fg="white",
                 justify="center").pack(pady=12)

        content = tk.Frame(main_frame, bg="white", width=410, height=480)
        content.pack(side="right", fill="both")
        content.pack_propagate(False)
        tk.Label(content, text="Welcome!", font=("Arial", 28, "bold"),
                 bg="white", fg="#123B5D").pack(pady=(80, 10))
        tk.Label(content, text="Manage your habits and monitor\nyour daily progress.",
                 font=("Arial", 12), bg="white", fg="#58717D",
                 justify="center").pack(pady=(0, 35))
        tk.Button(content, text="Login", font=("Arial", 12, "bold"),
                  bg="#0797A5", fg="white", activebackground="#067784",
                  activeforeground="white", width=25, height=2, relief="flat",
                  cursor="hand2", command=self.show_login).pack(pady=8)
        tk.Button(content, text="Create an Account", font=("Arial", 12),
                  bg="white", fg="#0797A5", activebackground="#E5F5F5",
                  activeforeground="#0797A5", width=25, height=2,
                  relief="solid", borderwidth=1, cursor="hand2",
                  command=self.show_signup).pack(pady=8)
        tk.Label(content, text="Personal Habit Tracker", font=("Arial", 9),
                 bg="white", fg="#999999").pack(side="bottom", pady=25)

    def show_login(self):
        self.clear_screen()
        frame = tk.Frame(self.root, bg="white", width=500, height=500)
        frame.place(relx=0.5, rely=0.5, anchor="center")
        frame.pack_propagate(False)
        tk.Label(frame, text="Login", font=("Arial", 28, "bold"),
                 bg="white", fg="#123B5D").pack(pady=(55, 10))
        tk.Label(frame, text="Sign in to continue to your account",
                 font=("Arial", 11), bg="white", fg="#58717D").pack(pady=(0, 30))

        tk.Label(frame, text="Username", font=("Arial", 11, "bold"),
                 bg="white", fg="#333333").pack(anchor="w", padx=80)
        self.username_entry = tk.Entry(frame, font=("Arial", 12), width=35,
                                       relief="solid", borderwidth=1)
        self.username_entry.pack(pady=(5, 18), ipady=7)

        tk.Label(frame, text="Password", font=("Arial", 11, "bold"),
                 bg="white", fg="#333333").pack(anchor="w", padx=80)
        self.password_entry = tk.Entry(frame, font=("Arial", 12), width=35,
                                       show="*", relief="solid", borderwidth=1)
        self.password_entry.pack(pady=(5, 25), ipady=7)
        self.password_entry.bind("<Return>", lambda _event: self.login())

        tk.Button(frame, text="Login", font=("Arial", 12, "bold"),
                  bg="#0797A5", fg="white", activebackground="#067784",
                  activeforeground="white", width=28, height=2, relief="flat",
                  cursor="hand2", command=self.login).pack(pady=5)
        tk.Button(frame, text="Create an Account", font=("Arial", 10),
                  bg="white", fg="#0797A5", relief="flat", cursor="hand2",
                  command=self.show_signup).pack(pady=8)
        tk.Button(frame, text="← Back", font=("Arial", 10), bg="white",
                  fg="#58717D", relief="flat", cursor="hand2",
                  command=self.show_welcome).pack()
        self.login_status_label = tk.Label(
            frame, text="", font=("Arial", 9), bg="white", fg="#B45309"
        )
        self.login_status_label.pack(pady=(6, 0))
        self.username_entry.focus_set()

    def login(self):
        """Authenticate via the user repository, then open the dashboard."""
        logger = logging.getLogger(__name__)
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showwarning(
                "Missing Information", "Enter your username and password.", parent=self.root
            )
            return
        if len(username) > 50:
            messagebox.showwarning("Invalid Username", "Username is too long.", parent=self.root)
            return

        self.login_status_label.configure(text="Checking account...", fg="#B45309")
        self.root.update_idletasks()
        try:
            user = UserController().authenticate(username, password)
            logger.info("Login accepted for username=%s role=%s", username, user["role_name"])
        except AuthenticationError:
            self.login_status_label.configure(text="Invalid username or password.", fg="#B91C1C")
            messagebox.showerror("Login Failed", "Invalid username or password.", parent=self.root)
            return
        except (DatabaseError, ValidationError) as exc:
            logger.exception("Login failed for username=%s", username)
            self.login_status_label.configure(text="Unable to complete login.", fg="#B91C1C")
            messagebox.showerror("Login Error", str(exc), parent=self.root)
            return
        except Exception as exc:
            logger.exception("Unexpected error during login for username=%s", username)
            messagebox.showerror(
                "Login Error",
                f"An unexpected error interrupted login.\n\n{type(exc).__name__}: {exc}\n\n"
                "Details were written to logs/app.log.",
                parent=self.root,
            )
            return

        try:
            from views.dashboard_window import DashboardWindow
            DashboardWindow(self.root, user)
            logger.info("Dashboard opened for username=%s", username)
        except Exception as exc:
            logger.exception("Authentication succeeded but dashboard launch failed")
            self.show_login()
            self.username_entry.insert(0, username)
            messagebox.showerror(
                "Dashboard Could Not Open",
                f"Your credentials were accepted, but the dashboard failed to start.\n\n"
                f"{type(exc).__name__}: {exc}\n\nCheck logs/app.log for the traceback.",
                parent=self.root,
            )

    def show_signup(self):
        self.clear_screen()
        frame = tk.Frame(self.root, bg="white", width=500, height=540)
        frame.place(relx=0.5, rely=0.5, anchor="center")
        frame.pack_propagate(False)
        tk.Label(frame, text="Create Your Account", font=("Arial", 24, "bold"),
                 bg="white", fg="#123B5D").pack(pady=(28, 20))

        def add_field(label, show=None):
            tk.Label(frame, text=label, font=("Arial", 10, "bold"),
                     bg="white", fg="#333333").pack(anchor="w", padx=70)
            entry = tk.Entry(frame, font=("Arial", 11), width=42, show=show)
            entry.pack(padx=70, pady=(4, 11), ipady=5, fill="x")
            return entry

        self.full_name_entry = add_field("Full Name")
        self.signup_username_entry = add_field("Username")
        self.signup_password_entry = add_field("Password", show="*")
        self.confirm_password_entry = add_field("Confirm Password", show="*")
        tk.Button(frame, text="Create Account", font=("Arial", 11, "bold"),
                  bg="#0797A5", fg="white", activebackground="#067784",
                  activeforeground="white", width=28, height=2, relief="flat",
                  cursor="hand2", command=self.create_account).pack(pady=(5, 8))
        tk.Button(frame, text="← Back to Login", font=("Arial", 10), bg="white",
                  fg="#0797A5", relief="flat", cursor="hand2",
                  command=self.show_login).pack()

    def create_account(self):
        full_name = self.full_name_entry.get().strip()
        username = self.signup_username_entry.get().strip()
        password = self.signup_password_entry.get()
        confirm = self.confirm_password_entry.get()

        if not full_name or not username or not password or not confirm:
            messagebox.showwarning("Missing Information", "Please complete all fields.", parent=self.root)
            return
        if password != confirm:
            messagebox.showerror("Password Error", "Passwords do not match.", parent=self.root)
            return

        try:
            UserController().register(full_name, username, password)
            messagebox.showinfo(
                "Account Created", "Your account has been created. You can now log in.", parent=self.root
            )
            self.show_login()
            self.username_entry.insert(0, username)
        except ValidationError as exc:
            messagebox.showwarning("Registration Details", str(exc), parent=self.root)
        except DatabaseError as exc:
            logging.getLogger(__name__).exception("Account registration failed")
            messagebox.showerror("Registration Error", str(exc), parent=self.root)
        except Exception as exc:
            logging.getLogger(__name__).exception("Unexpected account registration error")
            messagebox.showerror(
                "Registration Error",
                f"An unexpected error interrupted registration.\n{type(exc).__name__}: {exc}",
                parent=self.root,
            )
