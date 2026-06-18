import json
from types import SimpleNamespace
from urllib import request

DEFAULT_GEMINI_MODEL = "gemini-2.0-flash"
DEFAULT_NEBIUS_BASE_URL = "https://api.studio.nebius.com/v1"


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


def build_gemini_chat_prompt(
    question: str,
    game_memory: dict | None = None,
) -> str:
    return (
        "You are the LLM Coach inside a Bulls and Cows game.\n"
        "Answer the human like a helpful game companion: clear, playful, and concise.\n"
        "Use the full session memory and the human's question.\n"
        "Do not reveal the app's secret number. Do not claim certainty where the "
        "game clues do not support it.\n\n"
        f"{format_game_memory_for_prompt(game_memory)}\n\n"
        f"Human question: {question}\n\n"
        "Return a direct answer in at most four short sentences."
    )


def generate_gemini_chat_response(
    question: str,
    api_key: str | None,
    model_name: str = DEFAULT_GEMINI_MODEL,
    provider: str = "gemini",
    base_url: str = DEFAULT_NEBIUS_BASE_URL,
    game_memory: dict | None = None,
    llm_factory=None,
) -> dict:
    fallback = "I can help with the game state. Add a Gemini API key for a conversational answer."
    if not api_key:
        return {"source": "deterministic", "message": fallback}

    try:
        llm, used_model = _create_llm_with_model(api_key, model_name, provider, base_url, llm_factory)
        response = llm.invoke(build_gemini_chat_prompt(question, game_memory))
        message = getattr(response, "content", str(response)).strip()
        if not message:
            raise ValueError("Gemini returned an empty chat answer.")
        return {"source": provider, "message": message, "model": used_model}
    except Exception as exc:
        retry_result = _retry_default_model_after_quota(
            exc,
            api_key,
            model_name,
            provider,
            base_url,
            lambda llm: llm.invoke(build_gemini_chat_prompt(question, game_memory)),
            llm_factory,
        )
        if retry_result:
            return retry_result
        return {"source": "fallback", "message": fallback, "error": _friendly_gemini_error(exc)}


def generate_gemini_agent_message(
    role: str,
    payload: dict,
    api_key: str | None,
    model_name: str = DEFAULT_GEMINI_MODEL,
    provider: str = "gemini",
    base_url: str = DEFAULT_NEBIUS_BASE_URL,
    llm_factory=None,
) -> dict:
    fallback = payload.get("fallback", "")
    if not api_key:
        return {"source": "deterministic", "message": fallback}

    try:
        llm, used_model = _create_llm_with_model(api_key, model_name, provider, base_url, llm_factory)
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
        return {"source": provider, "message": message, "model": used_model}
    except Exception as exc:
        return {"source": "fallback", "message": fallback, "error": _friendly_gemini_error(exc)}


def generate_gemini_coach_tip(
    notes: dict,
    api_key: str | None,
    model_name: str = DEFAULT_GEMINI_MODEL,
    provider: str = "gemini",
    base_url: str = DEFAULT_NEBIUS_BASE_URL,
    game_memory: dict | None = None,
    llm_factory=None,
) -> dict:
    if not api_key:
        return {"source": "deterministic", "tip": notes.get("tip", "")}

    try:
        llm, used_model = _create_llm_with_model(api_key, model_name, provider, base_url, llm_factory)
        response = llm.invoke(build_gemini_coach_prompt(notes, game_memory))
        tip = getattr(response, "content", str(response)).strip()
        if not tip:
            raise ValueError("Gemini returned an empty tip.")
        return {"source": provider, "tip": tip, "model": used_model}
    except Exception as exc:
        return {
            "source": "fallback",
            "tip": notes.get("tip", ""),
            "error": _friendly_gemini_error(exc),
        }


def _create_llm_with_model(
    api_key: str,
    model_name: str,
    provider: str = "gemini",
    base_url: str = DEFAULT_NEBIUS_BASE_URL,
    llm_factory=None,
):
    if llm_factory:
        try:
            return llm_factory(provider, model_name), model_name
        except TypeError:
            try:
                return llm_factory(model_name), model_name
            except TypeError:
                return llm_factory(), model_name
    if provider == "nebius":
        return _NebiusChatLLM(api_key, model_name, base_url), model_name
    return _create_gemini_llm(api_key, model_name), model_name


def _retry_default_model_after_quota(
    exc: Exception,
    api_key: str,
    model_name: str,
    provider: str,
    base_url: str,
    invoke_fn,
    llm_factory=None,
):
    if provider != "gemini" or model_name == DEFAULT_GEMINI_MODEL or not _is_quota_error(exc):
        return None
    try:
        llm, used_model = _create_llm_with_model(api_key, DEFAULT_GEMINI_MODEL, provider, base_url, llm_factory)
        response = invoke_fn(llm)
        message = getattr(response, "content", str(response)).strip()
        if not message:
            raise ValueError("Gemini returned an empty chat answer.")
        return {"source": provider, "message": message, "model": used_model}
    except Exception as fallback_exc:
        return {
            "source": "fallback",
            "message": "I can help with the game state, but Gemini quota is exhausted right now.",
            "error": _friendly_gemini_error(fallback_exc),
        }


def _is_quota_error(exc: Exception) -> bool:
    text = str(exc).lower()
    return "429" in text or "resource_exhausted" in text or "quota" in text


def _friendly_gemini_error(exc: Exception) -> str:
    if _is_quota_error(exc):
        return "Gemini quota is exhausted for the selected model. Try again shortly, remove GEMINI_MODEL to use the default, or use a key with more quota."
    return str(exc)


def _create_gemini_llm(api_key: str, model_name: str):
    from langchain_google_genai import ChatGoogleGenerativeAI

    return ChatGoogleGenerativeAI(
        model=model_name,
        google_api_key=api_key,
        temperature=0.4,
        max_retries=1,
    )


class _NebiusChatLLM:
    def __init__(self, api_key: str, model_name: str, base_url: str = DEFAULT_NEBIUS_BASE_URL):
        self.api_key = api_key
        self.model_name = model_name
        self.base_url = base_url.rstrip("/")

    def invoke(self, prompt: str):
        payload = json.dumps(
            {
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.4,
            }
        ).encode("utf-8")
        req = request.Request(
            f"{self.base_url}/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with request.urlopen(req, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"]
        return SimpleNamespace(content=content)
