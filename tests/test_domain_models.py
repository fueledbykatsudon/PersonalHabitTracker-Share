"""Tests for encapsulated habit domain models."""

import unittest
from datetime import date

from core.exceptions import ValidationError
from models.habit import Habit
from models.habit_completion import HabitCompletion
from validators.habit_validator import HabitValidationError


class HabitModelTests(unittest.TestCase):
    def test_habit_normalizes_fields_and_returns_record(self):
        habit = Habit(7, " Read 20 Minutes ", "Productivity", " Read a book ", "Daily")
        row = habit.to_record()
        self.assertEqual(row["habit_name"], "Read 20 Minutes")
        self.assertEqual(row["description"], "Read a book")
        self.assertEqual(row["user_id"], 7)

    def test_habit_property_setter_rejects_empty_category(self):
        habit = Habit(7, "Read", "Health", "", "Daily")
        with self.assertRaises(ValidationError):
            habit.category = "   "

    def test_habit_property_setter_accepts_custom_category(self):
        habit = Habit(7, "Read", "Health", "", "Daily")
        habit.category = "Spirituality"
        self.assertEqual(habit.category, "Spirituality")

    def test_habit_accepts_custom_category(self):
        habit = Habit(7, "Journal", "Spirituality", "Reflect", "Daily")
        self.assertEqual(habit.category, "Spirituality")

    def test_habit_rejects_empty_name(self):
        with self.assertRaises(HabitValidationError):
            Habit(7, "", "Health", "", "Daily")


class HabitCompletionModelTests(unittest.TestCase):
    def test_completion_can_be_marked_and_reset(self):
        completion = HabitCompletion(3, date(2026, 10, 15), False)
        completion.mark_complete()
        self.assertTrue(completion.completed)
        completion.reset()
        self.assertFalse(completion.completed)

    def test_completion_property_validates_types(self):
        with self.assertRaises(ValidationError):
            HabitCompletion(0, date.today(), False)
        completion = HabitCompletion(1, date.today(), False)
        with self.assertRaises(ValidationError):
            completion.completed = "yes"


if __name__ == "__main__":
    unittest.main()
