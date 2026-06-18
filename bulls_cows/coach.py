from bulls_cows.game import generate_candidates


def build_coach_notes(player_history: list[dict]) -> dict:
    previous_guesses = [item["guess"] for item in player_history]
    used_digits = sorted({digit for guess in previous_guesses for digit in guess})
    suggested_guess = _suggest_guess(previous_guesses)
    clue_notes = [_build_clue_note(item) for item in player_history]

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
    }


def _suggest_guess(previous_guesses: list[str]) -> str:
    previous = set(previous_guesses)
    for candidate in generate_candidates():
        if candidate not in previous:
            return candidate
    return "No legal guesses left"


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
