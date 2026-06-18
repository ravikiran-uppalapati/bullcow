import unittest

from bulls_cows.llm_coach import (
    build_gemini_coach_prompt,
    build_gemini_opponent_prompt,
    generate_gemini_agent_message,
    generate_gemini_coach_tip,
)


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

    def test_opponent_prompt_asks_for_playful_sledging_without_insults(self):
        prompt = build_gemini_opponent_prompt(
            current_guess="102",
            turn=1,
            candidate_count=648,
            reasoning="Starting from all valid numbers.",
        )

        self.assertIn("Opponent Agent", prompt)
        self.assertIn("102", prompt)
        self.assertIn("playful", prompt)
        self.assertIn("no insults", prompt.lower())

    def test_generate_agent_message_uses_injected_llm(self):
        class FakeMessage:
            content = "I am opening with 102. Let's see if your secret survives this."

        class FakeLlm:
            def invoke(self, prompt):
                self.prompt = prompt
                return FakeMessage()

        fake_llm = FakeLlm()

        result = generate_gemini_agent_message(
            "opponent",
            {
                "current_guess": "102",
                "turn": 1,
                "candidate_count": 648,
                "reasoning": "Starting from all valid numbers.",
            },
            api_key="test-key",
            llm_factory=lambda: fake_llm,
        )

        self.assertEqual(result["source"], "gemini")
        self.assertIn("102", result["message"])
        self.assertIn("102", fake_llm.prompt)


if __name__ == "__main__":
    unittest.main()
