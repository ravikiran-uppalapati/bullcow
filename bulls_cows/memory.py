from __future__ import annotations

from typing import Any


def build_game_memory(
    agent_state: dict[str, Any],
    player_history: list[dict[str, Any]],
    coach_notes: dict[str, Any],
    phase: str,
) -> dict[str, Any]:
    agent_history = list(agent_state.get("history", []))
    human_history = list(player_history)

    return {
        "phase": phase,
        "agent": {
            "turn": agent_state.get("turn", 1),
            "current_guess": agent_state.get("current_guess"),
            "status": agent_state.get("status", "playing"),
            "candidate_count": len(agent_state.get("candidates", [])),
            "reasoning": agent_state.get("reasoning", ""),
            "history": agent_history,
        },
        "human": {
            "turn": len(human_history) + 1,
            "history": human_history,
        },
        "coach": {
            "attempts": coach_notes.get("attempts", len(human_history)),
            "suggested_guess": coach_notes.get("suggested_guess", ""),
            "tip": coach_notes.get("tip", ""),
            "used_digits": coach_notes.get("used_digits", []),
            "previous_guesses": coach_notes.get("previous_guesses", []),
        },
        "timeline": _build_timeline(agent_history, human_history),
    }


def _build_timeline(
    agent_history: list[dict[str, Any]],
    human_history: list[dict[str, Any]],
) -> list[str]:
    events: list[tuple[float, str]] = []

    for item in agent_history:
        turn = int(item.get("turn", 0))
        before = item.get("candidates_before", "?")
        after = item.get("candidates_after", "?")
        events.append(
            (
                turn,
                "Agent turn "
                f"{turn} guessed {item.get('guess')} and got "
                f"{item.get('bulls')} bulls, {item.get('cows')} cows; "
                f"candidates went from {before} to {after}.",
            )
        )

    for item in human_history:
        turn = int(item.get("turn", 0))
        events.append(
            (
                turn + 0.5,
                "Human turn "
                f"{turn} guessed {item.get('guess')} and got "
                f"{item.get('bulls')} bulls, {item.get('cows')} cows.",
            )
        )

    return [event for _, event in sorted(events, key=lambda item: item[0])]
