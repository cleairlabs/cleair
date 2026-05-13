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
    fake_processor = MagicMock()
    monkeypatch.setattr("cleair._core.CleairHttpSpanProcessor", fake_processor)

    _core.init(CleairConfig(service_name="svc", base_url=DEFAULT_BASE_URL, api_key="test-key"))
    _core._ensure_provider()

    fake_processor.assert_called_once_with(base_url=DEFAULT_BASE_URL, api_key="test-key", service_name="svc")


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
