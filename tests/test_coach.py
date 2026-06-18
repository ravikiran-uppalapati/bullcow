import unittest

from bulls_cows.coach import build_coach_notes
from bulls_cows.game import CandidateFeedback, score_guess


class CoachTests(unittest.TestCase):
    def test_coach_opens_with_a_play_tip_when_no_guesses_exist(self):
        notes = build_coach_notes([])

        self.assertEqual(notes["attempts"], 0)
        self.assertEqual(notes["tip"], "Start with three different digits.")
        self.assertEqual(notes["previous_guesses"], [])
        self.assertEqual(notes["suggested_guess"], "102")

    def test_coach_lists_previous_guesses_and_used_digits(self):
        notes = build_coach_notes(
            [
                {"turn": 1, "guess": "123", "bulls": 1, "cows": 1},
                {"turn": 2, "guess": "456", "bulls": 0, "cows": 1},
            ]
        )

        self.assertEqual(notes["attempts"], 2)
        self.assertEqual(notes["previous_guesses"], ["123", "456"])
        self.assertEqual(notes["used_digits"], ["1", "2", "3", "4", "5", "6"])
        self.assertNotIn(notes["suggested_guess"], ["123", "456"])
        self.assertIn("move", notes["tip"].lower())

    def test_coach_keeps_full_clue_notes_for_each_human_guess(self):
        notes = build_coach_notes(
            [
                {"turn": 1, "guess": "123", "bulls": 1, "cows": 1},
                {"turn": 2, "guess": "456", "bulls": 0, "cows": 2},
            ]
        )

        self.assertEqual(
            notes["clue_notes"],
            [
                {
                    "turn": 1,
                    "guess": "123",
                    "response": "1 bull, 1 cow",
                    "bulls": 1,
                    "cows": 1,
                },
                {
                    "turn": 2,
                    "guess": "456",
                    "response": "0 bulls, 2 cows",
                    "bulls": 0,
                    "cows": 2,
                },
            ],
        )

    def test_coach_suggests_a_guess_consistent_with_previous_feedback(self):
        history = [
            {"turn": 1, "guess": "102", "bulls": 0, "cows": 1},
            {"turn": 2, "guess": "103", "bulls": 0, "cows": 0},
            {"turn": 3, "guess": "104", "bulls": 0, "cows": 1},
        ]

        notes = build_coach_notes(history)

        self.assertNotIn(notes["suggested_guess"], ["102", "103", "104"])
        for item in history:
            self.assertEqual(
                score_guess(notes["suggested_guess"], item["guess"]),
                CandidateFeedback(item["bulls"], item["cows"]),
            )
        self.assertGreater(notes["possible_count"], 0)
        self.assertIn("consistent", notes["reasoning"].lower())


if __name__ == "__main__":
    unittest.main()
