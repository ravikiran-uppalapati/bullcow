from dataclasses import dataclass


@dataclass(frozen=True)
class CandidateFeedback:
    bulls: int
    cows: int


def is_valid_secret(value: str) -> bool:
    return (
        len(value) == 3
        and value.isdigit()
        and value[0] != "0"
        and len(set(value)) == 3
    )


def is_valid_feedback(bulls: int, cows: int) -> bool:
    return 0 <= bulls <= 3 and 0 <= cows <= 3 and bulls + cows <= 3


def generate_candidates() -> list[str]:
    return [
        f"{number:03d}"
        for number in range(100, 1000)
        if is_valid_secret(f"{number:03d}")
    ]


def score_guess(secret: str, guess: str) -> CandidateFeedback:
    bulls = sum(secret_digit == guess_digit for secret_digit, guess_digit in zip(secret, guess))
    shared_digits = len(set(secret) & set(guess))
    return CandidateFeedback(bulls=bulls, cows=shared_digits - bulls)
