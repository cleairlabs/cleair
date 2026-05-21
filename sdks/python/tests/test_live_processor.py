from __future__ import annotations

from types import SimpleNamespace

from cleair.exporters.live_http import CleairLiveSpanProcessor


def test_live_processor_emits_root_span_start(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_post(payload: dict) -> None:
        captured["payload"] = payload

    processor = CleairLiveSpanProcessor(base_url="http://localhost:8000", api_key="key", service_name="svc")
    monkeypatch.setattr(processor, "_post", fake_post)

    span = SimpleNamespace(
        context=SimpleNamespace(is_valid=True, trace_id=0x11111111111111111111111111111111, span_id=0x2222222222222222),
        parent=None,
        attributes={"agent.id": "agent-1", "batch.id": "batch-1", "cleair.type": "agent"},
        name="root",
    )
    processor.on_start(span)

    assert captured["payload"] == {
        "runId": "11111111111111111111111111111111",
        "serviceName": "svc",
        "metadata": {"agent.id": "agent-1", "batch.id": "batch-1"},
        "span": {
            "id": "2222222222222222",
            "parentId": None,
            "label": "root",
            "type": "agent",
        },
    }
