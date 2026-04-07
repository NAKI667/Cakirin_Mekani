from __future__ import annotations

import random

from ..exceptions import ValidationError
from ..models import GameResult

VALID_SIDES = {"yazi", "tura"}


def play_coinflip(
    bet: int,
    side: str,
    *,
    rng: random.Random | None = None,
    forced_result: str | None = None,
) -> GameResult:
    clean_side = side.strip().lower()
    if clean_side not in VALID_SIDES:
        raise ValidationError("Yazı tura için sadece 'yazi' veya 'tura' seçebilirsin.")

    if bet <= 0:
        raise ValidationError("Bahis miktarı sıfırdan büyük olmalı.")

    if forced_result is not None:
        result_side = forced_result
    else:
        chooser = rng or random.Random()
        result_side = chooser.choice(sorted(VALID_SIDES))

    is_win = clean_side == result_side
    summary = (
        f"Para havada {result_side} geldi; seçimin masayı topladı."
        if is_win
        else f"Para havada {result_side} geldi; bu el kasa güldü."
    )

    return GameResult(
        game="coinflip",
        bet=bet,
        outcome="win" if is_win else "loss",
        net_change=bet if is_win else -bet,
        details={"choice": clean_side, "result": result_side},
        summary=summary,
    )
