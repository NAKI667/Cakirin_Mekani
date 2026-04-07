from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path

APP_NAME = "Çakır'ın Mekanı"
APP_SLUG = "cakir-casino"
DEFAULT_HOME_DIR = ".cakir_casino"
DEFAULT_DB_NAME = "casino.db"
DEFAULT_SESSION_NAME = "session.json"
DEFAULT_STARTING_BALANCE = 1000
DEFAULT_ADMIN_USERNAME = "cakir"
DEFAULT_ADMIN_PASSWORD = "istanbul"


@dataclass(frozen=True, slots=True)
class AppPaths:
    home: Path
    db_path: Path
    session_path: Path


def get_app_paths() -> AppPaths:
    override = os.environ.get("CAKIR_CASINO_HOME")
    base_dir = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path.cwd()
    home = (
        Path(override).expanduser().resolve()
        if override
        else (base_dir / DEFAULT_HOME_DIR).resolve()
    )
    return AppPaths(
        home=home,
        db_path=home / DEFAULT_DB_NAME,
        session_path=home / DEFAULT_SESSION_NAME,
    )
