from __future__ import annotations

from types import SimpleNamespace

from opentelemetry.trace import StatusCode

from cleair.exporters.cleair_http import CleairHttpSpanProcessor


def test_on_start_emits_run_started_for_root_span(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_post(run_id: str, events: list[dict]) -> None:
        captured["run_id"] = run_id
        captured["events"] = events

    processor = CleairHttpSpanProcessor(base_url="http://localhost:8000", api_key="key", service_name="svc")
    monkeypatch.setattr(processor, "_post", fake_post)

    span = SimpleNamespace(
        context=SimpleNamespace(is_valid=True, trace_id=0x11111111111111111111111111111111, span_id=0x2222222222222222),
        parent=None,
        attributes={"agent.id": "agent-1", "batch.id": "batch-1"},
        name="root",
    )
    processor.on_start(span)

    events = captured["events"]
    assert captured["run_id"] == "11111111111111111111111111111111"
    assert events[0] == {
        "type": "run_started",
        "runId": captured["run_id"],
        "runLabel": "svc",
        "metadata": {"agent.id": "agent-1", "batch.id": "batch-1"},
    }
    assert events[1]["type"] == "node_added"
    assert events[2] == {"type": "node_status_changed", "nodeId": "2222222222222222", "status": "running"}


def test_on_end_uses_status_code_enum_and_emits_run_completed(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_post(run_id: str, events: list[dict]) -> None:
        captured["run_id"] = run_id
        captured["events"] = events

    processor = CleairHttpSpanProcessor(base_url="http://localhost:8000", api_key="key", service_name="svc")
    monkeypatch.setattr(processor, "_post", fake_post)

    span = SimpleNamespace(
        context=SimpleNamespace(is_valid=True, trace_id=0xAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA, span_id=0xBBBBBBBBBBBBBBBB),
        parent=None,
        status=SimpleNamespace(status_code=StatusCode.ERROR),
        start_time=1_000_000,
        end_time=5_500_000,
        events=[SimpleNamespace(name="function.output", attributes={"value": "done"})],
    )
    processor.on_end(span)

    events = captured["events"]
    assert captured["run_id"] == "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
    assert events[0] == {"type": "node_status_changed", "nodeId": "bbbbbbbbbbbbbbbb", "status": "error"}
    assert events[1] == {"type": "node_finished", "nodeId": "bbbbbbbbbbbbbbbb", "durationMs": 4, "output": "done"}
    assert events[2] == {"type": "run_completed"}
