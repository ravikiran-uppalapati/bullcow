import unittest

from bulls_cows.session_flow import (
    next_phase_after_agent_feedback,
    next_phase_after_human_guess,
    start_game_phase,
)


class SessionFlowTests(unittest.TestCase):
    def test_start_game_moves_from_intro_to_agent_turn(self):
        self.assertEqual(start_game_phase(), "agent_turn")

    def test_agent_feedback_moves_to_human_turn_when_agent_is_still_playing(self):
        self.assertEqual(next_phase_after_agent_feedback("playing"), "human_turn")

    def test_agent_feedback_stays_on_agent_result_when_agent_finished(self):
        self.assertEqual(next_phase_after_agent_feedback("won"), "agent_result")
        self.assertEqual(next_phase_after_agent_feedback("conflict"), "agent_result")

    def test_human_guess_moves_back_to_agent_turn_until_player_wins(self):
        self.assertEqual(next_phase_after_human_guess(False), "agent_turn")
        self.assertEqual(next_phase_after_human_guess(True), "human_result")


if __name__ == "__main__":
    unittest.main()
