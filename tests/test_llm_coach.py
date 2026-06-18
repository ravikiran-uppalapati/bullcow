import unittest

from bulls_cows.llm_coach import (
    build_gemini_chat_prompt,
    build_gemini_coach_prompt,
    build_gemini_opponent_prompt,
    build_gemini_referee_prompt,
    format_game_memory_for_prompt,
    generate_gemini_agent_message,
    generate_gemini_chat_response,
    generate_gemini_coach_tip,
    generate_gemini_referee_help,
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

    def test_generate_tip_can_include_game_memory(self):
        class FakeMessage:
            content = "Use 407 because your earlier 427 clue says 7 is useful."

        class FakeLlm:
            def invoke(self, prompt):
                self.prompt = prompt
                return FakeMessage()

        fake_llm = FakeLlm()
        notes = {
            "tip": "Useful digits found. Move them around.",
            "suggested_guess": "407",
            "clue_notes": [{"turn": 1, "guess": "427", "response": "0 bulls, 2 cows"}],
        }
        memory = {
            "phase": "human_turn",
            "agent": {"history": []},
            "human": {"history": [{"turn": 1, "guess": "427", "bulls": 0, "cows": 2}]},
            "coach": {"suggested_guess": "407", "tip": "Useful digits found."},
            "timeline": ["Human turn 1 guessed 427 and got 0 bulls, 2 cows."],
        }

        result = generate_gemini_coach_tip(
            notes,
            api_key="test-key",
            game_memory=memory,
            llm_factory=lambda: fake_llm,
        )

        self.assertEqual(result["source"], "gemini")
        self.assertIn("Human turn 1 guessed 427", fake_llm.prompt)

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

    def test_game_memory_format_includes_full_duel_history(self):
        memory = {
            "phase": "human_turn",
            "agent": {
                "turn": 2,
                "current_guess": "123",
                "candidate_count": 126,
                "reasoning": "Eliminated many candidates.",
                "history": [
                    {
                        "turn": 1,
                        "guess": "102",
                        "bulls": 0,
                        "cows": 1,
                        "candidates_before": 648,
                        "candidates_after": 126,
                    }
                ],
            },
            "human": {
                "turn": 2,
                "history": [
                    {"turn": 1, "guess": "427", "bulls": 0, "cows": 2},
                ],
            },
            "coach": {"suggested_guess": "407", "tip": "Move useful digits around."},
            "timeline": [
                "Agent turn 1 guessed 102 and got 0 bulls, 1 cow.",
                "Human turn 1 guessed 427 and got 0 bulls, 2 cows.",
            ],
        }

        text = format_game_memory_for_prompt(memory)

        self.assertIn("Current phase: human_turn", text)
        self.assertIn("Agent turn 1 guessed 102", text)
        self.assertIn("Human turn 1 guessed 427", text)
        self.assertIn("Suggested human guess: 407", text)

    def test_agent_prompt_includes_game_memory_when_provided(self):
        memory = {
            "phase": "agent_turn",
            "agent": {"history": []},
            "human": {"history": [{"turn": 1, "guess": "427", "bulls": 0, "cows": 2}]},
            "coach": {"suggested_guess": "407", "tip": "Move useful digits around."},
            "timeline": ["Human turn 1 guessed 427 and got 0 bulls, 2 cows."],
        }

        prompt = build_gemini_opponent_prompt(
            current_guess="123",
            turn=2,
            candidate_count=126,
            reasoning="Eliminated many candidates.",
            game_memory=memory,
        )

        self.assertIn("Full session memory", prompt)
        self.assertIn("Human turn 1 guessed 427", prompt)

    def test_referee_prompt_includes_secret_guess_and_exact_feedback(self):
        prompt = build_gemini_referee_prompt(
            secret="427",
            agent_guess="472",
            bulls=1,
            cows=2,
            question="How should I respond?",
        )

        self.assertIn("427", prompt)
        self.assertIn("472", prompt)
        self.assertIn("1 bull", prompt)
        self.assertIn("2 cows", prompt)
        self.assertIn("How should I respond?", prompt)

    def test_generate_referee_help_uses_injected_llm(self):
        class FakeMessage:
            content = "Reply with 1 bull and 2 cows."

        class FakeLlm:
            def invoke(self, prompt):
                self.prompt = prompt
                return FakeMessage()

        fake_llm = FakeLlm()

        result = generate_gemini_referee_help(
            secret="427",
            agent_guess="472",
            bulls=1,
            cows=2,
            question="How should I respond?",
            api_key="test-key",
            llm_factory=lambda: fake_llm,
        )

        self.assertEqual(result["source"], "gemini")
        self.assertEqual(result["message"], "Reply with 1 bull and 2 cows.")
        self.assertIn("427", fake_llm.prompt)

    def test_chat_prompt_includes_question_and_game_memory(self):
        memory = {
            "phase": "agent_turn",
            "agent": {"current_guess": "102", "candidate_count": 648},
            "human": {"history": []},
            "coach": {"suggested_guess": "103", "tip": "Start with different digits."},
            "timeline": ["Agent turn 1 guessed 102 and got pending feedback."],
        }

        prompt = build_gemini_chat_prompt(
            question="How should I think about this move?",
            game_memory=memory,
            exact_feedback={"bulls": 1, "cows": 1, "agent_guess": "102"},
        )

        self.assertIn("How should I think about this move?", prompt)
        self.assertIn("Agent turn 1 guessed 102", prompt)
        self.assertIn("Exact feedback available: 1 bulls, 1 cows", prompt)

    def test_generate_chat_response_uses_injected_llm(self):
        class FakeMessage:
            content = "Give 1 bull and 1 cow, then use that clue for your next move."

        class FakeLlm:
            def invoke(self, prompt):
                self.prompt = prompt
                return FakeMessage()

        fake_llm = FakeLlm()

        result = generate_gemini_chat_response(
            question="What should I do?",
            api_key="test-key",
            game_memory={"phase": "agent_turn", "timeline": []},
            llm_factory=lambda: fake_llm,
        )

        self.assertEqual(result["source"], "gemini")
        self.assertIn("Give 1 bull", result["message"])
        self.assertIn("What should I do?", fake_llm.prompt)


if __name__ == "__main__":
    unittest.main()
