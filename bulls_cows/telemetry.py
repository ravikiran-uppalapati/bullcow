from __future__ import annotations

from typing import Any

from bulls_cows.agent_graph import AgentState, apply_feedback_turn
from bulls_cows.game import CandidateFeedback

try:
    from langsmith import traceable
except Exception:
    def traceable(*args, **kwargs):
        def decorator(func):
            return func

        return decorator


@traceable(name="agent_feedback_turn", run_type="chain")
def run_traced_agent_feedback_turn(
    state: AgentState,
    feedback: CandidateFeedback,
) -> AgentState:
    return apply_feedback_turn(state, feedback)


@traceable(name="human_guess_turn", run_type="chain")
def record_human_guess_turn(
    guess: str,
    bulls: int,
    cows: int,
    won: bool,
    turn: int,
) -> dict[str, Any]:
    return {
        "actor": "human",
        "turn": turn,
        "guess": guess,
        "feedback": {"bulls": bulls, "cows": cows},
        "status": "won" if won else "playing",
    }


@traceable(name="llm_agent_message", run_type="llm")
def record_llm_agent_message(
    role: str,
    source: str,
    message: str,
    context: dict[str, Any],
) -> dict[str, Any]:
    return {
        "role": role,
        "source": source,
        "message": message,
        "context": context,
    }
