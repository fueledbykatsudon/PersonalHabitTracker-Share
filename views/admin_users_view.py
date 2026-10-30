"""Admin-only, read-only view of registered users and audit records."""

import tkinter as tk
from tkinter import ttk, messagebox

from core.exceptions import DatabaseError
from models.accounts import account_from_user_record
from controllers.user_controller import UserController
from controllers.audit_log_controller import AuditLogController


from views.navigation import get_page_container, clear_page

class AdminUsersView:
    def __init__(self, root, user):
        self.window = root
        self.root = get_page_container(root)
        self.user = dict(user)
        self.account = account_from_user_record(self.user)
        self.user["role_name"] = self.account.role_name
        self.clear_window()

        if not self.account.can_manage_users:
            messagebox.showerror("Access Denied", "Only an administrator can open this page.")
            from views.dashboard_window import DashboardWindow
            DashboardWindow(self.window, self.user)
            return

        self.window.title("Personal Habit Tracker - Administration")
        self.window.geometry("1120x740")
        self.window.minsize(1000, 650)
        self.window.resizable(True, True)
        self.window.configure(bg="#F3F9FA")

        header = tk.Frame(self.root, bg="#F3F9FA")
        header.pack(fill="x", padx=28, pady=(22, 12))
        tk.Label(header, text="Administration", font=("Arial", 23, "bold"),
                 fg="#0D2D48", bg="#F3F9FA").pack(side="left")
        tk.Button(header, text="← Back to Dashboard", command=self.go_back,
                  cursor="hand2").pack(side="right")

        tk.Label(self.root,
                 text="Admin-only view. Password hashes are never displayed.",
                 font=("Arial", 10), fg="#58717D", bg="#F3F9FA").pack(
                     anchor="w", padx=30, pady=(0, 12))

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=28, pady=(0, 24))
        users_tab = ttk.Frame(notebook, padding=12)
        audit_tab = ttk.Frame(notebook, padding=12)
        notebook.add(users_tab, text="Registered Users")
        notebook.add(audit_tab, text="Audit Log")

        self.users_tree = ttk.Treeview(
            users_tab,
            columns=("id", "full_name", "username", "role", "created_at"),
            show="headings", height=18,
        )
        for column, title, width in (
            ("id", "ID", 65),
            ("full_name", "Full Name", 220),
            ("username", "Username", 170),
            ("role", "Role", 140),
            ("created_at", "Created At", 230),
        ):
            self.users_tree.heading(column, text=title)
            self.users_tree.column(column, width=width, anchor="w")
        self.users_tree.pack(fill="both", expand=True)

        self.audit_tree = ttk.Treeview(
            audit_tab,
            columns=("id", "username", "action", "description", "created_at"),
            show="headings", height=18,
        )
        for column, title, width in (
            ("id", "Log ID", 65),
            ("username", "User", 125),
            ("action", "Action", 140),
            ("description", "Description", 320),
            ("created_at", "Created At", 190),
        ):
            self.audit_tree.heading(column, text=title)
            self.audit_tree.column(column, width=width, anchor="w")
        self.audit_tree.pack(fill="both", expand=True)

        refresh = ttk.Button(self.root, text="Refresh Data", command=self.load_data)
        refresh.pack(anchor="e", padx=30, pady=(0, 10))
        self.load_data()

    def clear_window(self):
        clear_page(self.root)

    def load_data(self):
        for tree in (getattr(self, "users_tree", None), getattr(self, "audit_tree", None)):
            if tree is not None:
                for item in tree.get_children():
                    tree.delete(item)

        try:
            users = UserController().list_users()
            logs = AuditLogController().list_recent(200)
            for row in users:
                self.users_tree.insert("", "end", values=(
                    row["user_id"], row["full_name"], row["username"],
                    row["role_name"], row["created_at"],
                ))
            for row in logs:
                self.audit_tree.insert("", "end", values=(
                    row["log_id"], row["username"], row["action"],
                    row["description"] or "", row["created_at"],
                ))
        except DatabaseError as exc:
            messagebox.showerror("Database Error", str(exc), parent=self.root)

    def go_back(self):
        from views.dashboard_window import DashboardWindow
        DashboardWindow(self.window, self.user)
