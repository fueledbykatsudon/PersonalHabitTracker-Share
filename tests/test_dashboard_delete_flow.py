"""Regression tests for the Dashboard's visible Delete Selected action path."""
import unittest
from unittest.mock import Mock, patch

from views.dashboard_window import DashboardWindow


class DashboardDeleteFlowTests(unittest.TestCase):
    def setUp(self):
        # Exercise the action handler without creating a real Tk window or DB.
        self.app = DashboardWindow.__new__(DashboardWindow)
        self.app.root = Mock(name="page_container")
        self.app.user = {"user_id": 17}
        self.app.tree = Mock(name="habit_tree")
        self.app.repository = Mock(name="habit_controller")
        self.app.habits_by_id = {
            8: {"habit_id": 8, "habit_name": "Read for 20 Minutes"}
        }
        self.app.refresh_data = Mock(name="refresh_data")
        self.app.tree.exists.return_value = True
        self.app.tree.selection.return_value = ("8",)
        self.app.tree.focus.return_value = "8"

    @patch("views.dashboard_window.messagebox.showinfo")
    @patch("views.dashboard_window.messagebox.askyesno", return_value=True)
    def test_confirmed_delete_uses_selected_habit_and_refreshes(self, _ask, _info):
        self.app.delete_selected()
        self.app.repository.delete.assert_called_once_with(17, 8)
        self.app.refresh_data.assert_called_once_with()

    @patch("views.dashboard_window.messagebox.showinfo")
    @patch("views.dashboard_window.messagebox.askyesno", return_value=False)
    def test_cancelled_delete_does_not_mutate_repository(self, _ask, _info):
        self.app.delete_selected()
        self.app.repository.delete.assert_not_called()
        self.app.refresh_data.assert_not_called()

    @patch("views.dashboard_window.messagebox.showinfo")
    @patch("views.dashboard_window.messagebox.askyesno", return_value=True)
    def test_focused_row_is_used_when_tree_selection_is_empty(self, _ask, _info):
        self.app.tree.selection.return_value = ()
        self.app.tree.focus.return_value = "8"
        self.app.delete_selected()
        self.app.repository.delete.assert_called_once_with(17, 8)

    @patch("views.dashboard_window.messagebox.showwarning")
    def test_no_selected_or_focused_row_shows_warning(self, warning):
        self.app.tree.selection.return_value = ()
        self.app.tree.focus.return_value = ""
        self.app.tree.exists.return_value = False
        self.app.delete_selected()
        warning.assert_called_once()
        self.app.repository.delete.assert_not_called()


if __name__ == "__main__":
    unittest.main()
