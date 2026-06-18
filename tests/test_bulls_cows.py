import unittest

from bulls_cows.game import (
    CandidateFeedback,
    generate_candidates,
    is_valid_secret,
    is_valid_feedback,
    score_guess,
)
from bulls_cows.solver import filter_candidates, next_guess


class BullsCowsGameTests(unittest.TestCase):
    def test_scores_exact_match_as_three_bulls(self):
        self.assertEqual(score_guess("123", "123"), CandidateFeedback(bulls=3, cows=0))

    def test_scores_reordered_digits_as_cows(self):
        self.assertEqual(score_guess("123", "132"), CandidateFeedback(bulls=1, cows=2))

    def test_scores_no_overlap_as_zero_feedback(self):
        self.assertEqual(score_guess("123", "456"), CandidateFeedback(bulls=0, cows=0))

    def test_generates_all_valid_three_digit_candidates(self):
        candidates = generate_candidates()

        self.assertEqual(len(candidates), 648)
        self.assertTrue(all(is_valid_secret(candidate) for candidate in candidates))
        self.assertIn("102", candidates)
        self.assertNotIn("012", candidates)
        self.assertNotIn("112", candidates)

    def test_filters_candidates_to_feedback_consistent_values(self):
        candidates = ["123", "132", "456", "124"]

        filtered = filter_candidates(candidates, guess="123", feedback=CandidateFeedback(1, 2))

        self.assertEqual(filtered, ["132"])

    def test_next_guess_is_deterministic_first_candidate(self):
        self.assertEqual(next_guess(["427", "123", "987"]), "427")

    def test_next_guess_returns_none_for_conflict(self):
        self.assertIsNone(next_guess([]))

    def test_feedback_is_valid_only_for_possible_bulls_and_cows(self):
        self.assertTrue(is_valid_feedback(0, 0))
        self.assertTrue(is_valid_feedback(3, 0))
        self.assertFalse(is_valid_feedback(-1, 0))
        self.assertFalse(is_valid_feedback(4, 0))
        self.assertFalse(is_valid_feedback(0, 4))
        self.assertFalse(is_valid_feedback(2, 2))


if __name__ == "__main__":
    unittest.main()
