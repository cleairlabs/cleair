from __future__ import annotations

import asyncio
import json

from fastapi.testclient import TestClient
from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import ExportTraceServiceRequest
import pytest

from cleair_backend import main
from cleair_backend.auth import AuthConfig, SESSION_COOKIE_NAME, _sign_value
from cleair_backend.store import TraceStore


def otlp_payload(trace_id: str, service_name: str, span_id: str, label: str, *, metadata: dict[str, str] | None = None, parent_span_id: str | None = None) -> dict:
    span_attributes = [] if metadata is None else [
        {"key": key, "value": {"stringValue": value}}
        for key, value in metadata.items()
    ]
    span_attributes.append({"key": "cleair.type", "value": {"stringValue": "agent"}})
    span_payload = {
        "traceId": trace_id,
        "spanId": span_id,
        "name": label,
        "startTimeUnixNano": "1000",
        "endTimeUnixNano": "2001000",
        "attributes": span_attributes,
    }
    if parent_span_id is not None:
        span_payload["parentSpanId"] = parent_span_id
    return {
        "resourceSpans": [
            {
                "resource": {"attributes": [{"key": "service.name", "value": {"stringValue": service_name}}]},
                "scopeSpans": [
                    {
                        "spans": [
                            span_payload
                        ]
                    }
                ],
            }
        ]
    }


@pytest.fixture(autouse=True)
def reset_app_state() -> None:
    original_auth_config = main.auth_config
    original_store = main.trace_store
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
    main.trace_store = TraceStore()
    try:
        yield
    finally:
        main.auth_config = original_auth_config
        main.trace_store = original_store


def test_protected_routes_require_authenticated_session() -> None:
    client = TestClient(main.app)

    response = client.get("/agents")

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required"}


def test_valid_code_sets_session_cookie_and_unlocks_routes() -> None:
    client = TestClient(main.app)

    verify_response = client.post("/auth/verify", json={"code": "123456"})
    api_key_response = client.post("/api-key")
    agents_response = client.get("/agents")

    assert verify_response.status_code == 200
    assert verify_response.json() == {"authenticated": True}
    assert api_key_response.status_code == 201
    assert len(api_key_response.json()["apiKey"]) == 32
    assert agents_response.status_code == 200
    assert agents_response.json() == []


def test_api_key_creation_is_idempotent() -> None:
    client = TestClient(main.app)

    client.post("/auth/verify", json={"code": "123456"})
    first_response = client.post("/api-key")
    second_response = client.post("/api-key")

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


def test_trace_ingest_accepts_api_key_without_session() -> None:
    client = TestClient(main.app)
    api_key = main.trace_store.ensure_api_key()

    response = client.post(
        "/v1/traces",
        headers={"Authorization": f"Bearer {api_key}"},
        json=otlp_payload("run-1", "Agent", "span-1", "first"),
    )

    assert response.status_code == 204


@pytest.mark.parametrize("authorization", [None, "invalid", "Basic key", "Bearer unknown"])
def test_trace_ingest_rejects_invalid_bearer_token(authorization: str | None) -> None:
    client = TestClient(main.app)
    headers = {} if authorization is None else {"Authorization": authorization}

    response = client.post("/v1/traces", headers=headers, json=otlp_payload("run-1", "Agent", "span-1", "first"))

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid bearer token"}
    assert response.headers["WWW-Authenticate"] == "Bearer"


def test_live_ingest_emits_running_node_before_otlp_completion() -> None:
    client = TestClient(main.app)
    client.post("/auth/verify", json={"code": "123456"})
    api_key = client.post("/api-key").json()["apiKey"]

    live_response = client.post(
        "/v1/live",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "runId": "run-1",
            "serviceName": "Agent",
            "metadata": {"agent.id": "agent-1"},
            "span": {"id": "span-1", "parentId": None, "label": "first", "type": "agent"},
        },
    )
    otlp_response = client.post(
        "/v1/traces",
        headers={"Authorization": f"Bearer {api_key}"},
        json=otlp_payload("run-1", "Agent", "span-1", "first", metadata={"agent.id": "agent-1"}),
    )
    agents_response = client.get("/agents")

    assert live_response.status_code == 204
    assert otlp_response.status_code == 204
    assert agents_response.json() == [
        {
            "serviceName": "Agent",
            "runId": "run-1",
            "metadata": {"agent.id": "agent-1"},
            "events": [
                {"type": "run_started", "runId": "run-1", "runLabel": "Agent", "metadata": {"agent.id": "agent-1"}},
                {"type": "node_added", "node": {"id": "span-1", "parentId": None, "label": "first", "subtitle": "Agent", "type": "agent"}},
                {"type": "node_status_changed", "nodeId": "span-1", "status": "running"},
                {"type": "node_added", "node": {"id": "span-1", "parentId": None, "label": "first", "subtitle": "Agent", "type": "agent"}},
                {"type": "node_status_changed", "nodeId": "span-1", "status": "running"},
                {"type": "node_status_changed", "nodeId": "span-1", "status": "done"},
                {"type": "node_finished", "nodeId": "span-1", "durationMs": 2},
                {"type": "run_completed"},
            ],
        }
    ]


def test_trace_ingest_accepts_otlp_protobuf() -> None:
    client = TestClient(main.app)
    client.post("/auth/verify", json={"code": "123456"})
    api_key = main.trace_store.ensure_api_key()
    request_message = ExportTraceServiceRequest()
    resource_span = request_message.resource_spans.add()
    resource_attribute = resource_span.resource.attributes.add()
    resource_attribute.key = "service.name"
    resource_attribute.value.string_value = "Agent"
    scope_span = resource_span.scope_spans.add()
    span = scope_span.spans.add()
    span.trace_id = bytes.fromhex("11111111111111111111111111111111")
    span.span_id = bytes.fromhex("2222222222222222")
    span.name = "first"
    span.start_time_unix_nano = 1000
    span.end_time_unix_nano = 2_001_000
    span_attribute = span.attributes.add()
    span_attribute.key = "cleair.type"
    span_attribute.value.string_value = "agent"

    response = client.post(
        "/v1/traces",
        headers={"Content-Type": "application/x-protobuf", "Authorization": f"Bearer {api_key}"},
        content=request_message.SerializeToString(),
    )
    agents_response = client.get("/agents")

    assert response.status_code == 204
    assert agents_response.json()[0]["runId"] == "11111111111111111111111111111111"


def test_agents_keep_multiple_runs_for_same_service_name() -> None:
    client = TestClient(main.app)
    client.post("/auth/verify", json={"code": "123456"})
    api_key = client.post("/api-key").json()["apiKey"]

    first_response = client.post(
        "/v1/traces",
        headers={"Authorization": f"Bearer {api_key}"},
        json=otlp_payload(
            "run-1",
            "Agent",
            "span-1",
            "first",
            metadata={"agent.id": "agent-1", "batch.id": "batch-1"},
        ),
    )
    second_response = client.post(
        "/v1/traces",
        headers={"Authorization": f"Bearer {api_key}"},
        json=otlp_payload(
            "run-2",
            "Agent",
            "span-2",
            "second",
            metadata={"agent.id": "agent-2", "batch.id": "batch-1"},
        ),
    )
    agents_response = client.get("/agents")

    assert first_response.status_code == 204
    assert second_response.status_code == 204
    assert agents_response.status_code == 200
    assert agents_response.json() == [
        {
            "serviceName": "Agent",
            "runId": "run-2",
            "metadata": {"agent.id": "agent-2", "batch.id": "batch-1"},
            "events": [
                {"type": "run_started", "runId": "run-2", "runLabel": "Agent", "metadata": {"agent.id": "agent-2", "batch.id": "batch-1"}},
                {"type": "node_added", "node": {"id": "span-2", "parentId": None, "label": "second", "subtitle": "Agent", "type": "agent"}},
                {"type": "node_status_changed", "nodeId": "span-2", "status": "running"},
                {"type": "node_status_changed", "nodeId": "span-2", "status": "done"},
                {"type": "node_finished", "nodeId": "span-2", "durationMs": 2},
                {"type": "run_completed"},
            ],
        },
        {
            "serviceName": "Agent",
            "runId": "run-1",
            "metadata": {"agent.id": "agent-1", "batch.id": "batch-1"},
            "events": [
                {"type": "run_started", "runId": "run-1", "runLabel": "Agent", "metadata": {"agent.id": "agent-1", "batch.id": "batch-1"}},
                {"type": "node_added", "node": {"id": "span-1", "parentId": None, "label": "first", "subtitle": "Agent", "type": "agent"}},
                {"type": "node_status_changed", "nodeId": "span-1", "status": "running"},
                {"type": "node_status_changed", "nodeId": "span-1", "status": "done"},
                {"type": "node_finished", "nodeId": "span-1", "durationMs": 2},
                {"type": "run_completed"},
            ],
        }
    ]


def test_stream_replays_existing_agent_events() -> None:
    main.trace_store.start_run("Agent", "run-1", metadata={"agent.id": "agent-1"})
    main.trace_store.append_events(
        "run-1",
        [
            {"type": "run_started", "runId": "run-1", "runLabel": "Agent", "metadata": {"agent.id": "agent-1"}},
            {"type": "node_added", "node": {"id": "span-1", "parentId": None, "label": "first", "subtitle": "Agent", "type": "agent"}},
        ],
    )

    stream = main._generate_sse()
    first_payload = asyncio.run(anext(stream))
    second_payload = asyncio.run(anext(stream))
    asyncio.run(stream.aclose())

    assert json.loads(first_payload.removeprefix("data: ").strip()) == {
        "runId": "run-1",
        "serviceName": "Agent",
        "event": {"type": "run_started", "runId": "run-1", "runLabel": "Agent", "metadata": {"agent.id": "agent-1"}},
    }
    assert json.loads(second_payload.removeprefix("data: ").strip()) == {
        "runId": "run-1",
        "serviceName": "Agent",
        "event": {
            "type": "node_added",
            "node": {"id": "span-1", "parentId": None, "label": "first", "subtitle": "Agent", "type": "agent"},
        },
    }


def test_delete_agent_removes_run_from_store() -> None:
    client = TestClient(main.app)
    client.post("/auth/verify", json={"code": "123456"})
    api_key = client.post("/api-key").json()["apiKey"]
    client.post(
        "/v1/traces",
        headers={"Authorization": f"Bearer {api_key}"},
        json=otlp_payload("run-1", "Agent", "span-1", "first"),
    )

    delete_response = client.delete("/agents/run-1")
    agents_response = client.get("/agents")

    assert delete_response.status_code == 204
    assert agents_response.json() == []


def test_delete_agent_returns_not_found_for_unknown_run() -> None:
    client = TestClient(main.app)
    client.post("/auth/verify", json={"code": "123456"})

    response = client.delete("/agents/run-unknown")

    assert response.status_code == 404
    assert response.json() == {"detail": "Unknown runId"}
