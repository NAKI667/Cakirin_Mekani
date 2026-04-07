from __future__ import annotations

import sqlite3

from .auth import AuthService
from .db import Database
from .exceptions import NotFoundError, ValidationError
from .models import GameResult, User


class CasinoService:
    def __init__(self, db: Database, auth: AuthService):
        self.db = db
        self.auth = auth

    def create_user(
        self,
        username: str,
        password: str,
        *,
        actor: str,
        is_admin: bool = False,
    ) -> User:
        user = self.auth.register(username, password, is_admin=is_admin)
        role = "admin" if is_admin else "oyuncu"
        self.log_action(actor, f"Yeni {role} hesabı açtı: {user.username}")
        return user

    def list_users(self) -> list[User]:
        rows = self.db.fetch_all(
            "SELECT * FROM users ORDER BY is_admin DESC, username ASC",
        )
        return [User.from_row(row) for row in rows]

    def delete_user(self, username: str, *, actor: str) -> None:
        with self.db.transaction() as connection:
            row = self._user_row(connection, username)
            if row is None:
                raise NotFoundError("Silinecek kullanıcı bulunamadı.")

            if username == actor:
                raise ValidationError("Aktif oyuncu kendi hesabını silemez.")

            if row["is_admin"]:
                admin_count = connection.execute(
                    "SELECT COUNT(*) AS count FROM users WHERE is_admin = 1",
                ).fetchone()["count"]
                if admin_count <= 1:
                    raise ValidationError("Masada en az bir admin kalmalı.")

            connection.execute(
                "DELETE FROM users WHERE username = ?",
                (username,),
            )
            connection.execute(
                "INSERT INTO audit_logs(username, action) VALUES (?, ?)",
                (actor, f"Kullanıcı hesabını sildi: {username}"),
            )

    def set_balance(self, username: str, amount: int, *, actor: str) -> User:
        if amount < 0:
            raise ValidationError("Bakiye sıfırın altına inemez.")

        with self.db.transaction() as connection:
            row = self._user_row(connection, username)
            if row is None:
                raise NotFoundError("Bakiyesi değiştirilecek kullanıcı bulunamadı.")

            connection.execute(
                "UPDATE users SET balance = ? WHERE username = ?",
                (amount, username),
            )
            connection.execute(
                "INSERT INTO audit_logs(username, action) VALUES (?, ?)",
                (actor, f"Bakiye ayarlandı: {username} -> {amount} chip"),
            )
            updated = self._user_row(connection, username)

        return User.from_row(updated)

    def settle_game(self, username: str, result: GameResult) -> User:
        if result.bet <= 0:
            raise ValidationError("Bahis miktarı sıfırdan büyük olmalı.")

        with self.db.transaction() as connection:
            row = self._user_row(connection, username)
            if row is None:
                raise NotFoundError("Oyuncu bulunamadı.")

            user = User.from_row(row)
            if user.balance < result.bet:
                raise ValidationError("Bu hamle için yeterli chip yok.")

            new_balance = user.balance + result.net_change
            if new_balance < 0:
                raise ValidationError("Bahis hesabı tutarsız; bakiye negatife düştü.")

            connection.execute(
                "UPDATE users SET balance = ? WHERE username = ?",
                (new_balance, username),
            )
            connection.execute(
                """
                INSERT INTO game_history(
                    username, game, bet, outcome, payout, balance_after, details
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    username,
                    result.game,
                    result.bet,
                    result.outcome,
                    result.net_change,
                    new_balance,
                    result.details_json(),
                ),
            )
            connection.execute(
                "INSERT INTO audit_logs(username, action) VALUES (?, ?)",
                (
                    username,
                    f"Oyun oynandı: {result.game} / {result.outcome} / {result.net_change:+} chip",
                ),
            )
            updated = self._user_row(connection, username)

        return User.from_row(updated)

    def history_for(self, username: str, limit: int = 10) -> list[sqlite3.Row]:
        safe_limit = max(1, min(limit, 50))
        return self.db.fetch_all(
            """
            SELECT game, bet, outcome, payout, balance_after, details, created_at
            FROM game_history
            WHERE username = ?
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (username, safe_limit),
        )

    def logs(self, limit: int = 50) -> list[sqlite3.Row]:
        safe_limit = max(1, min(limit, 100))
        return self.db.fetch_all(
            """
            SELECT username, action, created_at
            FROM audit_logs
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (safe_limit,),
        )

    def log_action(self, username: str, action: str) -> None:
        with self.db.transaction() as connection:
            connection.execute(
                "INSERT INTO audit_logs(username, action) VALUES (?, ?)",
                (username, action),
            )

    @staticmethod
    def _user_row(
        connection: sqlite3.Connection,
        username: str,
    ) -> sqlite3.Row | None:
        return connection.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,),
        ).fetchone()
