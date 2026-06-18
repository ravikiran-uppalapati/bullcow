DEFAULT_GEMINI_MODEL = "gemini-2.0-flash"


def format_game_memory_for_prompt(game_memory: dict | None) -> str:
    if not game_memory:
        return "Full session memory: not available."

    agent = game_memory.get("agent", {})
    human = game_memory.get("human", {})
    coach = game_memory.get("coach", {})
    timeline = game_memory.get("timeline", [])
    timeline_text = "\n".join(f"- {item}" for item in timeline) if timeline else "- No turns yet."

    return (
        "Full session memory:\n"
        f"Current phase: {game_memory.get('phase', 'unknown')}\n"
        f"Agent current guess: {agent.get('current_guess')}\n"
        f"Agent remaining candidate count: {agent.get('candidate_count')}\n"
        f"Agent latest reasoning: {agent.get('reasoning', '')}\n"
        f"Human next turn number: {human.get('turn')}\n"
        f"Suggested human guess: {coach.get('suggested_guess')}\n"
        f"Coach deterministic tip: {coach.get('tip')}\n"
        "Timeline:\n"
        f"{timeline_text}"
    )


def build_gemini_coach_prompt(notes: dict, game_memory: dict | None = None) -> str:
    clue_lines = [
        f"- Turn {item['turn']}: {item['guess']} -> {item['response']}"
        for item in notes.get("clue_notes", [])
    ]
    clue_text = "\n".join(clue_lines) if clue_lines else "- No guesses yet."
    suggested_guess = notes.get("suggested_guess", "unknown")
    baseline_tip = notes.get("tip", "")

    return (
        "You are the Coach Agent in a Bulls and Cows game.\n"
        "Give the human player one concise, friendly hint.\n"
        "Rules: bull = right digit/right place. cow = right digit/wrong place.\n"
        "Do not claim to know the secret number. Do not reveal a secret.\n"
        "Use only the session memory, clue history, and suggested guess.\n\n"
        f"{format_game_memory_for_prompt(game_memory)}\n\n"
        f"Current deterministic tip: {baseline_tip}\n"
        f"Suggested next guess: {suggested_guess}\n"
        "Human clue history:\n"
        f"{clue_text}\n\n"
        "Return one short hint, maximum two sentences."
    )


def build_gemini_opponent_prompt(
    current_guess: str,
    turn: int,
    candidate_count: int,
    reasoning: str,
    game_memory: dict | None = None,
) -> str:
    return (
        "You are the Opponent Agent in a Bulls and Cows game.\n"
        "You are playing against a human, but the deterministic LangGraph solver "
        "already chose your valid guess.\n"
        "React conversationally to this turn with playful sledging, confidence, "
        "and game-show energy.\n"
        "Keep it friendly: no insults, no bullying, no profanity, and do not claim "
        "to know the human's secret number.\n"
        "Mention the exact guess once.\n\n"
        f"Turn: {turn}\n"
        f"Chosen guess: {current_guess}\n"
        f"Remaining possible human secrets before feedback: {candidate_count}\n"
        f"Solver reasoning: {reasoning}\n\n"
        f"{format_game_memory_for_prompt(game_memory)}\n\n"
        "Return one short line, maximum two sentences."
    )


def build_gemini_coach_reasoning_prompt(notes: dict, game_memory: dict | None = None) -> str:
    base_prompt = build_gemini_coach_prompt(notes, game_memory)
    return (
        f"{base_prompt}\n\n"
        "Also explain why the suggested number is useful in simple terms. "
        "Stay concise and do not reveal or pretend to know the secret."
    )


def build_gemini_referee_prompt(
    secret: str,
    agent_guess: str,
    bulls: int,
    cows: int,
    question: str,
    game_memory: dict | None = None,
) -> str:
    return (
        "You are a friendly Bulls and Cows referee helping the human respond "
        "to the Opponent Agent.\n"
        "The app has already calculated the exact feedback. Do not change it.\n"
        "Explain the answer clearly and briefly. Mention the exact bulls/cows "
        "the human should submit.\n\n"
        f"Human secret number: {secret}\n"
        f"Opponent Agent guess: {agent_guess}\n"
        f"Exact response: {bulls} bull{'s' if bulls != 1 else ''}, "
        f"{cows} cow{'s' if cows != 1 else ''}\n"
        f"Human question: {question}\n\n"
        f"{format_game_memory_for_prompt(game_memory)}\n\n"
        "Return one helpful answer, maximum three short sentences."
    )


def generate_gemini_referee_help(
    secret: str,
    agent_guess: str,
    bulls: int,
    cows: int,
    question: str,
    api_key: str | None,
    model_name: str = DEFAULT_GEMINI_MODEL,
    game_memory: dict | None = None,
    llm_factory=None,
) -> dict:
    fallback = (
        f"Respond with {bulls} bull{'s' if bulls != 1 else ''} and "
        f"{cows} cow{'s' if cows != 1 else ''}."
    )
    if not api_key:
        return {"source": "deterministic", "message": fallback}

    try:
        llm = llm_factory() if llm_factory else _create_gemini_llm(api_key, model_name)
        response = llm.invoke(
            build_gemini_referee_prompt(
                secret,
                agent_guess,
                bulls,
                cows,
                question,
                game_memory,
            )
        )
        message = getattr(response, "content", str(response)).strip()
        if not message:
            raise ValueError("Gemini returned an empty referee answer.")
        return {"source": "gemini", "message": message}
    except Exception as exc:
        return {"source": "fallback", "message": fallback, "error": str(exc)}


def generate_gemini_agent_message(
    role: str,
    payload: dict,
    api_key: str | None,
    model_name: str = DEFAULT_GEMINI_MODEL,
    llm_factory=None,
) -> dict:
    fallback = payload.get("fallback", "")
    if not api_key:
        return {"source": "deterministic", "message": fallback}

    try:
        llm = llm_factory() if llm_factory else _create_gemini_llm(api_key, model_name)
        if role == "opponent":
            prompt = build_gemini_opponent_prompt(
                current_guess=payload["current_guess"],
                turn=int(payload["turn"]),
                candidate_count=int(payload["candidate_count"]),
                reasoning=payload.get("reasoning", ""),
                game_memory=payload.get("game_memory"),
            )
        elif role == "coach":
            prompt = build_gemini_coach_reasoning_prompt(
                payload["notes"],
                payload.get("game_memory"),
            )
        else:
            raise ValueError(f"Unknown LLM agent role: {role}")

        response = llm.invoke(prompt)
        message = getattr(response, "content", str(response)).strip()
        if not message:
            raise ValueError("Gemini returned an empty message.")
        return {"source": "gemini", "message": message}
    except Exception as exc:
        return {"source": "fallback", "message": fallback, "error": str(exc)}


def generate_gemini_coach_tip(
    notes: dict,
    api_key: str | None,
    model_name: str = DEFAULT_GEMINI_MODEL,
    game_memory: dict | None = None,
    llm_factory=None,
) -> dict:
    if not api_key:
        return {"source": "deterministic", "tip": notes.get("tip", "")}

    try:
        llm = llm_factory() if llm_factory else _create_gemini_llm(api_key, model_name)
        response = llm.invoke(build_gemini_coach_prompt(notes, game_memory))
        tip = getattr(response, "content", str(response)).strip()
        if not tip:
            raise ValueError("Gemini returned an empty tip.")
        return {"source": "gemini", "tip": tip}
    except Exception as exc:
        return {
            "source": "fallback",
            "tip": notes.get("tip", ""),
            "error": str(exc),
        }


def _create_gemini_llm(api_key: str, model_name: str):
    from langchain_google_genai import ChatGoogleGenerativeAI

    return ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=api_key,
        temperature=0.4,
        max_retries=1,
    )
