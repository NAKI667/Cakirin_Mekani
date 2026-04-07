from __future__ import annotations

import random
from dataclasses import dataclass, field

from ..exceptions import ValidationError
from ..models import GameResult

RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
SUITS = ["S", "H", "D", "C"]


def create_deck() -> list[str]:
    return [f"{rank}{suit}" for suit in SUITS for rank in RANKS]


def hand_value(cards: list[str]) -> int:
    total = 0
    ace_count = 0

    for card in cards:
        rank = card[:-1]
        if rank == "A":
            total += 11
            ace_count += 1
        elif rank in {"J", "Q", "K"}:
            total += 10
        else:
            total += int(rank)

    while total > 21 and ace_count:
        total -= 10
        ace_count -= 1

    return total


def is_blackjack(cards: list[str]) -> bool:
    return len(cards) == 2 and hand_value(cards) == 21


def blackjack_bonus(bet: int) -> int:
    return (bet * 3 + 1) // 2


@dataclass(slots=True)
class BlackjackRound:
    bet: int
    rng: random.Random | None = None
    deck: list[str] | None = None
    player_cards: list[str] = field(init=False)
    dealer_cards: list[str] = field(init=False)
    finished: bool = field(default=False, init=False)
    outcome: str | None = field(default=None, init=False)
    net_change: int = field(default=0, init=False)
    summary: str = field(default="", init=False)

    def __post_init__(self) -> None:
        if self.bet <= 0:
            raise ValidationError("Blackjack bahsi sıfırdan büyük olmalı.")

        if self.deck is None:
            source_deck = create_deck()
            shuffler = self.rng or random.Random()
            shuffler.shuffle(source_deck)
        else:
            source_deck = list(self.deck)

        self.deck = source_deck
        self.player_cards = [self._draw()]
        self.dealer_cards = [self._draw()]
        self.player_cards.append(self._draw())
        self.dealer_cards.append(self._draw())
        self._resolve_natural_blackjack()

    @property
    def player_total(self) -> int:
        return hand_value(self.player_cards)

    @property
    def dealer_total(self) -> int:
        return hand_value(self.dealer_cards)

    def visible_dealer_cards(self) -> list[str]:
        if self.finished:
            return list(self.dealer_cards)
        return [self.dealer_cards[0], "??"]

    def visible_dealer_total(self) -> int:
        if self.finished:
            return self.dealer_total
        return hand_value([self.dealer_cards[0]])

    def hit(self) -> "BlackjackRound":
        if self.finished:
            raise ValidationError("Bu el zaten kapandı.")

        self.player_cards.append(self._draw())
        if self.player_total > 21:
            self._finish(
                outcome="loss",
                net_change=-self.bet,
                summary="El patladı; kasa fişleri süpürdü.",
            )
        elif self.player_total == 21:
            self.stand()
        return self

    def stand(self) -> "BlackjackRound":
        if self.finished:
            raise ValidationError("Bu el zaten kapandı.")

        while self.dealer_total < 17:
            self.dealer_cards.append(self._draw())

        if self.dealer_total > 21:
            self._finish(
                outcome="win",
                net_change=self.bet,
                summary="Kasa patladı; masa bu tur senin oldu.",
            )
        elif self.player_total > self.dealer_total:
            self._finish(
                outcome="win",
                net_change=self.bet,
                summary="El üstün geldi; kasa geri çekildi.",
            )
        elif self.player_total < self.dealer_total:
            self._finish(
                outcome="loss",
                net_change=-self.bet,
                summary="Kasanın eli ağır bastı; bu tur fişler gitti.",
            )
        else:
            self._finish(
                outcome="push",
                net_change=0,
                summary="Masa dengede kaldı; bahis iade edildi.",
            )
        return self

    def to_result(self) -> GameResult:
        if not self.finished or self.outcome is None:
            raise ValidationError("Blackjack turu henüz tamamlanmadı.")

        return GameResult(
            game="blackjack",
            bet=self.bet,
            outcome=self.outcome,
            net_change=self.net_change,
            details={
                "player_cards": list(self.player_cards),
                "dealer_cards": list(self.dealer_cards),
                "player_total": self.player_total,
                "dealer_total": self.dealer_total,
            },
            summary=self.summary,
        )

    def _resolve_natural_blackjack(self) -> None:
        player_blackjack = is_blackjack(self.player_cards)
        dealer_blackjack = is_blackjack(self.dealer_cards)

        if player_blackjack and dealer_blackjack:
            self._finish(
                outcome="push",
                net_change=0,
                summary="İki taraf da blackjack buldu; masa orta yerde kaldı.",
            )
        elif player_blackjack:
            self._finish(
                outcome="blackjack",
                net_change=blackjack_bonus(self.bet),
                summary="Doğal blackjack; tek bakışta masa çözüldü.",
            )
        elif dealer_blackjack:
            self._finish(
                outcome="loss",
                net_change=-self.bet,
                summary="Kasa doğal blackjack açtı; bu tur söz onda kaldı.",
            )

    def _draw(self) -> str:
        if not self.deck:
            raise ValidationError("Destede kart kalmadı.")
        return self.deck.pop(0)

    def _finish(self, *, outcome: str, net_change: int, summary: str) -> None:
        self.finished = True
        self.outcome = outcome
        self.net_change = net_change
        self.summary = summary
