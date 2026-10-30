"""Field validation for creating and updating habits."""


class HabitValidationError(ValueError):
    """Raised when habit data fails application validation."""


ALLOWED_CATEGORIES = {
    "Health", "Productivity", "Lifestyle", "Learning", "Fitness",
    "Mental Wellness", "Finance", "Relationships",
}
MAX_CATEGORY_LENGTH = 50
ALLOWED_FREQUENCIES = {"Daily", "Weekly", "Monthly"}


def validate_habit_data(
    habit_name: str,
    category: str,
    description: str,
    target_frequency: str,
) -> dict[str, str]:
    """Normalize and validate fields before they reach SQL statements."""
    if not isinstance(habit_name, str):
        raise HabitValidationError("Habit name must be text.")
    name = habit_name.strip()
    if not name:
        raise HabitValidationError("Please enter a habit name.")
    if len(name) > 100:
        raise HabitValidationError("Habit name must be 100 characters or fewer.")
    if any(ord(character) < 32 and character not in "\t" for character in name):
        raise HabitValidationError("Habit name contains unsupported control characters.")

    if not isinstance(category, str):
        raise HabitValidationError("Please choose or enter a category.")
    clean_category = category.strip()
    if not clean_category:
        raise HabitValidationError("Please choose or enter a category.")
    if len(clean_category) > MAX_CATEGORY_LENGTH:
        raise HabitValidationError(
            f"Category must be {MAX_CATEGORY_LENGTH} characters or fewer."
        )
    if any(ord(character) < 32 for character in clean_category):
        raise HabitValidationError("Category contains unsupported characters.")

    if not isinstance(description, str):
        raise HabitValidationError("Description must be text.")
    clean_description = description.strip()
    if len(clean_description) > 2000:
        raise HabitValidationError("Description must be 2,000 characters or fewer.")

    if not isinstance(target_frequency, str) or target_frequency.strip() not in ALLOWED_FREQUENCIES:
        raise HabitValidationError("Please select a valid target frequency.")

    return {
        "habit_name": name,
        "category": clean_category,
        "description": clean_description,
        "target_frequency": target_frequency.strip(),
    }


def validate_reminder_settings(reminder_time, reminder_enabled) -> dict:
    """Validate optional daily reminder settings in 24-hour HH:MM format."""
    enabled = bool(reminder_enabled)
    if not enabled:
        return {"reminder_time": None, "reminder_enabled": False}

    if not isinstance(reminder_time, str):
        raise HabitValidationError("Enter a reminder time in 24-hour HH:MM format, such as 18:30.")
    clean_time = reminder_time.strip()
    import re
    if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", clean_time):
        raise HabitValidationError("Enter a valid reminder time in 24-hour HH:MM format, such as 18:30.")
    return {"reminder_time": clean_time, "reminder_enabled": True}
