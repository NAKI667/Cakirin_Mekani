from __future__ import annotations

import hashlib
import hmac
import secrets

PBKDF2_ROUNDS = 200_000


def hash_password(password: str, *, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ROUNDS,
    )
    return f"pbkdf2_sha256${PBKDF2_ROUNDS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, rounds, salt_hex, digest_hex = stored_hash.split("$", maxsplit=3)
    except ValueError:
        return False

    if algorithm != "pbkdf2_sha256":
        return False

    expected = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        bytes.fromhex(salt_hex),
        int(rounds),
    )
    return hmac.compare_digest(expected.hex(), digest_hex)
