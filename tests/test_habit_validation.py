import unittest

from validators.habit_validator import (
    HabitValidationError, validate_habit_data, validate_reminder_settings,
)


class HabitValidationTests(unittest.TestCase):
    def test_valid_habit_is_trimmed(self):
        result = validate_habit_data("  Drink Water  ", "Health", "  8 glasses  ", "Daily")
        self.assertEqual(result["habit_name"], "Drink Water")
        self.assertEqual(result["description"], "8 glasses")

    def test_empty_name_is_rejected(self):
        with self.assertRaises(HabitValidationError):
            validate_habit_data("  ", "Health", "", "Daily")

    def test_long_name_is_rejected(self):
        with self.assertRaises(HabitValidationError):
            validate_habit_data("x" * 101, "Health", "", "Daily")

    def test_category_over_50_characters_is_rejected(self):
        with self.assertRaises(HabitValidationError):
            validate_habit_data("Read", "x" * 51, "", "Daily")

    def test_predefined_new_category_is_accepted(self):
        result = validate_habit_data("Exercise", "Fitness", "Walk daily", "Daily")
        self.assertEqual(result["category"], "Fitness")

    def test_custom_category_is_accepted_and_trimmed(self):
        result = validate_habit_data("Journal", "  Spirituality  ", "Reflect", "Daily")
        self.assertEqual(result["category"], "Spirituality")

    def test_empty_category_is_rejected(self):
        with self.assertRaises(HabitValidationError):
            validate_habit_data("Journal", "   ", "Reflect", "Daily")

    def test_long_category_is_rejected(self):
        with self.assertRaises(HabitValidationError):
            validate_habit_data("Journal", "x" * 51, "Reflect", "Daily")

    def test_invalid_frequency_is_rejected(self):
        with self.assertRaises(HabitValidationError):
            validate_habit_data("Read", "Productivity", "", "Whenever")

    def test_valid_enabled_reminder_is_normalized(self):
        result = validate_reminder_settings(" 18:30 ", True)
        self.assertEqual(result, {"reminder_time": "18:30", "reminder_enabled": True})

    def test_disabled_reminder_discards_time(self):
        result = validate_reminder_settings("18:30", False)
        self.assertEqual(result, {"reminder_time": None, "reminder_enabled": False})

    def test_invalid_enabled_reminder_is_rejected(self):
        for value in ("9:00", "24:00", "12:60", "not a time", ""):
            with self.subTest(value=value):
                with self.assertRaises(HabitValidationError):
                    validate_reminder_settings(value, True)

    def test_long_description_is_rejected(self):
        with self.assertRaises(HabitValidationError):
            validate_habit_data("Read", "Productivity", "x" * 2001, "Daily")


if __name__ == "__main__":
    unittest.main()
