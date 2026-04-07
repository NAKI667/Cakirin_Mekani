from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from typing import Iterator, Sequence

from .config import (
    DEFAULT_ADMIN_PASSWORD,
    DEFAULT_ADMIN_USERNAME,
    DEFAULT_STARTING_BALANCE,
    AppPaths,
    get_app_paths,
)
from .security import hash_password

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    is_admin INTEGER NOT NULL DEFAULT 0,
    balance INTEGER NOT NULL DEFAULT 1000 CHECK(balance >= 0),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS game_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    game TEXT NOT NULL,
    bet INTEGER NOT NULL CHECK(bet > 0),
    outcome TEXT NOT NULL,
    payout INTEGER NOT NULL,
    balance_after INTEGER NOT NULL,
    details TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    action TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_game_history_username_created_at
ON game_history(username, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_audit_logs_username_created_at
ON audit_logs(username, created_at DESC);
"""


class Database:
    def __init__(self, paths: AppPaths | None = None):
        self.paths = paths or get_app_paths()

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        self.paths.home.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.paths.db_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        with self.transaction() as connection:
            connection.executescript(SCHEMA)
            self._seed_admin(connection)

    def _seed_admin(self, connection: sqlite3.Connection) -> None:
        row = connection.execute(
            "SELECT id FROM users WHERE username = ?",
            (DEFAULT_ADMIN_USERNAME,),
        ).fetchone()
        if row is not None:
            return

        connection.execute(
            """
            INSERT INTO users(username, password_hash, is_admin, balance)
            VALUES (?, ?, 1, ?)
            """,
            (
                DEFAULT_ADMIN_USERNAME,
                hash_password(DEFAULT_ADMIN_PASSWORD),
                DEFAULT_STARTING_BALANCE,
            ),
        )
        connection.execute(
            "INSERT INTO audit_logs(username, action) VALUES (?, ?)",
            (
                DEFAULT_ADMIN_USERNAME,
                "Masa kuruldu ve varsayılan admin hesabı açıldı.",
            ),
        )

    def fetch_one(
        self,
        query: str,
        params: Sequence[object] = (),
    ) -> sqlite3.Row | None:
        with self.transaction() as connection:
            return connection.execute(query, params).fetchone()

    def fetch_all(
        self,
        query: str,
        params: Sequence[object] = (),
    ) -> list[sqlite3.Row]:
        with self.transaction() as connection:
            return connection.execute(query, params).fetchall()
