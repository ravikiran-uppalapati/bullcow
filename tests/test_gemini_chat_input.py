import unittest

import main


class GeminiChatInputTests(unittest.TestCase):
    def test_optional_exact_feedback_returns_none_for_free_text(self):
        result = main.build_optional_exact_feedback(
            "my number is 427",
            "102",
        )

        self.assertIsNone(result)

    def test_optional_exact_feedback_scores_valid_secret(self):
        result = main.build_optional_exact_feedback("427", "472")

        self.assertEqual(result, {"bulls": 1, "cows": 2, "agent_guess": "472"})


if __name__ == "__main__":
    unittest.main()
