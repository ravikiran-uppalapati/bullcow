from bulls_cows.game import CandidateFeedback, score_guess


def filter_candidates(
    candidates: list[str],
    guess: str,
    feedback: CandidateFeedback,
) -> list[str]:
    return [
        candidate
        for candidate in candidates
        if score_guess(candidate, guess) == feedback
    ]


def next_guess(candidates: list[str]) -> str | None:
    if not candidates:
        return None
    return candidates[0]
