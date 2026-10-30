"""Compatibility wrapper; registration is implemented in LoginWindow."""

from views.login_window import LoginWindow


class SignupWindow:
    def __init__(self, root):
        self.window = LoginWindow(root)
        self.window.show_signup()
