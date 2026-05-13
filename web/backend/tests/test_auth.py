from __future__ import annotations

import asyncio
import json

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

    response = client.get("/agents")

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}


def test_valid_code_sets_session_cookie_and_unlocks_routes() -> None:
    client = TestClient(main.app)

    verify_response = client.post("/auth/verify", json={"code": "123456"})
    channel_response = client.post("/channel")
    agents_response = client.get("/agents")

    assert verify_response.status_code == 200
    assert verify_response.json() == {"authenticated": True}
    assert channel_response.status_code == 201
    assert len(channel_response.json()["apiKey"]) == 32
    assert agents_response.status_code == 200
    assert agents_response.json() == []


def test_channel_creation_is_idempotent() -> None:
    client = TestClient(main.app)

    client.post("/auth/verify", json={"code": "123456"})
    first_response = client.post("/channel")
    second_response = client.post("/channel")

    assert first_response.json() == second_response.json()


def test_invalid_code_is_rejected() -> None:
    client = TestClient(main.app)

    response = client.post("/auth/verify", json={"code": "123455"})

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}


def test_expired_signed_cookie_is_rejected() -> None:
    client = TestClient(main.app)
    expired_cookie = _sign_value(main.auth_config.secret_key, "1:expired-session")
    client.cookies.set(SESSION_COOKIE_NAME, expired_cookie)

    response = client.get("/agents")

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}


def test_trace_ingest_still_accepts_channel_api_key_without_session() -> None:
    client = TestClient(main.app)
    api_key = main.store.ensure_channel()

    response = client.post(
        "/v1/events",
        headers={"X-Channel-API-Key": api_key},
        json={"runId": "run-1", "events": [{"type": "run_started", "runId": "run-1", "runLabel": "Agent"}]},
    )

    assert response.status_code == 204


def test_agents_overwrite_by_service_name() -> None:
    client = TestClient(main.app)
    client.post("/auth/verify", json={"code": "123456"})
    api_key = client.post("/channel").json()["apiKey"]

    first_response = client.post(
        "/v1/events",
        headers={"X-Channel-API-Key": api_key},
        json={
            "runId": "run-1",
            "events": [
                {"type": "run_started", "runId": "run-1", "runLabel": "Agent"},
                {"type": "node_added", "node": {"id": "span-1", "parentId": None, "label": "first", "subtitle": "Agent", "type": "agent", "whatDescription": "first"}},
            ],
        },
    )
    second_response = client.post(
        "/v1/events",
        headers={"X-Channel-API-Key": api_key},
        json={
            "runId": "run-2",
            "events": [
                {"type": "run_started", "runId": "run-2", "runLabel": "Agent"},
                {"type": "node_added", "node": {"id": "span-2", "parentId": None, "label": "second", "subtitle": "Agent", "type": "agent", "whatDescription": "second"}},
            ],
        },
    )
    agents_response = client.get("/agents")

    assert first_response.status_code == 204
    assert second_response.status_code == 204
    assert agents_response.status_code == 200
    assert agents_response.json() == [
        {
            "serviceName": "Agent",
            "runId": "run-2",
            "events": [
                {"type": "run_started", "runId": "run-2", "runLabel": "Agent"},
                {"type": "node_added", "node": {"id": "span-2", "parentId": None, "label": "second", "subtitle": "Agent", "type": "agent", "whatDescription": "second"}},
            ],
        }
    ]


def test_stream_replays_existing_agent_events() -> None:
    main.store.start_run("Agent", "run-1")
    main.store.append_events(
        "Agent",
        [
            {"type": "run_started", "runId": "run-1", "runLabel": "Agent"},
            {"type": "node_added", "node": {"id": "span-1", "parentId": None, "label": "first", "subtitle": "Agent", "type": "agent", "whatDescription": "first"}},
        ],
    )

    stream = main._generate_sse()
    first_payload = asyncio.run(anext(stream))
    second_payload = asyncio.run(anext(stream))
    asyncio.run(stream.aclose())

    assert json.loads(first_payload.removeprefix("data: ").strip()) == {
        "serviceName": "Agent",
        "event": {"type": "run_started", "runId": "run-1", "runLabel": "Agent"},
    }
    assert json.loads(second_payload.removeprefix("data: ").strip()) == {
        "serviceName": "Agent",
        "event": {
            "type": "node_added",
            "node": {"id": "span-1", "parentId": None, "label": "first", "subtitle": "Agent", "type": "agent", "whatDescription": "first"},
        },
    }
