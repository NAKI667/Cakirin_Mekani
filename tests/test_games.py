from __future__ import annotations

from cakir_casino.games.blackjack import BlackjackRound, hand_value
from cakir_casino.games.coinflip import play_coinflip
from cakir_casino.games.roulette import play_roulette


def test_coinflip_win_pays_even_money():
    result = play_coinflip(100, "yazi", forced_result="yazi")

    assert result.outcome == "win"
    assert result.net_change == 100


def test_roulette_zero_breaks_parity_and_color():
    parity_result = play_roulette(50, "parity", "odd", forced_spin=0)
    color_result = play_roulette(50, "color", "red", forced_spin=0)

    assert parity_result.net_change == -50
    assert color_result.net_change == -50


def test_roulette_exact_number_pays_thirty_five_to_one():
    result = play_roulette(10, "number", "17", forced_spin=17)

    assert result.outcome == "win"
    assert result.net_change == 350


def test_blackjack_counts_aces_dynamically():
    assert hand_value(["AS", "9H", "AD"]) == 21


def test_blackjack_natural_blackjack_pays_bonus():
    round_state = BlackjackRound(
        bet=100,
        deck=["AS", "9D", "KH", "7C", "2S"],
    )

    assert round_state.finished is True
    assert round_state.outcome == "blackjack"
    assert round_state.net_change == 150


def test_blackjack_hit_can_bust():
    round_state = BlackjackRound(
        bet=100,
        deck=["9S", "7D", "8H", "6C", "9H"],
    )

    round_state.hit()

    assert round_state.finished is True
    assert round_state.outcome == "loss"
    assert round_state.net_change == -100


def test_blackjack_dealer_stands_on_seventeen():
    round_state = BlackjackRound(
        bet=100,
        deck=["10S", "6D", "7H", "9C", "2H", "5S"],
    )

    round_state.stand()

    assert round_state.dealer_cards == ["6D", "9C", "2H"]
    assert round_state.dealer_total == 17
    assert round_state.outcome == "push"
