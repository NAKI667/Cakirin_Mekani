from __future__ import annotations

import random

from ..exceptions import ValidationError
from ..models import GameResult

RED_NUMBERS = {
    1,
    3,
    5,
    7,
    9,
    12,
    14,
    16,
    18,
    19,
    21,
    23,
    25,
    27,
    30,
    32,
    34,
    36,
}


def roulette_color(number: int) -> str:
    if number == 0:
        return "green"
    return "red" if number in RED_NUMBERS else "black"


def play_roulette(
    bet: int,
    bet_type: str,
    value: str,
    *,
    rng: random.Random | None = None,
    forced_spin: int | None = None,
) -> GameResult:
    if bet <= 0:
        raise ValidationError("Bahis miktarı sıfırdan büyük olmalı.")

    clean_bet_type = bet_type.strip().lower()
    clean_value = value.strip().lower()

    if clean_bet_type not in {"color", "parity", "number"}:
        raise ValidationError("Rulette bet-type sadece color, parity veya number olabilir.")

    normalized_value = _normalize_value(clean_bet_type, clean_value)

    if forced_spin is not None:
        spin = forced_spin
    else:
        roller = rng or random.Random()
        spin = roller.randint(0, 36)

    color = roulette_color(spin)
    parity = "none" if spin == 0 else ("even" if spin % 2 == 0 else "odd")

    if clean_bet_type == "color":
        is_win = normalized_value == color
        net_change = bet if is_win else -bet
    elif clean_bet_type == "parity":
        is_win = spin != 0 and normalized_value == parity
        net_change = bet if is_win else -bet
    else:
        is_win = int(normalized_value) == spin
        net_change = bet * 35 if is_win else -bet

    summary = (
        f"Teker {spin} ({color}) üzerinde durdu; masa seni bu turda ödüllendirdi."
        if is_win
        else f"Teker {spin} ({color}) üzerinde durdu; bu tur rulet evi ağır bastı."
    )

    return GameResult(
        game="roulette",
        bet=bet,
        outcome="win" if is_win else "loss",
        net_change=net_change,
        details={
            "bet_type": clean_bet_type,
            "value": normalized_value,
            "spin": spin,
            "color": color,
            "parity": parity,
        },
        summary=summary,
    )


def _normalize_value(bet_type: str, value: str) -> str:
    if bet_type == "color":
        mapping = {
            "red": "red",
            "black": "black",
            "kirmizi": "red",
            "siyah": "black",
        }
        if value not in mapping:
            raise ValidationError("Renk bahsi için değer red/black ya da kirmizi/siyah olmalı.")
        return mapping[value]

    if bet_type == "parity":
        mapping = {
            "odd": "odd",
            "even": "even",
            "tek": "odd",
            "cift": "even",
        }
        if value not in mapping:
            raise ValidationError("Tek-çift bahsi için değer odd/even ya da tek/cift olmalı.")
        return mapping[value]

    try:
        number = int(value)
    except ValueError as error:
        raise ValidationError("Sayı bahsi için 0 ile 36 arasında bir sayı vermelisin.") from error

    if not 0 <= number <= 36:
        raise ValidationError("Sayı bahsi için 0 ile 36 arasında bir sayı vermelisin.")

    return str(number)
