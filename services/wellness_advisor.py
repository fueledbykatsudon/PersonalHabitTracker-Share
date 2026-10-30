"""Explainable, rule-based wellness suggestions from recorded habit progress.

This module deliberately uses straightforward rules rather than an AI model so
students can trace and explain every recommendation during a project defense.
It provides general habit-building guidance, not medical advice.
"""

from __future__ import annotations

from typing import Any, Mapping


class RuleBasedWellnessAdvisor:
    """Create a small set of suggestions from a 30-day progress report."""

    MIN_RECORDED_DAYS_FOR_PATTERN = 3
    MAX_RECOMMENDATIONS = 3

    def recommend(self, report: Mapping[str, Any]) -> list[dict[str, str]]:
        """Return up to three recommendation cards based on the supplied report."""
        raw_rows = report.get("rows", [])
        if not isinstance(raw_rows, (list, tuple)):
            raw_rows = []
        rows = [row for row in raw_rows if isinstance(row, Mapping)]
        total_habits = self._count(report.get("total_habits", len(rows)))
        recorded_days = self._count(report.get("recorded_days", 0))
        completed_days = self._count(report.get("completed_days", 0))
        completion_rate = min(100, self._count(report.get("completion_rate", 0)))

        recommendations: list[dict[str, str]] = []

        if total_habits == 0:
            recommendations.append({
                "title": "Start with one small habit",
                "message": (
                    "You have not created a habit yet. Choose one realistic action "
                    "that matters to you, add it in My Habits, and track it at a pace "
                    "that fits your routine."
                ),
            })
        elif recorded_days == 0:
            recommendations.append({
                "title": "Start recording your progress",
                "message": (
                    f"You have {total_habits} habit(s), but no habit-days recorded "
                    "in the last 30 days. Open Habit Tracking and record today's "
                    "status so future suggestions can use your activity."
                ),
            })
        elif recorded_days < self.MIN_RECORDED_DAYS_FOR_PATTERN:
            recommendations.append({
                "title": "Build a small baseline",
                "message": (
                    f"There are {recorded_days} recorded habit-day(s) in the last "
                    "30 days. Keep tracking for a few more days before drawing "
                    "conclusions from this limited sample."
                ),
            })
        elif completion_rate >= 80:
            recommendations.append({
                "title": "Your recorded consistency is strong",
                "message": (
                    f"You completed {completed_days} of {recorded_days} recorded "
                    f"habit-days ({completion_rate}%). Keep your routine realistic "
                    "and maintain the habits that are working for you."
                ),
            })
        elif completion_rate < 50:
            recommendations.append({
                "title": "Make the next step easier",
                "message": (
                    f"You completed {completed_days} of {recorded_days} recorded "
                    f"habit-days ({completion_rate}%). Consider making one habit "
                    "smaller, choosing a specific time, or linking it to a routine "
                    "you already do."
                ),
            })
        else:
            recommendations.append({
                "title": "Build on your current progress",
                "message": (
                    f"You completed {completed_days} of {recorded_days} recorded "
                    f"habit-days ({completion_rate}%). Notice which routines make "
                    "tracking easier, then repeat what works."
                ),
            })

        categories = {
            str(row.get("category") or "").strip()
            for row in rows
            if str(row.get("category") or "").strip()
        }
        if len(categories) == 1:
            category = next(iter(categories))
            recommendations.append({
                "title": "Review the balance of your routine",
                "message": (
                    f"Your current habits are all in the {category} category. "
                    "Consider whether your goals would benefit from another type "
                    "of habit, but only add one if it is useful and realistic for you."
                ),
            })
        else:
            recommendations.append({
                "title": "Keep goals manageable",
                "message": (
                    "Focus on a few habits you can realistically maintain instead "
                    "of adding many new goals at once. Small, repeatable actions "
                    "are easier to review and adjust."
                ),
            })

        low_completion = []
        for row in rows:
            name = str(row.get("habit_name") or "").strip()
            tracked = self._count(row.get("recorded_days", 0))
            completed = self._count(row.get("completed_days", 0))
            if not name or tracked < self.MIN_RECORDED_DAYS_FOR_PATTERN:
                continue
            habit_rate = min(100, round(completed * 100 / tracked))
            if habit_rate < 50:
                low_completion.append((habit_rate, name, completed, tracked))

        low_completion.sort(key=lambda item: (item[0], item[1].casefold()))
        if low_completion:
            _, name, completed, tracked = low_completion[0]
            recommendations.append({
                "title": f"Try adjusting: {name}",
                "message": (
                    f"This habit was completed on {completed} of {tracked} recorded "
                    "days. You could reduce the task to a smaller first step or "
                    "choose a more convenient time, then see whether that helps."
                ),
            })
        else:
            recommendations.append({
                "title": "Review your progress regularly",
                "message": (
                    "Check your records every week. If a habit no longer fits your "
                    "schedule or goals, update it rather than treating a missed day "
                    "as a failure."
                ),
            })

        return recommendations[: self.MAX_RECOMMENDATIONS]

    @staticmethod
    def _count(value: Any) -> int:
        """Convert report counts safely to non-negative integers."""
        try:
            return max(0, int(value or 0))
        except (TypeError, ValueError):
            return 0
