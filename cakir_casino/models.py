from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class User:
    id: int
    username: str
    is_admin: bool
    balance: int
    created_at: str
    password_hash: str = ""

    @classmethod
    def from_row(cls, row: sqlite3.Row) -> "User":
        return cls(
            id=row["id"],
            username=row["username"],
            is_admin=bool(row["is_admin"]),
            balance=row["balance"],
            created_at=row["created_at"],
            password_hash=row["password_hash"],
        )


@dataclass(slots=True)
class GameResult:
    game: str
    bet: int
    outcome: str
    net_change: int
    details: dict[str, Any] = field(default_factory=dict)
    summary: str = ""

    def details_json(self) -> str:
        return json.dumps(self.details, ensure_ascii=False, sort_keys=True)
