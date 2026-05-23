from __future__ import annotations

import base64
import hashlib
import os
from datetime import timedelta
from functools import lru_cache
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from jose import JWTError, jwt

from app.core.config import Settings, get_settings
from app.models.common import utc_now

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRES_IN = timedelta(hours=1)
TOKEN_NONCE_BYTES = 12


class InvalidTokenError(ValueError):
    pass


def create_access_token(subject: str, *, settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    now = utc_now()
    expires_at = now + ACCESS_TOKEN_EXPIRES_IN
    payload = {
        "sub": subject,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str, *, settings: Settings | None = None) -> dict[str, Any]:
    settings = settings or get_settings()
    try:
        payload: dict[str, Any] = jwt.decode(token, settings.jwt_secret, algorithms=[JWT_ALGORITHM])
    except JWTError as exc:
        raise InvalidTokenError("Invalid or expired token") from exc
    if payload.get("type") != "access" or not payload.get("sub"):
        raise InvalidTokenError("Invalid or expired token")
    return payload


def encrypt_token(token: str, *, settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    key = _encryption_key(settings.encryption_key)
    nonce = os.urandom(TOKEN_NONCE_BYTES)
    ciphertext = AESGCM(key).encrypt(nonce, token.encode("utf-8"), None)
    return base64.urlsafe_b64encode(nonce + ciphertext).decode("ascii")


def decrypt_token(encrypted_token: str, *, settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    try:
        raw = base64.urlsafe_b64decode(encrypted_token.encode("ascii"))
        nonce = raw[:TOKEN_NONCE_BYTES]
        ciphertext = raw[TOKEN_NONCE_BYTES:]
        return AESGCM(_encryption_key(settings.encryption_key)).decrypt(nonce, ciphertext, None).decode("utf-8")
    except Exception as exc:
        raise InvalidTokenError("Invalid encrypted token") from exc


@lru_cache(maxsize=1)
def _encryption_key(encryption_key: str) -> bytes:
    return hashlib.sha256(encryption_key.encode("utf-8")).digest()
