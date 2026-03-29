from __future__ import annotations

from fastapi.testclient import TestClient
import pytest

from cleair_backend import main
from cleair_backend.auth import AuthConfig, SESSION_COOKIE_NAME, _sign_value
from cleair_backend.store import TraceStore


@pytest.fixture(autouse=True)
def reset_app_state() -> None:
    original_auth_config = main.auth_config
    original_store = main.store
    main.auth_config = AuthConfig(
        enabled=True,
        secret_key="test-secret",
        code_hashes=frozenset(
            {
                "8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92",
            }
        ),
        secure_cookie=False,
    )
    main.store = TraceStore()
    try:
        yield
    finally:
        main.auth_config = original_auth_config
        main.store = original_store


def test_protected_routes_require_authenticated_session() -> None:
    client = TestClient(main.app)

    response = client.get("/channels")

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}


def test_valid_code_sets_session_cookie_and_unlocks_routes() -> None:
    client = TestClient(main.app)

    verify_response = client.post("/auth/verify", json={"code": "123456"})
    channels_response = client.get("/channels")

    assert verify_response.status_code == 200
    assert verify_response.json() == {"authenticated": True}
    assert channels_response.status_code == 200
    assert channels_response.json() == []


def test_invalid_code_is_rejected() -> None:
    client = TestClient(main.app)

    response = client.post("/auth/verify", json={"code": "123455"})

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}


def test_expired_signed_cookie_is_rejected() -> None:
    client = TestClient(main.app)
    expired_cookie = _sign_value(main.auth_config.secret_key, "1:expired-session")
    client.cookies.set(SESSION_COOKIE_NAME, expired_cookie)

    response = client.get("/channels")

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}


def test_trace_ingest_still_accepts_channel_api_key_without_session() -> None:
    client = TestClient(main.app)
    _, api_key = main.store.create_channel()

    response = client.post(
        "/v1/events",
        headers={"X-Channel-API-Key": api_key},
        json={"runId": "run-1", "events": []},
    )

    assert response.status_code == 204
