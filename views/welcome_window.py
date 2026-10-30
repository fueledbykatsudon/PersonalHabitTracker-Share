"""Compatibility wrapper for the current welcome/login flow."""

from views.login_window import LoginWindow


class WelcomeWindow:
    """Redirect older navigation paths to the single current login flow."""

    def __init__(self, root):
        self.root = root
        self.window = LoginWindow(root)

    def open_login(self):
        self.window.show_login()

    def open_signup(self):
        self.window.show_signup()
