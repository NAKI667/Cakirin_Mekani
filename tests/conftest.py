from __future__ import annotations

import pytest
from typer.testing import CliRunner

from cakir_casino.auth import AuthService
from cakir_casino.config import get_app_paths
from cakir_casino.db import Database
from cakir_casino.services import CasinoService
from cakir_casino.session import SessionManager


@pytest.fixture()
def app_home(tmp_path, monkeypatch):
    home = tmp_path / ".cakir_casino"
    monkeypatch.setenv("CAKIR_CASINO_HOME", str(home))
    return home


@pytest.fixture()
def services(app_home):
    paths = get_app_paths()
    db = Database(paths)
    db.initialize()
    session = SessionManager(paths.session_path)
    auth = AuthService(db, session)
    casino = CasinoService(db, auth)
    return {
        "paths": paths,
        "db": db,
        "session": session,
        "auth": auth,
        "casino": casino,
    }


@pytest.fixture()
def runner():
    return CliRunner()
