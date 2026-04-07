from __future__ import annotations

from .config import DEFAULT_STARTING_BALANCE
from .db import Database
from .exceptions import AuthenticationError, AuthorizationError, ValidationError
from .models import User
from .security import hash_password, verify_password
from .session import SessionManager


class AuthService:
    def __init__(self, db: Database, sessions: SessionManager):
        self.db = db
        self.sessions = sessions

    def register(
        self,
        username: str,
        password: str,
        *,
        is_admin: bool = False,
        initial_balance: int = DEFAULT_STARTING_BALANCE,
    ) -> User:
        clean_username = self._validate_username(username)
        self._validate_password(password)

        existing = self.db.fetch_one(
            "SELECT id FROM users WHERE username = ?",
            (clean_username,),
        )
        if existing is not None:
            raise ValidationError("Bu kullanıcı adı masada zaten oturuyor.")

        with self.db.transaction() as connection:
            connection.execute(
                """
                INSERT INTO users(username, password_hash, is_admin, balance)
                VALUES (?, ?, ?, ?)
                """,
                (
                    clean_username,
                    hash_password(password),
                    int(is_admin),
                    initial_balance,
                ),
            )
            connection.execute(
                "INSERT INTO audit_logs(username, action) VALUES (?, ?)",
                (clean_username, "Yeni oyuncu hesabı açıldı."),
            )
            row = connection.execute(
                "SELECT * FROM users WHERE username = ?",
                (clean_username,),
            ).fetchone()

        return User.from_row(row)

    def login(self, username: str, password: str) -> User:
        clean_username = username.strip()
        row = self.db.fetch_one(
            "SELECT * FROM users WHERE username = ?",
            (clean_username,),
        )
        if row is None or not verify_password(password, row["password_hash"]):
            raise AuthenticationError("Kullanıcı adı veya şifre hatalı.")

        user = User.from_row(row)
        self.sessions.create(user.username)
        with self.db.transaction() as connection:
            connection.execute(
                "INSERT INTO audit_logs(username, action) VALUES (?, ?)",
                (user.username, "Giriş yapıldı."),
            )
        return user

    def logout(self) -> str:
        current = self.sessions.current_username()
        if current is None:
            raise AuthenticationError("Önce bir oyuncu girişi olmalı.")

        with self.db.transaction() as connection:
            connection.execute(
                "INSERT INTO audit_logs(username, action) VALUES (?, ?)",
                (current, "Çıkış yapıldı."),
            )

        self.sessions.clear()
        return current

    def current_user(self) -> User | None:
        current = self.sessions.current_username()
        if current is None:
            return None

        row = self.db.fetch_one(
            "SELECT * FROM users WHERE username = ?",
            (current,),
        )
        if row is None:
            self.sessions.clear()
            return None
        return User.from_row(row)

    def require_user(self) -> User:
        user = self.current_user()
        if user is None:
            raise AuthenticationError("Bu masa için önce giriş yapman gerekiyor.")
        return user

    def require_admin(self) -> User:
        user = self.require_user()
        if not user.is_admin:
            raise AuthorizationError("Bu komut sadece Çakır'ın adamlarına açık.")
        return user

    @staticmethod
    def _validate_username(username: str) -> str:
        clean_username = username.strip()
        if len(clean_username) < 3:
            raise ValidationError("Kullanıcı adı en az 3 karakter olmalı.")
        if " " in clean_username:
            raise ValidationError("Kullanıcı adında boşluk kullanılamaz.")
        return clean_username

    @staticmethod
    def _validate_password(password: str) -> None:
        if len(password) < 4:
            raise ValidationError("Şifre en az 4 karakter olmalı.")
