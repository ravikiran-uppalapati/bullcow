from __future__ import annotations

from typing import Any


def build_agent_toolbelt(
    game_memory: dict[str, Any],
    chat_history: list[dict[str, Any]],
    tracing_enabled: bool,
    gemini_enabled: bool,
) -> list[dict[str, str]]:
    agent = game_memory.get("agent", {})
    human = game_memory.get("human", {})
    coach = game_memory.get("coach", {})
    agent_history = agent.get("history", [])
    human_history = human.get("history", [])
    latest_agent_turn = agent_history[-1] if agent_history else {}
    latest_human_turn = human_history[-1] if human_history else {}

    return [
        {
            "name": "candidate_generator",
            "label": "Candidate Generator",
            "owner": "Opponent Agent",
            "status": "ready",
            "evidence": f"{agent.get('candidate_count', 0)} possible secrets in memory",
        },
        {
            "name": "score_guess",
            "label": "Bulls/Cows Scorer",
            "owner": "Game Engine",
            "status": "used" if agent_history or human_history else "ready",
            "evidence": _latest_score_evidence(latest_agent_turn, latest_human_turn),
        },
        {
            "name": "filter_candidates",
            "label": "Candidate Filter",
            "owner": "LangGraph Solver",
            "status": "used" if agent_history else "waiting",
            "evidence": _candidate_filter_evidence(latest_agent_turn, agent.get("candidate_count", 0)),
        },
        {
            "name": "choose_next_guess",
            "label": "Next Guess Selector",
            "owner": "LangGraph Solver",
            "status": "used" if agent.get("current_guess") else "waiting",
            "evidence": f"Next guess: {agent.get('current_guess') or 'not chosen yet'}",
        },
        {
            "name": "coach_memory",
            "label": "Coach Memory",
            "owner": "Coach Agent",
            "status": "used" if human_history else "ready",
            "evidence": f"Suggested human guess: {coach.get('suggested_guess') or 'not ready'}",
        },
        {
            "name": "gemini_chat",
            "label": "LLM Coach",
            "owner": "Coach Agent",
            "status": "used" if chat_history else ("ready" if gemini_enabled else "needs key"),
            "evidence": _chat_evidence(chat_history),
        },
        {
            "name": "llm_reasoning",
            "label": "LLM Reasoning",
            "owner": "Opponent + Coach",
            "status": "ready" if gemini_enabled else "fallback",
            "evidence": "LLM enabled" if gemini_enabled else "Using deterministic fallback",
        },
        {
            "name": "langsmith_trace",
            "label": "LangSmith Trace",
            "owner": "Observability",
            "status": "watching" if tracing_enabled else "off",
            "evidence": "Live runs traced" if tracing_enabled else "Set LANGSMITH_TRACING=true",
        },
    ]


def _latest_score_evidence(
    latest_agent_turn: dict[str, Any],
    latest_human_turn: dict[str, Any],
) -> str:
    if latest_human_turn:
        return (
            f"Human {latest_human_turn.get('guess')} -> "
            f"{latest_human_turn.get('bulls')}B/{latest_human_turn.get('cows')}C"
        )
    if latest_agent_turn:
        return (
            f"Agent {latest_agent_turn.get('guess')} -> "
            f"{latest_agent_turn.get('bulls')}B/{latest_agent_turn.get('cows')}C"
        )
    return "Ready to score the next guess"


def _candidate_filter_evidence(latest_agent_turn: dict[str, Any], candidate_count: int) -> str:
    if latest_agent_turn:
        before = latest_agent_turn.get("candidates_before", "?")
        after = latest_agent_turn.get("candidates_after", candidate_count)
        return f"{before} -> {after} candidates"
    return f"{candidate_count} candidates before feedback"


def _chat_evidence(chat_history: list[dict[str, Any]]) -> str:
    if not chat_history:
        return "Ask Coach any game question"
    return f"Last question: {chat_history[-1].get('question', '')}"
