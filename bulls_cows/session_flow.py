def start_game_phase() -> str:
    return "agent_turn"


def next_phase_after_agent_feedback(agent_status: str) -> str:
    if agent_status == "playing":
        return "human_turn"
    return "agent_result"


def next_phase_after_human_guess(player_won: bool) -> str:
    if player_won:
        return "human_result"
    return "agent_turn"
