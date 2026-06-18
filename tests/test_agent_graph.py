import unittest
import warnings

warnings.filterwarnings("ignore", message=".*allowed_objects.*", category=Warning)

from bulls_cows.agent_graph import (
    apply_feedback_turn,
    build_graph,
    create_initial_agent_state,
)
from bulls_cows.game import CandidateFeedback


class AgentGraphTests(unittest.TestCase):
    def test_initial_state_has_candidates_and_first_guess(self):
        state = create_initial_agent_state()

        self.assertEqual(state["status"], "playing")
        self.assertEqual(len(state["candidates"]), 648)
        self.assertEqual(state["current_guess"], "102")
        self.assertEqual(state["turn"], 1)

    def test_feedback_turn_filters_candidates_and_records_history(self):
        state = create_initial_agent_state()

        updated = apply_feedback_turn(state, CandidateFeedback(bulls=0, cows=1))

        self.assertLess(updated["candidate_count_after"], updated["candidate_count_before"])
        self.assertEqual(updated["history"][0]["guess"], "102")
        self.assertEqual(updated["history"][0]["bulls"], 0)
        self.assertEqual(updated["history"][0]["cows"], 1)
        self.assertEqual(updated["turn"], 2)
        self.assertEqual(updated["status"], "playing")
        self.assertIn("eliminated", updated["reasoning"].lower())

    def test_feedback_turn_detects_win(self):
        state = create_initial_agent_state()

        updated = apply_feedback_turn(state, CandidateFeedback(bulls=3, cows=0))

        self.assertEqual(updated["status"], "won")
        self.assertEqual(updated["current_guess"], "102")
        self.assertIn("solved", updated["reasoning"].lower())

    def test_feedback_turn_detects_conflict(self):
        state = create_initial_agent_state()
        state["current_guess"] = "123"

        updated = apply_feedback_turn(state, CandidateFeedback(bulls=3, cows=1))

        self.assertEqual(updated["status"], "conflict")
        self.assertIsNone(updated["current_guess"])
        self.assertIn("contradict", updated["reasoning"].lower())

    def test_compiled_graph_runs_one_feedback_turn(self):
        graph = build_graph()
        state = create_initial_agent_state()
        state["pending_feedback"] = CandidateFeedback(bulls=0, cows=1)

        updated = graph.invoke(state)

        self.assertEqual(updated["turn"], 2)
        self.assertEqual(updated["history"][0]["guess"], "102")


if __name__ == "__main__":
    unittest.main()
