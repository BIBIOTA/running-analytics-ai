from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from datetime import timedelta
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import Settings, get_settings
from app.models.common import utc_now

JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRES_IN = timedelta(hours=1)
TOKEN_NONCE_BYTES = 12


class InvalidTokenError(ValueError):
    pass


def create_access_token(subject: str, *, settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    expires_at = utc_now() + ACCESS_TOKEN_EXPIRES_IN
    issued_at = utc_now()
    header = {"alg": JWT_ALGORITHM, "typ": "JWT"}
    payload = {
        "sub": subject,
        "type": "access",
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    signing_input = ".".join(
        [
            _base64url_encode_json(header),
            _base64url_encode_json(payload),
        ]
    )
    signature = hmac.new(
        settings.jwt_secret.encode("utf-8"),
        signing_input.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return f"{signing_input}.{_base64url_encode(signature)}"


def decode_access_token(token: str, *, settings: Settings | None = None) -> dict[str, Any]:
    settings = settings or get_settings()
    try:
        header_segment, payload_segment, signature_segment = token.split(".")
        signing_input = f"{header_segment}.{payload_segment}"
        expected_signature = hmac.new(
            settings.jwt_secret.encode("utf-8"),
            signing_input.encode("ascii"),
            hashlib.sha256,
        ).digest()
        provided_signature = _base64url_decode(signature_segment)
        if not hmac.compare_digest(expected_signature, provided_signature):
            raise InvalidTokenError("Invalid or expired token")

        header = json.loads(_base64url_decode(header_segment))
        payload = json.loads(_base64url_decode(payload_segment))
    except (ValueError, TypeError, json.JSONDecodeError) as exc:
        raise InvalidTokenError("Invalid or expired token") from exc

    if header.get("alg") != JWT_ALGORITHM:
        raise InvalidTokenError("Invalid or expired token")
    if payload.get("type") != "access" or not payload.get("sub"):
        raise InvalidTokenError("Invalid or expired token")
    if int(payload.get("exp", 0)) <= int(utc_now().timestamp()):
        raise InvalidTokenError("Invalid or expired token")
    return payload


def encrypt_token(token: str, *, settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    key = _encryption_key(settings)
    nonce = os.urandom(TOKEN_NONCE_BYTES)
    ciphertext = AESGCM(key).encrypt(nonce, token.encode("utf-8"), None)
    return base64.urlsafe_b64encode(nonce + ciphertext).decode("ascii")


def decrypt_token(encrypted_token: str, *, settings: Settings | None = None) -> str:
    settings = settings or get_settings()
    try:
        raw = base64.urlsafe_b64decode(encrypted_token.encode("ascii"))
        nonce = raw[:TOKEN_NONCE_BYTES]
        ciphertext = raw[TOKEN_NONCE_BYTES:]
        return AESGCM(_encryption_key(settings)).decrypt(nonce, ciphertext, None).decode("utf-8")
    except Exception as exc:
        raise InvalidTokenError("Invalid encrypted token") from exc


def _encryption_key(settings: Settings) -> bytes:
    return hashlib.sha256(settings.encryption_key.encode("utf-8")).digest()


def _base64url_encode_json(value: dict[str, Any]) -> str:
    raw = json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return _base64url_encode(raw)


def _base64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _base64url_decode(value: str) -> bytes:
    padded = value + "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(padded.encode("ascii"))
