from bulls_cows.game import CandidateFeedback, generate_candidates, score_guess


def build_coach_notes(player_history: list[dict]) -> dict:
    previous_guesses = [item["guess"] for item in player_history]
    used_digits = sorted({digit for guess in previous_guesses for digit in guess})
    clue_notes = [_build_clue_note(item) for item in player_history]
    possible_candidates = _filter_possible_candidates(player_history)
    suggested_guess = _suggest_guess(previous_guesses, possible_candidates)
    possible_count = len(possible_candidates)

    if not previous_guesses:
        tip = "Start with three different digits."
    else:
        latest = player_history[-1]
        if latest["bulls"] == 0 and latest["cows"] == 0:
            tip = "No hits. Try fresh digits."
        elif latest["bulls"] > 0:
            tip = "You have a locked position. Change the uncertain slots."
        else:
            tip = "Useful digits found. Move them around."

    return {
        "attempts": len(previous_guesses),
        "previous_guesses": previous_guesses,
        "clue_notes": clue_notes,
        "used_digits": used_digits,
        "suggested_guess": suggested_guess,
        "tip": tip,
        "possible_count": possible_count,
        "reasoning": _build_reasoning(player_history, suggested_guess, possible_count),
    }


def _filter_possible_candidates(player_history: list[dict]) -> list[str]:
    candidates = generate_candidates()
    for item in player_history:
        feedback = CandidateFeedback(item["bulls"], item["cows"])
        candidates = [
            candidate
            for candidate in candidates
            if score_guess(candidate, item["guess"]) == feedback
        ]
    return candidates


def _suggest_guess(previous_guesses: list[str], possible_candidates: list[str]) -> str:
    previous = set(previous_guesses)
    for candidate in possible_candidates:
        if candidate not in previous:
            return candidate
    return "No legal guesses left"


def _build_reasoning(player_history: list[dict], suggested_guess: str, possible_count: int) -> str:
    if not player_history:
        return "Opening with three different digits gives the Coach useful signal quickly."
    if possible_count == 0:
        return "The previous clues conflict, so no legal number matches every response."
    return (
        f"{suggested_guess} is consistent with all {len(player_history)} previous "
        f"bulls/cows responses and leaves {possible_count} possible secret numbers."
    )


def _build_clue_note(item: dict) -> dict:
    bulls = item["bulls"]
    cows = item["cows"]
    return {
        "turn": item["turn"],
        "guess": item["guess"],
        "response": f"{bulls} {_plural('bull', bulls)}, {cows} {_plural('cow', cows)}",
        "bulls": bulls,
        "cows": cows,
    }


def _plural(word: str, count: int) -> str:
    if count == 1:
        return word
    return f"{word}s"
