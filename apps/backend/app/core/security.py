from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from datetime import datetime, timedelta, timezone

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import get_settings

JWT_ALGORITHM = "HS256"
JWT_EXPIRES_IN = timedelta(hours=1)
UTC = getattr(__import__("datetime"), "UTC", timezone.__dict__["utc"])
_NONCE_SIZE = 12


def create_access_token(user_id: str) -> str:
    settings = get_settings()
    now = datetime.now(UTC)
    header = {"alg": JWT_ALGORITHM, "typ": "JWT"}
    payload = {
        "sub": user_id,
        "iat": int(now.timestamp()),
        "exp": int((now + JWT_EXPIRES_IN).timestamp()),
    }
    signing_input = ".".join([_b64_json(header), _b64_json(payload)])
    signature = _sign(signing_input, settings.jwt_secret)
    return f"{signing_input}.{signature}"


def decode_access_token(token: str) -> str:
    settings = get_settings()
    try:
        header_part, payload_part, signature = token.split(".")
        signing_input = f"{header_part}.{payload_part}"
        if not hmac.compare_digest(signature, _sign(signing_input, settings.jwt_secret)):
            raise ValueError("Invalid or expired token")
        header = _b64_decode_json(header_part)
        if header.get("alg") != JWT_ALGORITHM:
            raise ValueError("Invalid or expired token")
        payload = _b64_decode_json(payload_part)
        if int(payload.get("exp", 0)) < int(datetime.now(UTC).timestamp()):
            raise ValueError("Invalid or expired token")
        user_id = payload.get("sub")
    except Exception as exc:
        raise ValueError("Invalid or expired token") from exc
    if not isinstance(user_id, str) or not user_id:
        raise ValueError("Invalid or expired token")
    return user_id


def _encryption_key() -> bytes:
    raw_key = get_settings().encryption_key
    try:
        decoded = base64.urlsafe_b64decode(raw_key)
        if len(decoded) == 32:
            return decoded
    except Exception:
        pass

    key = raw_key.encode("utf-8")
    if len(key) != 32:
        raise ValueError("ENCRYPTION_KEY must be 32 bytes or base64-encoded 32 bytes")
    return key


def _b64_json(value: dict[str, object]) -> str:
    data = json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return _b64_encode(data)


def _b64_decode_json(value: str) -> dict[str, object]:
    return json.loads(_b64_decode(value))


def _sign(signing_input: str, secret: str) -> str:
    digest = hmac.new(
        secret.encode("utf-8"),
        signing_input.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return _b64_encode(digest)


def _b64_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64_decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def encrypt_token(token: str) -> str:
    nonce = os.urandom(_NONCE_SIZE)
    encrypted = AESGCM(_encryption_key()).encrypt(nonce, token.encode("utf-8"), None)
    return base64.urlsafe_b64encode(nonce + encrypted).decode("ascii")


def decrypt_token(encrypted_token: str) -> str:
    data = base64.urlsafe_b64decode(encrypted_token.encode("ascii"))
    nonce = data[:_NONCE_SIZE]
    ciphertext = data[_NONCE_SIZE:]
    return AESGCM(_encryption_key()).decrypt(nonce, ciphertext, None).decode("utf-8")
