import unittest

from bulls_cows.toolbelt import build_agent_toolbelt


class ToolbeltTests(unittest.TestCase):
    def test_toolbelt_marks_core_solver_tools_as_used_after_agent_feedback(self):
        game_memory = {
            "phase": "human_turn",
            "agent": {
                "current_guess": "123",
                "candidate_count": 42,
                "history": [
                    {
                        "guess": "102",
                        "bulls": 0,
                        "cows": 1,
                        "candidates_before": 648,
                        "candidates_after": 126,
                    }
                ],
            },
            "human": {"history": []},
            "coach": {"suggested_guess": "103"},
        }

        tools = build_agent_toolbelt(
            game_memory,
            chat_history=[],
            tracing_enabled=True,
            gemini_enabled=False,
        )

        by_name = {tool["name"]: tool for tool in tools}
        self.assertEqual(by_name["score_guess"]["status"], "used")
        self.assertEqual(by_name["filter_candidates"]["status"], "used")
        self.assertEqual(by_name["choose_next_guess"]["evidence"], "Next guess: 123")
        self.assertEqual(by_name["langsmith_trace"]["status"], "watching")

    def test_toolbelt_marks_chat_and_gemini_tools_when_available(self):
        game_memory = {
            "phase": "agent_turn",
            "agent": {"current_guess": "102", "candidate_count": 648, "history": []},
            "human": {"history": [{"guess": "427", "bulls": 0, "cows": 2}]},
            "coach": {"suggested_guess": "103"},
        }

        tools = build_agent_toolbelt(
            game_memory,
            chat_history=[{"question": "What should I do?", "answer": "Try 103."}],
            tracing_enabled=False,
            gemini_enabled=True,
        )

        by_name = {tool["name"]: tool for tool in tools}
        self.assertEqual(by_name["gemini_chat"]["status"], "used")
        self.assertEqual(by_name["coach_memory"]["status"], "used")
        self.assertEqual(by_name["llm_reasoning"]["status"], "ready")


if __name__ == "__main__":
    unittest.main()
