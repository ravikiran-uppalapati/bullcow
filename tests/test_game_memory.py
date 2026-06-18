import unittest

from bulls_cows.memory import build_game_memory


class GameMemoryTests(unittest.TestCase):
    def test_build_game_memory_includes_both_agent_and_human_histories(self):
        agent_state = {
            "turn": 3,
            "current_guess": "345",
            "candidates": ["345", "354"],
            "status": "playing",
            "reasoning": "The latest feedback eliminated 40 candidates.",
            "history": [
                {
                    "turn": 1,
                    "guess": "102",
                    "bulls": 0,
                    "cows": 1,
                    "candidates_before": 648,
                    "candidates_after": 126,
                    "next_guess": "123",
                    "status": "playing",
                },
                {
                    "turn": 2,
                    "guess": "123",
                    "bulls": 1,
                    "cows": 1,
                    "candidates_before": 126,
                    "candidates_after": 2,
                    "next_guess": "345",
                    "status": "playing",
                },
            ],
        }
        player_history = [
            {"turn": 1, "guess": "427", "bulls": 0, "cows": 2, "status": "playing"},
            {"turn": 2, "guess": "274", "bulls": 1, "cows": 1, "status": "playing"},
        ]
        notes = {
            "attempts": 2,
            "suggested_guess": "407",
            "tip": "Useful digits found. Move them around.",
            "previous_guesses": ["427", "274"],
        }

        memory = build_game_memory(agent_state, player_history, notes, "human_turn")

        self.assertEqual(memory["phase"], "human_turn")
        self.assertEqual(memory["agent"]["current_guess"], "345")
        self.assertEqual(memory["agent"]["candidate_count"], 2)
        self.assertEqual(len(memory["agent"]["history"]), 2)
        self.assertEqual(memory["human"]["history"][1]["guess"], "274")
        self.assertEqual(memory["coach"]["suggested_guess"], "407")
        self.assertIn("agent turn 1", memory["timeline"][0].lower())
        self.assertIn("human turn 2", memory["timeline"][-1].lower())


if __name__ == "__main__":
    unittest.main()
