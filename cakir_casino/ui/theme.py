from __future__ import annotations

import json
import random

from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from ..models import User

QUOTE_BANK: dict[str, list[tuple[str, str]]] = {
    "welcome": [
        ("Çakır", "Racon burada kesilir, masa önce düzen ister."),
        ("Polat", "Oyuna giriyorsan önce soğukkanlı olacaksın."),
    ],
    "auth": [
        ("Çakır", "Masaya oturan adam sözünün de hesabının da arkasında durur."),
        ("Polat", "İsim veriyorsan yükünü de taşıyacaksın."),
    ],
    "win": [
        ("Çakır", "Kazanan el bağırmaz, fişi toplar."),
        ("Polat", "Sabırla duran bazen tek hamlede bütün masayı alır."),
    ],
    "lose": [
        ("Çakır", "Bu masada düşen kalkmayı da bilecek."),
        ("Polat", "Kayıp, hesabını bilen adama yol gösterir."),
    ],
    "push": [
        ("Çakır", "Bazen masa susar, herkes yerini korur."),
        ("Polat", "Beraberlik de oyunun dilidir."),
    ],
    "roulette": [
        ("Çakır", "Teker döner ama racon yerinden oynamaz."),
        ("Polat", "Şans döner, soğukkanlılık dönmez."),
    ],
    "blackjack": [
        ("Çakır", "Bir kart fazla bazen bütün masayı devirir."),
        ("Polat", "On yediyi gören durmasını da bilir."),
    ],
    "admin": [
        ("Çakır", "Masa da adam da disiplin ister."),
        ("Polat", "Düzen bozulursa oyunun tadı kalmaz."),
    ],
    "history": [
        ("Çakır", "Geçmişi bilmeyen masaya eksik oturur."),
        ("Polat", "İz bırakmayan hamle, hamle sayılmaz."),
    ],
    "profile": [
        ("Çakır", "Adam önce kendi masasını tanır."),
        ("Polat", "Durduğun yeri bilirsen oyun seni savurmaz."),
    ],
    "error": [
        ("Çakır", "Masa hata kaldırır, ama ikinciyi sevmez."),
        ("Polat", "Yanlış hamleyi erkenden fark etmek de güçtür."),
    ],
    "general": [
        ("Çakır", "Bu mekan ayakta kalıyorsa herkes haddini bildiği içindir."),
        ("Polat", "Sakin kalan oyuncu oyunun ritmini belirler."),
    ],
}

TONE_STYLES = {
    "info": "cyan",
    "success": "green",
    "warning": "yellow",
    "error": "red",
    "admin": "magenta",
}


class CasinoUI:
    def __init__(self, console: Console | None = None):
        self.console = console or Console(highlight=False)

    def info(self, title: str, message: str, *, category: str = "general") -> None:
        self._panel(title, message, category=category, tone="info")

    def success(self, title: str, message: str, *, category: str = "win") -> None:
        self._panel(title, message, category=category, tone="success")

    def warning(self, title: str, message: str, *, category: str = "general") -> None:
        self._panel(title, message, category=category, tone="warning")

    def error(self, title: str, message: str, *, category: str = "error") -> None:
        self._panel(title, message, category=category, tone="error")

    def admin(self, title: str, message: str) -> None:
        self._panel(title, message, category="admin", tone="admin")

    def show_profile(self, user: User) -> None:
        table = Table(title="Oyuncu Profili", title_style="bold cyan")
        table.add_column("Alan", style="bold")
        table.add_column("Değer")
        table.add_row("Kullanıcı", user.username)
        table.add_row("Rol", "Admin" if user.is_admin else "Oyuncu")
        table.add_row("Bakiye", f"{user.balance} chip")
        table.add_row("Oluşturulma", user.created_at)
        self.console.print(table)
        self._quote_footer("profile")

    def show_users(self, users: list[User]) -> None:
        table = Table(title="Mekandaki Hesaplar", title_style="bold magenta")
        table.add_column("Kullanıcı")
        table.add_column("Rol")
        table.add_column("Bakiye", justify="right")
        table.add_column("Oluşturulma")
        for user in users:
            table.add_row(
                user.username,
                "Admin" if user.is_admin else "Oyuncu",
                str(user.balance),
                user.created_at,
            )
        self.console.print(table)
        self._quote_footer("admin")

    def show_history(self, rows: list[object]) -> None:
        table = Table(title="Oyun Geçmişi", title_style="bold yellow")
        table.add_column("Oyun")
        table.add_column("Bahis", justify="right")
        table.add_column("Sonuç")
        table.add_column("Payout", justify="right")
        table.add_column("Bakiye", justify="right")
        table.add_column("Detay")
        table.add_column("Tarih")
        for row in rows:
            detail = self._summarize_details(row["game"], row["details"])
            table.add_row(
                row["game"],
                str(row["bet"]),
                row["outcome"],
                f"{row['payout']:+}",
                str(row["balance_after"]),
                detail,
                row["created_at"],
            )
        self.console.print(table)
        self._quote_footer("history")

    def show_logs(self, rows: list[object]) -> None:
        table = Table(title="Audit Logları", title_style="bold magenta")
        table.add_column("Kullanıcı")
        table.add_column("İşlem")
        table.add_column("Tarih")
        for row in rows:
            table.add_row(row["username"], row["action"], row["created_at"])
        self.console.print(table)
        self._quote_footer("admin")

    def show_blackjack(self, round_state: object) -> None:
        dealer_cards = ", ".join(round_state.visible_dealer_cards())
        player_cards = ", ".join(round_state.player_cards)
        message = (
            f"Bahis: {round_state.bet} chip\n"
            f"Oyuncu eli: {player_cards} ({round_state.player_total})\n"
            f"Kasa eli: {dealer_cards} ({round_state.visible_dealer_total()})"
        )
        if round_state.finished:
            message = f"{message}\n\nFinal: {round_state.summary}"
            tone = "success" if round_state.net_change > 0 else "warning" if round_state.net_change == 0 else "error"
        else:
            tone = "warning"
        self._panel("Blackjack Masası", message, category="blackjack", tone=tone)

    def _panel(self, title: str, message: str, *, category: str, tone: str) -> None:
        speaker, quote = self._quote(category)
        group = Group(
            Text(message),
            Text(""),
            Text(f"{speaker}: \"{quote}\"", style="italic dim"),
        )
        self.console.print(
            Panel(
                group,
                title=title,
                border_style=TONE_STYLES[tone],
                padding=(1, 2),
            ),
        )

    def _quote(self, category: str) -> tuple[str, str]:
        bank = QUOTE_BANK.get(category, QUOTE_BANK["general"])
        return random.choice(bank)

    def _quote_footer(self, category: str) -> None:
        speaker, quote = self._quote(category)
        self.console.print(Text(f"{speaker}: \"{quote}\"", style="italic dim"))

    @staticmethod
    def _summarize_details(game: str, payload: str) -> str:
        details = json.loads(payload)
        if game == "coinflip":
            return f"{details['choice']} -> {details['result']}"
        if game == "roulette":
            return f"{details['bet_type']}={details['value']}, spin={details['spin']}"
        if game == "blackjack":
            return (
                f"P:{details['player_total']} / "
                f"D:{details['dealer_total']}"
            )
        return json.dumps(details, ensure_ascii=False)
