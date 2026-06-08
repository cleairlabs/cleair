from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

import pytest
from opentelemetry.trace import StatusCode

from cleair import _core
from cleair._config import CleairConfig, DEFAULT_BASE_URL


@pytest.fixture(autouse=True)
def _reset_state(monkeypatch):
    monkeypatch.setattr(_core, "_config", None)
    monkeypatch.setattr(_core, "_provider", None)


def test_init_uses_explicit_config() -> None:
    _core.init(CleairConfig(service_name="svc", base_url="https://example.com", api_key="key"))

    assert _core._config == CleairConfig(service_name="svc", base_url="https://example.com", api_key="key")


def test_init_rejects_conflicting_config_when_provider_exists(monkeypatch) -> None:
    _core.init(enabled=False)
    monkeypatch.setattr(_core, "_provider", object())

    with pytest.raises(ValueError, match="already been called"):
        _core.init(service_name="other")


def test_provider_requires_api_key_when_enabled() -> None:
    _core.init(CleairConfig())

    with pytest.raises(ValueError, match="api_key is required"):
        _core.flush()


def test_flush_uses_provider(monkeypatch) -> None:
    force_flush = MagicMock()
    monkeypatch.setattr(_core, "_ensure_provider", lambda: MagicMock(force_flush=force_flush))

    _core.flush()

    force_flush.assert_called_once_with()


def test_provider_builds_processor_from_base_url(monkeypatch) -> None:
    fake_exporter = MagicMock(name="exporter")
    fake_batch_processor = MagicMock(name="batch_processor")
    fake_live_processor = MagicMock(name="live_processor")
    monkeypatch.setattr("cleair._core.OTLPSpanExporter", fake_exporter)
    monkeypatch.setattr("cleair._core.BatchSpanProcessor", fake_batch_processor)
    monkeypatch.setattr("cleair._core.CleairLiveSpanProcessor", fake_live_processor)

    _core.init(CleairConfig(service_name="svc", base_url=DEFAULT_BASE_URL, api_key="test-key"))
    _core._ensure_provider()

    fake_live_processor.assert_called_once_with(
        base_url=DEFAULT_BASE_URL,
        api_key="test-key",
        service_name="svc",
    )
    fake_exporter.assert_called_once_with(
        endpoint=f"{DEFAULT_BASE_URL}/v1/traces",
        headers={"Authorization": "Bearer test-key"},
    )
    fake_batch_processor.assert_called_once_with(fake_exporter.return_value, schedule_delay_millis=_core.OTLP_SCHEDULE_DELAY_MILLIS)


def test_provider_skips_live_processor_when_disabled(monkeypatch) -> None:
    fake_exporter = MagicMock(name="exporter")
    fake_batch_processor = MagicMock(name="batch_processor")
    fake_live_processor = MagicMock(name="live_processor")
    monkeypatch.setattr("cleair._core.OTLPSpanExporter", fake_exporter)
    monkeypatch.setattr("cleair._core.BatchSpanProcessor", fake_batch_processor)
    monkeypatch.setattr("cleair._core.CleairLiveSpanProcessor", fake_live_processor)

    _core.init(CleairConfig(service_name="svc", base_url=DEFAULT_BASE_URL, api_key="test-key", use_live=False))
    _core._ensure_provider()

    fake_live_processor.assert_not_called()
    fake_exporter.assert_called_once_with(
        endpoint=f"{DEFAULT_BASE_URL}/v1/traces",
        headers={"Authorization": "Bearer test-key"},
    )
    fake_batch_processor.assert_called_once_with(fake_exporter.return_value, schedule_delay_millis=_core.OTLP_SCHEDULE_DELAY_MILLIS)


def test_span_records_exception_and_reraises(monkeypatch) -> None:
    fake_span = MagicMock()
    fake_span.__enter__ = MagicMock(return_value=fake_span)
    fake_span.__exit__ = MagicMock(return_value=False)
    fake_tracer = MagicMock()
    fake_tracer.start_as_current_span.return_value = fake_span
    monkeypatch.setattr(_core, "_tracer", lambda: fake_tracer)
    monkeypatch.setattr(_core, "_ensure_provider", lambda: object())
    _core.init(cleair_api_key="key")

    with pytest.raises(RuntimeError, match="boom"):
        with _core.span("test") as span_handle:
            assert span_handle is fake_span
            raise RuntimeError("boom")

    fake_span.record_exception.assert_called_once()
    args = fake_span.set_status.call_args[0]
    assert args[0].status_code == StatusCode.ERROR


def test_trace_call_capture_output_adds_event(monkeypatch) -> None:
    class FakeSpan:
        def __init__(self) -> None:
            self.events: list[tuple[str, dict[str, object]]] = []
            self.attributes: dict[str, object] = {}

        def __enter__(self) -> "FakeSpan":
            return self

        def __exit__(self, _exc_type, _exc, _tb) -> bool:
            return False

        def set_attribute(self, name: str, value: object) -> None:
            self.attributes[name] = value

        def record_exception(self, _exception: Exception) -> None:
            return None

        def set_status(self, _status: object) -> None:
            return None

        def add_event(self, name: str, attributes: dict[str, object] | None = None) -> None:
            self.events.append((name, attributes or {}))

    class FakeTracer:
        def __init__(self, span: FakeSpan) -> None:
            self.span = span

        def start_as_current_span(self, _name: str, attributes=None) -> FakeSpan:
            return self.span

    span = FakeSpan()
    monkeypatch.setattr(_core, "_tracer", lambda: FakeTracer(span))
    monkeypatch.setattr(_core, "_ensure_provider", lambda: object())
    _core.init(cleair_api_key="key")

    def target() -> str:
        return "ok"

    result = _core.trace_call(target, capture_output=True)

    assert result == "ok"
    assert span.events == [("function.output", {"value": "ok"})]


def test_observe_async_wraps_coroutine(monkeypatch) -> None:
    fake_span = MagicMock()
    fake_span.__enter__ = MagicMock(return_value=fake_span)
    fake_span.__exit__ = MagicMock(return_value=False)
    fake_tracer = MagicMock()
    fake_tracer.start_as_current_span.return_value = fake_span
    monkeypatch.setattr(_core, "_tracer", lambda: fake_tracer)
    monkeypatch.setattr(_core, "_ensure_provider", lambda: object())
    _core.init(cleair_api_key="key")

    @_core.observe
    async def greet(name: str) -> str:
        return f"hi {name}"

    assert greet.__name__ == "greet"
    result = asyncio.run(greet("world"))
    assert result == "hi world"


def test_start_run_creates_new_root_and_propagates_metadata(monkeypatch) -> None:
    entered_spans: list[tuple[str, object, object]] = []

    class FakeSpan:
        def __enter__(self):
            return self

        def __exit__(self, _exc_type, _exc, _tb) -> bool:
            return False

        def record_exception(self, _exception: Exception) -> None:
            return None

        def set_status(self, _status: object) -> None:
            return None

        def set_attribute(self, _name: str, _value: object) -> None:
            return None

    class FakeTracer:
        def start_as_current_span(self, name: str, context=None, attributes=None) -> FakeSpan:
            entered_spans.append((name, context, attributes))
            return FakeSpan()

    monkeypatch.setattr(_core, "_tracer", lambda: FakeTracer())
    monkeypatch.setattr(_core, "_ensure_provider", lambda: object())
    _core.init(cleair_api_key="key")

    with _core.start_run("agent.run", metadata={"agent.id": "agent-1", "batch.id": "batch-1"}):
        with _core.span("child"):
            pass

    assert entered_spans[0][0] == "agent.run"
    assert entered_spans[0][1] is not None
    assert entered_spans[0][2] == {"cleair.type": "trace", "agent.id": "agent-1", "batch.id": "batch-1"}
    assert entered_spans[1] == ("child", None, {"agent.id": "agent-1", "batch.id": "batch-1"})


def test_start_run_accepts_agent_and_batch_params(monkeypatch) -> None:
    entered_spans: list[tuple[str, object, object]] = []

    class FakeSpan:
        def __enter__(self):
            return self

        def __exit__(self, _exc_type, _exc, _tb) -> bool:
            return False

        def record_exception(self, _exception: Exception) -> None:
            return None

        def set_status(self, _status: object) -> None:
            return None

        def set_attribute(self, _name: str, _value: object) -> None:
            return None

    class FakeTracer:
        def start_as_current_span(self, name: str, context=None, attributes=None) -> FakeSpan:
            entered_spans.append((name, context, attributes))
            return FakeSpan()

    monkeypatch.setattr(_core, "_tracer", lambda: FakeTracer())
    monkeypatch.setattr(_core, "_ensure_provider", lambda: object())
    _core.init(cleair_api_key="key")

    with _core.start_run("agent.run", agent_id="agent-1", batch_id="batch-1"):
        with _core.span("child"):
            pass

    assert entered_spans[0][2] == {"cleair.type": "trace", "agent.id": "agent-1", "batch.id": "batch-1"}
    assert entered_spans[1] == ("child", None, {"agent.id": "agent-1", "batch.id": "batch-1"})
