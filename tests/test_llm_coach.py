import unittest

from bulls_cows.llm_coach import build_gemini_coach_prompt, generate_gemini_coach_tip


class LlmCoachTests(unittest.TestCase):
    def test_prompt_includes_game_state_without_secret(self):
        notes = {
            "tip": "Useful digits found. Move them around.",
            "suggested_guess": "102",
            "clue_notes": [
                {"turn": 1, "guess": "123", "response": "1 bull, 1 cow"},
            ],
        }

        prompt = build_gemini_coach_prompt(notes)

        self.assertIn("Bulls and Cows", prompt)
        self.assertIn("123 -> 1 bull, 1 cow", prompt)
        self.assertIn("102", prompt)
        self.assertIn("Do not claim to know the secret number", prompt)

    def test_generate_tip_falls_back_without_api_key(self):
        notes = {"tip": "Start with three different digits.", "clue_notes": []}

        result = generate_gemini_coach_tip(notes, api_key="")

        self.assertEqual(result["source"], "deterministic")
        self.assertEqual(result["tip"], "Start with three different digits.")

    def test_generate_tip_uses_injected_llm(self):
        class FakeMessage:
            content = "Try moving the known digit and testing two new ones."

        class FakeLlm:
            def invoke(self, prompt):
                self.prompt = prompt
                return FakeMessage()

        fake_llm = FakeLlm()
        notes = {
            "tip": "Useful digits found. Move them around.",
            "suggested_guess": "102",
            "clue_notes": [{"turn": 1, "guess": "123", "response": "1 bull, 1 cow"}],
        }

        result = generate_gemini_coach_tip(
            notes,
            api_key="test-key",
            llm_factory=lambda: fake_llm,
        )

        self.assertEqual(result["source"], "gemini")
        self.assertEqual(result["tip"], "Try moving the known digit and testing two new ones.")
        self.assertIn("123 -> 1 bull, 1 cow", fake_llm.prompt)


if __name__ == "__main__":
    unittest.main()
