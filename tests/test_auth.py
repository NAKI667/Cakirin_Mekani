from __future__ import annotations

import pytest

from cakir_casino.exceptions import AuthenticationError, ValidationError


def test_register_duplicate_user_fails(services):
    auth = services["auth"]
    user = auth.register("polat", "derinmasa")

    assert user.balance == 1000

    with pytest.raises(ValidationError):
        auth.register("polat", "baskasifre")


def test_login_persists_session(services):
    auth = services["auth"]
    session = services["session"]

    auth.register("elif", "kurtlarvadisi")
    user = auth.login("elif", "kurtlarvadisi")

    assert user.username == "elif"
    assert session.current_username() == "elif"
    assert auth.current_user().username == "elif"


def test_wrong_password_fails(services):
    auth = services["auth"]
    auth.register("memati", "saglamkapi")

    with pytest.raises(AuthenticationError):
        auth.login("memati", "yanlissifre")
