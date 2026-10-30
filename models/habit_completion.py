"""Encapsulated daily completion model."""

from datetime import date

from core.exceptions import ValidationError


class HabitCompletion:
    def __init__(self, habit_id: int, completion_date: date, completed: bool = False):
        self.habit_id = habit_id
        self.completion_date = completion_date
        self.completed = completed

    @property
    def habit_id(self) -> int:
        return self.__habit_id

    @habit_id.setter
    def habit_id(self, value: int) -> None:
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise ValidationError("Habit ID must be a positive integer.")
        self.__habit_id = value

    @property
    def completion_date(self) -> date:
        return self.__completion_date

    @completion_date.setter
    def completion_date(self, value: date) -> None:
        if not isinstance(value, date):
            raise ValidationError("Completion date must be a date value.")
        self.__completion_date = value

    @property
    def completed(self) -> bool:
        return self.__completed

    @completed.setter
    def completed(self, value: bool) -> None:
        if not isinstance(value, bool):
            raise ValidationError("Completed status must be True or False.")
        self.__completed = value

    def mark_complete(self) -> None:
        self.completed = True

    def reset(self) -> None:
        self.completed = False
