"""Encapsulated Habit domain model."""

from __future__ import annotations

from typing import Any

from validators.habit_validator import validate_habit_data
from core.exceptions import ValidationError


class Habit:
    """Validated habit entity using private attributes and property setters."""

    def __init__(
        self,
        user_id: int,
        habit_name: str,
        category: str,
        description: str,
        target_frequency: str,
        habit_id: int | None = None,
        created_at: Any = None,
    ):
        self.user_id = user_id
        self.habit_id = habit_id
        values = validate_habit_data(habit_name, category, description, target_frequency)
        self.habit_name = values["habit_name"]
        self.category = values["category"]
        self.description = values["description"]
        self.target_frequency = values["target_frequency"]
        self.created_at = created_at

    @property
    def habit_id(self) -> int | None:
        return self.__habit_id

    @habit_id.setter
    def habit_id(self, value: int | None) -> None:
        if value is not None and (isinstance(value, bool) or not isinstance(value, int) or value < 1):
            raise ValidationError("Habit ID must be a positive integer or None.")
        self.__habit_id = value

    @property
    def user_id(self) -> int:
        return self.__user_id

    @user_id.setter
    def user_id(self, value: int) -> None:
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValidationError("User ID must be a positive integer.")
        self.__user_id = value

    @property
    def habit_name(self) -> str:
        return self.__habit_name

    @habit_name.setter
    def habit_name(self, value: str) -> None:
        if not isinstance(value, str) or not value.strip() or len(value.strip()) > 100:
            raise ValidationError("Habit name must contain 1–100 characters.")
        self.__habit_name = value.strip()

    @property
    def category(self) -> str:
        return self.__category

    @category.setter
    def category(self, value: str) -> None:
        if not isinstance(value, str) or not value.strip() or len(value.strip()) > 50:
            raise ValidationError("Category must contain 1–50 characters.")
        if any(ord(character) < 32 for character in value.strip()):
            raise ValidationError("Category contains unsupported characters.")
        self.__category = value.strip()

    @property
    def description(self) -> str:
        return self.__description

    @description.setter
    def description(self, value: str) -> None:
        if not isinstance(value, str) or len(value.strip()) > 2000:
            raise ValidationError("Description must be text with at most 2,000 characters.")
        self.__description = value.strip()

    @property
    def target_frequency(self) -> str:
        return self.__target_frequency

    @target_frequency.setter
    def target_frequency(self, value: str) -> None:
        valid = {"Daily", "Weekly", "Monthly"}
        if not isinstance(value, str) or value.strip() not in valid:
            raise ValidationError("Please select a valid target frequency.")
        self.__target_frequency = value.strip()

    @property
    def created_at(self):
        return self.__created_at

    @created_at.setter
    def created_at(self, value) -> None:
        self.__created_at = value

    def to_record(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "habit_name": self.habit_name,
            "category": self.category,
            "description": self.description,
            "target_frequency": self.target_frequency,
            "habit_id": self.habit_id,
            "created_at": self.created_at,
        }
