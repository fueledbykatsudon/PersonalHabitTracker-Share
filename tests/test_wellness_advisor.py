import unittest

from services.wellness_advisor import RuleBasedWellnessAdvisor


class RuleBasedWellnessAdvisorTests(unittest.TestCase):
    def setUp(self):
        self.advisor = RuleBasedWellnessAdvisor()

    def test_recommends_starting_a_habit_when_user_has_none(self):
        recommendations = self.advisor.recommend({
            "total_habits": 0,
            "recorded_days": 0,
            "completed_days": 0,
            "completion_rate": 0,
            "rows": [],
        })
        self.assertIn("Start with one small habit", recommendations[0]["title"])
        self.assertEqual(len(recommendations), 3)

    def test_asks_user_to_start_tracking_when_no_days_recorded(self):
        recommendations = self.advisor.recommend({
            "total_habits": 1,
            "recorded_days": 0,
            "completed_days": 0,
            "completion_rate": 0,
            "rows": [{"habit_name": "Walk", "category": "Health", "recorded_days": 0, "completed_days": 0}],
        })
        self.assertEqual(recommendations[0]["title"], "Start recording your progress")

    def test_high_completion_rate_gets_positive_suggestion(self):
        recommendations = self.advisor.recommend({
            "total_habits": 1,
            "recorded_days": 10,
            "completed_days": 9,
            "completion_rate": 90,
            "rows": [{"habit_name": "Read", "category": "Productivity", "recorded_days": 10, "completed_days": 9}],
        })
        self.assertEqual(recommendations[0]["title"], "Your recorded consistency is strong")

    def test_low_habit_completion_generates_habit_specific_suggestion(self):
        recommendations = self.advisor.recommend({
            "total_habits": 1,
            "recorded_days": 8,
            "completed_days": 2,
            "completion_rate": 25,
            "rows": [{"habit_name": "Morning walk", "category": "Health", "recorded_days": 8, "completed_days": 2}],
        })
        self.assertEqual(recommendations[0]["title"], "Make the next step easier")
        self.assertEqual(recommendations[2]["title"], "Try adjusting: Morning walk")

    def test_limited_data_does_not_claim_a_pattern(self):
        recommendations = self.advisor.recommend({
            "total_habits": 1,
            "recorded_days": 2,
            "completed_days": 1,
            "completion_rate": 50,
            "rows": [{"habit_name": "Read", "category": "Productivity", "recorded_days": 2, "completed_days": 1}],
        })
        self.assertEqual(recommendations[0]["title"], "Build a small baseline")
        self.assertIn("limited sample", recommendations[0]["message"])

    def test_recommendations_handle_malformed_counts_without_crashing(self):
        recommendations = self.advisor.recommend({
            "total_habits": "not-a-number",
            "recorded_days": None,
            "completed_days": object(),
            "completion_rate": 1000,
            "rows": None,
        })
        self.assertEqual(len(recommendations), 3)
        self.assertTrue(all("title" in item and "message" in item for item in recommendations))


if __name__ == "__main__":
    unittest.main()
