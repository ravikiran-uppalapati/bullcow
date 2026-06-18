from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from bulls_cows.game import CandidateFeedback, generate_candidates
from bulls_cows.solver import filter_candidates, next_guess


class AgentState(TypedDict, total=False):
    candidates: list[str]
    current_guess: str | None
    pending_feedback: CandidateFeedback | None
    history: list[dict[str, Any]]
    turn: int
    status: str
    candidate_count_before: int
    candidate_count_after: int
    reasoning: str


def create_initial_agent_state() -> AgentState:
    candidates = generate_candidates()
    return {
        "candidates": candidates,
        "current_guess": next_guess(candidates),
        "pending_feedback": None,
        "history": [],
        "turn": 1,
        "status": "playing",
        "candidate_count_before": len(candidates),
        "candidate_count_after": len(candidates),
        "reasoning": "Starting from all valid 3-digit numbers with unique digits.",
    }


def initialize_game(state: AgentState) -> AgentState:
    if state.get("candidates") and state.get("current_guess"):
        return state
    return create_initial_agent_state()


def receive_feedback(state: AgentState) -> AgentState:
    feedback = state.get("pending_feedback")
    guess = state.get("current_guess")
    history = list(state.get("history", []))
    candidates = list(state.get("candidates", []))

    if feedback is None or guess is None:
        return {
            **state,
            "status": "conflict",
            "reasoning": "Cannot continue because the current guess or feedback is missing.",
        }

    history.append(
        {
            "turn": state.get("turn", 1),
            "guess": guess,
            "bulls": feedback.bulls,
            "cows": feedback.cows,
            "candidates_before": len(candidates),
        }
    )

    return {
        **state,
        "history": history,
        "candidate_count_before": len(candidates),
    }


def filter_candidate_pool(state: AgentState) -> AgentState:
    feedback = state.get("pending_feedback")
    guess = state.get("current_guess")
    candidates = list(state.get("candidates", []))

    if feedback is None or guess is None:
        return state

    if feedback.bulls < 0 or feedback.cows < 0 or feedback.bulls + feedback.cows > 3:
        return {
            **state,
            "candidates": [],
            "candidate_count_after": 0,
            "status": "conflict",
        }

    if feedback.bulls == 3 and feedback.cows == 0:
        return {
            **state,
            "candidates": [guess],
            "candidate_count_after": 1,
            "status": "won",
        }

    filtered = filter_candidates(candidates, guess, feedback)
    return {
        **state,
        "candidates": filtered,
        "candidate_count_after": len(filtered),
    }


def choose_next_guess(state: AgentState) -> AgentState:
    if state.get("status") == "won":
        return state

    guess = next_guess(list(state.get("candidates", [])))
    return {
        **state,
        "current_guess": guess,
        "turn": int(state.get("turn", 1)) + 1 if guess is not None else state.get("turn", 1),
    }


def detect_win_or_conflict(state: AgentState) -> AgentState:
    if state.get("status") == "won":
        return state
    if not state.get("candidates") or state.get("current_guess") is None:
        return {**state, "status": "conflict", "current_guess": None}
    return {**state, "status": "playing"}


def explain_reasoning(state: AgentState) -> AgentState:
    status = state.get("status")
    before = state.get("candidate_count_before", 0)
    after = state.get("candidate_count_after", 0)
    current_guess = state.get("current_guess")

    if status == "won":
        reasoning = f"Solved it: {current_guess} matches all three positions."
    elif status == "conflict":
        reasoning = (
            "The feedback contradicts the remaining candidate set, so no valid "
            "3-digit number can satisfy the game history."
        )
    else:
        eliminated = before - after
        reasoning = (
            f"The latest feedback eliminated {eliminated} candidates, leaving "
            f"{after}. The next deterministic guess is {current_guess}."
        )

    history = list(state.get("history", []))
    if history:
        history[-1] = {
            **history[-1],
            "candidates_after": after,
            "next_guess": current_guess,
            "status": status,
        }

    return {**state, "history": history, "reasoning": reasoning}


def build_graph():
    graph = StateGraph(AgentState)
    graph.add_node("initialize_game", initialize_game)
    graph.add_node("receive_feedback", receive_feedback)
    graph.add_node("filter_candidates", filter_candidate_pool)
    graph.add_node("choose_next_guess", choose_next_guess)
    graph.add_node("detect_win_or_conflict", detect_win_or_conflict)
    graph.add_node("explain_reasoning", explain_reasoning)

    graph.set_entry_point("initialize_game")
    graph.add_edge("initialize_game", "receive_feedback")
    graph.add_edge("receive_feedback", "filter_candidates")
    graph.add_edge("filter_candidates", "choose_next_guess")
    graph.add_edge("choose_next_guess", "detect_win_or_conflict")
    graph.add_edge("detect_win_or_conflict", "explain_reasoning")
    graph.add_edge("explain_reasoning", END)
    return graph.compile()


def apply_feedback_turn(state: AgentState, feedback: CandidateFeedback) -> AgentState:
    graph = build_graph()
    return graph.invoke({**state, "pending_feedback": feedback})
