from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import time
from dataclasses import dataclass
from pathlib import Path

from fastapi import HTTPException, Request
from fastapi.responses import Response


SESSION_COOKIE_NAME = "cleair_demo_session"
SESSION_COOKIE_MAX_AGE_SECONDS = 60 * 60 * 24 * 7
AUTH_DETAIL = "Authentication required"


@dataclass(frozen=True)
class AuthConfig:
    enabled: bool
    secret_key: str
    code_hashes: frozenset[str]
    secure_cookie: bool


def _hash_code(access_code: str) -> str:
    return hashlib.sha256(access_code.encode("utf-8")).hexdigest()


def load_auth_config() -> AuthConfig:
    secret_key = os.environ.get("CLEAIR_AUTH_SECRET", "")
    codes_path = Path(os.environ.get("CLEAIR_AUTH_CODES_PATH", "auth_codes.json"))
    secure_cookie = os.environ.get("CLEAIR_AUTH_SECURE_COOKIE", "").lower() in {"1", "true", "yes", "on"}
    code_hashes = frozenset(_load_code_hashes(codes_path)) if secret_key else frozenset()
    return AuthConfig(
        enabled=bool(secret_key),
        secret_key=secret_key,
        code_hashes=code_hashes,
        secure_cookie=secure_cookie,
    )


def _load_code_hashes(codes_path: Path) -> set[str]:
    if not codes_path.exists():
        return set()
    payload = json.loads(codes_path.read_text())
    return {
        _hash_code(access_code)
        for access_code in payload.get("codes", [])
        if isinstance(access_code, str) and access_code.isdigit() and len(access_code) == 6
    }


def _sign_value(secret_key: str, value: str) -> str:
    signature = hmac.new(secret_key.encode("utf-8"), value.encode("utf-8"), hashlib.sha256).hexdigest()
    return f"{value}.{signature}"


def _read_signed_value(secret_key: str, signed_value: str | None) -> str | None:
    if not signed_value or "." not in signed_value:
        return None
    value, provided_signature = signed_value.rsplit(".", 1)
    expected_signature = hmac.new(secret_key.encode("utf-8"), value.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(provided_signature, expected_signature):
        return None
    issued_at, _, _ = value.partition(":")
    if not issued_at.isdigit():
        return None
    if time.time() - int(issued_at) > SESSION_COOKIE_MAX_AGE_SECONDS:
        return None
    return value


def _make_session_token(secret_key: str) -> str:
    issued_at = str(int(time.time()))
    session_nonce = secrets.token_hex(16)
    return _sign_value(secret_key, f"{issued_at}:{session_nonce}")


def set_authenticated_session(response: Response, auth_config: AuthConfig) -> None:
    response.set_cookie(
        SESSION_COOKIE_NAME,
        _make_session_token(auth_config.secret_key),
        httponly=True,
        samesite="lax",
        secure=auth_config.secure_cookie,
        max_age=SESSION_COOKIE_MAX_AGE_SECONDS,
    )


def clear_authenticated_session(response: Response, auth_config: AuthConfig) -> None:
    response.delete_cookie(
        SESSION_COOKIE_NAME, httponly=True, samesite="lax", secure=auth_config.secure_cookie
    )


def is_authenticated(request: Request, auth_config: AuthConfig) -> bool:
    if not auth_config.enabled:
        return True
    signed_value = request.cookies.get(SESSION_COOKIE_NAME)
    return _read_signed_value(auth_config.secret_key, signed_value) is not None


def require_authenticated_request(request: Request, auth_config: AuthConfig) -> None:
    if not is_authenticated(request, auth_config):
        raise HTTPException(status_code=401, detail=AUTH_DETAIL)


def verify_access_code(access_code: str, auth_config: AuthConfig) -> bool:
    if not auth_config.enabled:
        return True
    if not (access_code.isdigit() and len(access_code) == 6):
        return False
    return _hash_code(access_code) in auth_config.code_hashes
