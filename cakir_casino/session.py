from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


class SessionManager:
    def __init__(self, session_path: Path):
        self.session_path = session_path

    def load(self) -> dict[str, str] | None:
        try:
            payload = json.loads(self.session_path.read_text(encoding="utf-8"))
        except (FileNotFoundError, UnicodeDecodeError, json.JSONDecodeError):
            return None

        if not isinstance(payload, dict):
            return None
        username = payload.get("username")
        if not isinstance(username, str) or not username.strip():
            return None
        return payload

    def current_username(self) -> str | None:
        payload = self.load()
        if not payload:
            return None
        return payload.get("username")

    def create(self, username: str) -> None:
        payload = {
            "username": username,
            "logged_in_at": datetime.now(timezone.utc).isoformat(),
        }
        self.session_path.parent.mkdir(parents=True, exist_ok=True)
        self.session_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def clear(self) -> str | None:
        payload = self.load() if self.session_path.exists() else None
        username = payload.get("username") if payload else None
        self.session_path.unlink(missing_ok=True)
        return username
