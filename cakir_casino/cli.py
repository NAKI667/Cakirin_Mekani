from __future__ import annotations

import sys
from dataclasses import dataclass

import typer

from .auth import AuthService
from .config import (
    APP_NAME,
    DEFAULT_ADMIN_PASSWORD,
    DEFAULT_ADMIN_USERNAME,
    get_app_paths,
)
from .db import Database
from .exceptions import CasinoError, ValidationError
from .games import BlackjackRound, play_coinflip, play_roulette
from .services import CasinoService
from .session import SessionManager
from .ui import CasinoUI

app = typer.Typer(no_args_is_help=True, help="Çakır'ın Mekanı komut satırı casinosu.")
auth_app = typer.Typer(no_args_is_help=True, help="Kayıt, giriş ve çıkış komutları.")
profile_app = typer.Typer(no_args_is_help=True, help="Aktif oyuncu profilini gösterir.")
play_app = typer.Typer(no_args_is_help=True, help="Casino oyunları.")
admin_app = typer.Typer(no_args_is_help=True, help="Admin komutları.")
admin_users_app = typer.Typer(no_args_is_help=True, help="Kullanıcı yönetimi.")
admin_balance_app = typer.Typer(no_args_is_help=True, help="Bakiye yönetimi.")
admin_logs_app = typer.Typer(no_args_is_help=True, help="Logları gösterir.")

app.add_typer(auth_app, name="auth")
app.add_typer(profile_app, name="profile")
app.add_typer(play_app, name="play")
app.add_typer(admin_app, name="admin")
admin_app.add_typer(admin_users_app, name="users")
admin_app.add_typer(admin_balance_app, name="balance")
admin_app.add_typer(admin_logs_app, name="logs")


@dataclass(slots=True)
class Runtime:
    db: Database
    auth: AuthService
    casino: CasinoService
    ui: CasinoUI


class InputClosed(Exception):
    """Raised when interactive stdin closes unexpectedly."""


def build_runtime() -> Runtime:
    paths = get_app_paths()
    db = Database(paths)
    db.initialize()
    sessions = SessionManager(paths.session_path)
    auth = AuthService(db, sessions)
    casino = CasinoService(db, auth)
    ui = CasinoUI()
    return Runtime(db=db, auth=auth, casino=casino, ui=ui)


def fail(ui: CasinoUI, error: Exception) -> None:
    ui.error("Masada Terslik Var", str(error))
    raise typer.Exit(code=1)


def ensure_bet(balance: int, bet: int) -> None:
    if bet <= 0:
        raise ValidationError("Bahis miktarı sıfırdan büyük olmalı.")
    if balance < bet:
        raise ValidationError("Bu bahis için yeterli chip yok.")


def render_result(ui: CasinoUI, heading: str, balance: int, result: object) -> None:
    message = (
        f"Özet: {result.summary}\n"
        f"Bahis: {result.bet} chip\n"
        f"Net değişim: {result.net_change:+} chip\n"
        f"Güncel bakiye: {balance} chip"
    )
    if result.net_change > 0:
        ui.success(heading, message, category="win")
    elif result.net_change < 0:
        ui.error(heading, message, category="lose")
    else:
        ui.warning(heading, message, category="push")


def configure_console() -> None:
    if sys.platform == "win32":
        try:
            import ctypes

            ctypes.windll.kernel32.SetConsoleCP(65001)
            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
        except Exception:
            pass

    for name in ("stdout", "stderr"):
        stream = getattr(sys, name, None)
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8")
            except Exception:
                pass


def prompt_int(label: str, *, minimum: int = 0) -> int:
    while True:
        raw_value = read_line(f"{label}: ")
        try:
            parsed = int(raw_value)
        except ValueError:
            print("Sayı girmen gerekiyor.")
            continue

        if parsed < minimum:
            print(f"En az {minimum} olmalı.")
            continue
        return parsed


def read_line(prompt: str) -> str:
    try:
        return input(prompt).strip()
    except EOFError as error:
        raise InputClosed from error


def play_blackjack_round(runtime: Runtime, bet: int) -> None:
    user = runtime.auth.require_user()
    ensure_bet(user.balance, bet)
    round_state = BlackjackRound(bet=bet)
    runtime.ui.show_blackjack(round_state)

    while not round_state.finished:
        action = typer.prompt("Hamle", default="stand").strip().lower()
        if action in {"hit", "cek"}:
            round_state.hit()
        elif action in {"stand", "dur"}:
            round_state.stand()
        else:
            runtime.ui.warning(
                "Hamle Bekleniyor",
                "Blackjack için hit/cek ya da stand/dur kullan.",
                category="blackjack",
            )
            continue
        runtime.ui.show_blackjack(round_state)

    result = round_state.to_result()
    updated_user = runtime.casino.settle_game(user.username, result)
    render_result(runtime.ui, "Blackjack Sonucu", updated_user.balance, result)


def interactive_admin_menu(runtime: Runtime) -> None:
    while True:
        print(
            "\n[Admin Menüsü]\n"
            "1. Kullanıcıları listele\n"
            "2. Kullanıcı oluştur\n"
            "3. Kullanıcı sil\n"
            "4. Bakiye ayarla\n"
            "5. Logları göster\n"
            "0. Geri dön\n"
        )
        try:
            choice = read_line("Seçim: ")
        except InputClosed:
            runtime.ui.info("Admin Menüsü Kapandı", "Girdi kapandı, admin menüsünden çıkılıyor.")
            return
        try:
            actor = runtime.auth.require_admin()
            if choice == "1":
                runtime.ui.show_users(runtime.casino.list_users())
            elif choice == "2":
                username = read_line("Yeni kullanıcı adı: ")
                password = read_line("Şifre: ")
                is_admin = read_line("Admin olsun mu? (e/h): ").lower() == "e"
                user = runtime.casino.create_user(
                    username,
                    password,
                    actor=actor.username,
                    is_admin=is_admin,
                )
                role = "admin" if is_admin else "oyuncu"
                runtime.ui.admin(
                    "Hesap Açıldı",
                    f"{user.username} için yeni {role} hesabı açıldı.\nBakiye: {user.balance} chip",
                )
            elif choice == "3":
                username = input("Silinecek kullanıcı: ").strip()
                runtime.casino.delete_user(username, actor=actor.username)
                runtime.ui.admin("Hesap Silindi", f"{username} masadan çıkarıldı.")
            elif choice == "4":
                username = input("Kullanıcı adı: ").strip()
                amount = prompt_int("Yeni bakiye", minimum=0)
                user = runtime.casino.set_balance(username, amount, actor=actor.username)
                runtime.ui.admin(
                    "Bakiye Güncellendi",
                    f"{user.username} yeni bakiyesi: {user.balance} chip",
                )
            elif choice == "5":
                limit = prompt_int("Kaç log gösterilsin", minimum=1)
                runtime.ui.show_logs(runtime.casino.logs(limit=limit))
            elif choice == "0":
                return
            else:
                runtime.ui.warning("Seçim Hatalı", "Admin menüsünde geçerli bir sayı seç.")
        except CasinoError as error:
            runtime.ui.error("Admin Hatası", str(error))


def interactive_launcher() -> None:
    while True:
        runtime = build_runtime()
        active_user = runtime.auth.current_user()
        runtime.ui.info(
            APP_NAME,
            (
                f"Aktif oyuncu: {active_user.username if active_user else 'yok'}\n"
                "1. Kayıt ol\n"
                "2. Giriş yap\n"
                "3. Profili göster\n"
                "4. Geçmişi göster\n"
                "5. Yazı tura oyna\n"
                "6. Rulet oyna\n"
                "7. Blackjack oyna\n"
                "8. Çıkış yap\n"
                "9. Admin menüsü\n"
                "0. Programı kapat"
            ),
            category="welcome",
        )
        try:
            choice = read_line("Seçim: ")
        except InputClosed:
            runtime.ui.info("Güle Güle", "Girdi kapandı, masa usulca kapanıyor.", category="general")
            return
        try:
            if choice == "1":
                username = read_line("Kullanıcı adı: ")
                password = read_line("Şifre: ")
                user = runtime.auth.register(username, password)
                runtime.ui.success(
                    "Yeni Oyuncu",
                    f"{user.username} masaya oturdu.\nBaşlangıç bakiyesi: {user.balance} chip",
                    category="auth",
                )
            elif choice == "2":
                username = read_line("Kullanıcı adı: ")
                password = read_line("Şifre: ")
                user = runtime.auth.login(username, password)
                runtime.ui.success(
                    "Mekana Giriş",
                    f"Hoş geldin {user.username}.\nMasanın mevcut bakiyesi: {user.balance} chip",
                    category="welcome",
                )
            elif choice == "3":
                runtime.ui.show_profile(runtime.auth.require_user())
            elif choice == "4":
                limit = prompt_int("Kaç kayıt gösterilsin", minimum=1)
                user = runtime.auth.require_user()
                runtime.ui.show_history(runtime.casino.history_for(user.username, limit=limit))
            elif choice == "5":
                user = runtime.auth.require_user()
                bet = prompt_int("Bahis miktarı", minimum=1)
                ensure_bet(user.balance, bet)
                side = read_line("Taraf (yazi/tura): ")
                result = play_coinflip(bet=bet, side=side)
                updated_user = runtime.casino.settle_game(user.username, result)
                render_result(runtime.ui, "Yazı Tura Sonucu", updated_user.balance, result)
            elif choice == "6":
                user = runtime.auth.require_user()
                bet = prompt_int("Bahis miktarı", minimum=1)
                ensure_bet(user.balance, bet)
                bet_type = read_line("Bahis tipi (color/parity/number): ")
                value = read_line("Değer: ")
                result = play_roulette(bet=bet, bet_type=bet_type, value=value)
                updated_user = runtime.casino.settle_game(user.username, result)
                render_result(runtime.ui, "Rulet Sonucu", updated_user.balance, result)
            elif choice == "7":
                bet = prompt_int("Bahis miktarı", minimum=1)
                play_blackjack_round(runtime, bet)
            elif choice == "8":
                username = runtime.auth.logout()
                runtime.ui.info("Masa Kapandı", f"{username} masadan kalktı.", category="auth")
            elif choice == "9":
                interactive_admin_menu(runtime)
            elif choice == "0":
                runtime.ui.info("Güle Güle", "Masa kapanıyor.", category="general")
                return
            else:
                runtime.ui.warning("Seçim Hatalı", "Geçerli bir menü numarası seç.")
        except InputClosed:
            runtime.ui.info("Güle Güle", "Girdi kapandı, masa usulca kapanıyor.", category="general")
            return
        except CasinoError as error:
            runtime.ui.error("Masada Terslik Var", str(error))


@app.command("init-db")
def init_db() -> None:
    runtime = build_runtime()
    runtime.ui.info(
        "Masa Hazır",
        (
            f"Veritabanı hazır: {runtime.db.paths.db_path}\n"
            f"Varsayılan admin: {DEFAULT_ADMIN_USERNAME} / {DEFAULT_ADMIN_PASSWORD}"
        ),
        category="welcome",
    )


@app.command("history")
def history(limit: int = typer.Option(10, "--limit", min=1, max=50)) -> None:
    runtime = build_runtime()
    try:
        user = runtime.auth.require_user()
        rows = runtime.casino.history_for(user.username, limit=limit)
        runtime.ui.show_history(rows)
    except CasinoError as error:
        fail(runtime.ui, error)


@auth_app.command("register")
def register(
    username: str = typer.Option(..., "--username", "-u", prompt=True),
    password: str = typer.Option(
        ...,
        "--password",
        "-p",
        prompt=True,
        hide_input=True,
        confirmation_prompt=True,
    ),
) -> None:
    runtime = build_runtime()
    try:
        user = runtime.auth.register(username, password)
        runtime.ui.success(
            "Yeni Oyuncu",
            f"{user.username} masaya oturdu.\nBaşlangıç bakiyesi: {user.balance} chip",
            category="auth",
        )
    except CasinoError as error:
        fail(runtime.ui, error)


@auth_app.command("login")
def login(
    username: str = typer.Option(..., "--username", "-u", prompt=True),
    password: str = typer.Option(..., "--password", "-p", prompt=True, hide_input=True),
) -> None:
    runtime = build_runtime()
    try:
        user = runtime.auth.login(username, password)
        runtime.ui.success(
            "Mekana Giriş",
            f"Hoş geldin {user.username}.\nMasanın mevcut bakiyesi: {user.balance} chip",
            category="welcome",
        )
    except CasinoError as error:
        fail(runtime.ui, error)


@auth_app.command("logout")
def logout() -> None:
    runtime = build_runtime()
    try:
        username = runtime.auth.logout()
        runtime.ui.info(
            "Masa Kapandı",
            f"{username} masadan kalktı.",
            category="auth",
        )
    except CasinoError as error:
        fail(runtime.ui, error)


@profile_app.command("show")
def profile_show() -> None:
    runtime = build_runtime()
    try:
        user = runtime.auth.require_user()
        runtime.ui.show_profile(user)
    except CasinoError as error:
        fail(runtime.ui, error)


@play_app.command("coinflip")
def coinflip(
    bet: int = typer.Option(..., "--bet", min=1),
    side: str = typer.Option(..., "--side"),
) -> None:
    runtime = build_runtime()
    try:
        user = runtime.auth.require_user()
        result = play_coinflip(bet=bet, side=side)
        updated_user = runtime.casino.settle_game(user.username, result)
        render_result(runtime.ui, "Yazı Tura Sonucu", updated_user.balance, result)
    except CasinoError as error:
        fail(runtime.ui, error)


@play_app.command("roulette")
def roulette(
    bet: int = typer.Option(..., "--bet", min=1),
    bet_type: str = typer.Option(..., "--bet-type"),
    value: str = typer.Option(..., "--value"),
) -> None:
    runtime = build_runtime()
    try:
        user = runtime.auth.require_user()
        result = play_roulette(bet=bet, bet_type=bet_type, value=value)
        updated_user = runtime.casino.settle_game(user.username, result)
        render_result(runtime.ui, "Rulet Sonucu", updated_user.balance, result)
    except CasinoError as error:
        fail(runtime.ui, error)


@play_app.command("blackjack")
def blackjack(
    bet: int = typer.Option(..., "--bet", min=1),
) -> None:
    runtime = build_runtime()
    try:
        play_blackjack_round(runtime, bet)
    except CasinoError as error:
        fail(runtime.ui, error)


@admin_users_app.command("list")
def admin_users_list() -> None:
    runtime = build_runtime()
    try:
        runtime.auth.require_admin()
        runtime.ui.show_users(runtime.casino.list_users())
    except CasinoError as error:
        fail(runtime.ui, error)


@admin_users_app.command("create")
def admin_users_create(
    username: str = typer.Option(..., "--username", "-u", prompt=True),
    password: str = typer.Option(
        ...,
        "--password",
        "-p",
        prompt=True,
        hide_input=True,
        confirmation_prompt=True,
    ),
    admin: bool = typer.Option(False, "--admin/--player"),
) -> None:
    runtime = build_runtime()
    try:
        actor = runtime.auth.require_admin()
        user = runtime.casino.create_user(
            username,
            password,
            actor=actor.username,
            is_admin=admin,
        )
        role = "admin" if admin else "oyuncu"
        runtime.ui.admin(
            "Hesap Açıldı",
            f"{user.username} için yeni {role} hesabı açıldı.\nBakiye: {user.balance} chip",
        )
    except CasinoError as error:
        fail(runtime.ui, error)


@admin_users_app.command("delete")
def admin_users_delete(username: str) -> None:
    runtime = build_runtime()
    try:
        actor = runtime.auth.require_admin()
        runtime.casino.delete_user(username, actor=actor.username)
        runtime.ui.admin(
            "Hesap Silindi",
            f"{username} masadan çıkarıldı.",
        )
    except CasinoError as error:
        fail(runtime.ui, error)


@admin_balance_app.command("set")
def admin_balance_set(
    username: str = typer.Option(..., "--username"),
    amount: int = typer.Option(..., "--amount", min=0),
) -> None:
    runtime = build_runtime()
    try:
        actor = runtime.auth.require_admin()
        user = runtime.casino.set_balance(username, amount, actor=actor.username)
        runtime.ui.admin(
            "Bakiye Güncellendi",
            f"{user.username} yeni bakiyesi: {user.balance} chip",
        )
    except CasinoError as error:
        fail(runtime.ui, error)


@admin_logs_app.command("show")
def admin_logs_show(limit: int = typer.Option(20, "--limit", min=1, max=100)) -> None:
    runtime = build_runtime()
    try:
        runtime.auth.require_admin()
        runtime.ui.show_logs(runtime.casino.logs(limit=limit))
    except CasinoError as error:
        fail(runtime.ui, error)


def run() -> None:
    configure_console()
    if len(sys.argv) == 1:
        interactive_launcher()
        return
    app()
