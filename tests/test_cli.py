from __future__ import annotations

from cakir_casino.cli import app


def test_help_smoke(runner, app_home):
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "Çakır'ın Mekanı" in result.output


def test_register_login_profile_flow(runner, app_home):
    register = runner.invoke(
        app,
        [
            "auth",
            "register",
            "--username",
            "polat",
            "--password",
            "derinmasa",
        ],
    )
    login = runner.invoke(
        app,
        [
            "auth",
            "login",
            "--username",
            "polat",
            "--password",
            "derinmasa",
        ],
    )
    profile = runner.invoke(app, ["profile", "show"])

    assert register.exit_code == 0
    assert login.exit_code == 0
    assert profile.exit_code == 0
    assert "polat" in profile.output
    assert "1000 chip" in profile.output


def test_coinflip_history_and_blackjack_smoke(runner, app_home):
    runner.invoke(
        app,
        [
            "auth",
            "register",
            "--username",
            "memati",
            "--password",
            "saglamkapi",
        ],
    )
    runner.invoke(
        app,
        [
            "auth",
            "login",
            "--username",
            "memati",
            "--password",
            "saglamkapi",
        ],
    )

    coinflip = runner.invoke(
        app,
        ["play", "coinflip", "--bet", "100", "--side", "yazi"],
    )
    blackjack = runner.invoke(
        app,
        ["play", "blackjack", "--bet", "100"],
        input="stand\n",
    )
    history = runner.invoke(app, ["history", "--limit", "5"])

    assert coinflip.exit_code == 0
    assert blackjack.exit_code == 0
    assert history.exit_code == 0
    assert "coinflip" in history.output
    assert "Blackjack" in blackjack.output


def test_admin_commands_smoke(runner, app_home):
    login = runner.invoke(
        app,
        [
            "auth",
            "login",
            "--username",
            "cakir",
            "--password",
            "istanbul",
        ],
    )
    create = runner.invoke(
        app,
        [
            "admin",
            "users",
            "create",
            "--username",
            "lazziya",
            "--password",
            "mekan123",
            "--player",
        ],
    )
    balance = runner.invoke(
        app,
        [
            "admin",
            "balance",
            "set",
            "--username",
            "lazziya",
            "--amount",
            "1500",
        ],
    )
    logs = runner.invoke(app, ["admin", "logs", "show", "--limit", "5"])

    assert login.exit_code == 0
    assert create.exit_code == 0
    assert balance.exit_code == 0
    assert logs.exit_code == 0
    assert "lazziya" in logs.output
