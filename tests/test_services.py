from __future__ import annotations

import pytest

from cakir_casino.exceptions import ValidationError
from cakir_casino.games.coinflip import play_coinflip


def test_settle_game_updates_balance_and_history(services):
    auth = services["auth"]
    casino = services["casino"]

    user = auth.register("abdulhey", "golgeden")
    result = play_coinflip(100, "tura", forced_result="tura")
    updated = casino.settle_game(user.username, result)
    history = casino.history_for(user.username)

    assert updated.balance == 1100
    assert history[0]["game"] == "coinflip"
    assert history[0]["payout"] == 100


def test_settle_game_rejects_insufficient_balance(services):
    auth = services["auth"]
    casino = services["casino"]

    user = auth.register("testere", "kurtkapan")
    result = play_coinflip(1200, "yazi", forced_result="yazi")

    with pytest.raises(ValidationError):
        casino.settle_game(user.username, result)


def test_admin_balance_update_is_persisted(services):
    auth = services["auth"]
    casino = services["casino"]

    auth.register("halo", "guzeloyun")
    updated = casino.set_balance("halo", 2500, actor="cakir")

    assert updated.balance == 2500
