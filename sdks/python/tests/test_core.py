from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

import pytest
from opentelemetry.trace import StatusCode

from cleair import _core
from cleair._config import CleairConfig, DEFAULT_CLEAIR_HTTP_ENDPOINT


@pytest.fixture(autouse=True)
def _reset_init(monkeypatch):
    monkeypatch.setattr(_core, "_initialized", False)


# --- init() ---


def test_init_unknown_exporter_raises():
    config = CleairConfig(exporter="nope")
    with pytest.raises(ValueError, match="nope"):
        _core.init(config)


def test_init_console_exporter():
    _core.init(CleairConfig(exporter="console"))
    assert _core._initialized is True


def test_init_default_cleair_http_uses_api_key(monkeypatch):
    fake_processor = MagicMock()
    monkeypatch.setattr("cleair.exporters.cleair_http.CleairHttpSpanProcessor", fake_processor)
    _core.init(cleair_api_key="test-key")
    fake_processor.assert_called_once_with(endpoint=DEFAULT_CLEAIR_HTTP_ENDPOINT, service_name="cleair-app", api_key="test-key",)
    assert _core._initialized is True


def test_init_default_cleair_http_requires_api_key():
    with pytest.raises(ValueError, match="cleair_api_key is required"):
        _core.init()


def test_init_prefers_explicit_exporter_over_api_key(monkeypatch):
    fake_processor = MagicMock()
    monkeypatch.setattr("cleair.exporters.cleair_http.CleairHttpSpanProcessor", fake_processor)
    _core.init(exporter="console", cleair_api_key="test-key")
    fake_processor.assert_not_called()
    assert _core._initialized is True


def test_init_prefers_config_exporter_over_api_key(monkeypatch):
    fake_processor = MagicMock()
    monkeypatch.setattr("cleair.exporters.cleair_http.CleairHttpSpanProcessor", fake_processor)
    _core.init(CleairConfig(exporter="console"), cleair_api_key="test-key")
    fake_processor.assert_not_called()
    assert _core._initialized is True


def test_init_only_runs_once():
    _core.init(CleairConfig(exporter="console"))
    # second call with a different exporter is ignored
    _core.init(cleair_api_key="test-key")
    assert _core._initialized is True


# --- span() error path ---

def test_span_records_exception_and_reraises(monkeypatch):
    fake_span = MagicMock()
    fake_span.__enter__ = MagicMock(return_value=fake_span)
    fake_span.__exit__ = MagicMock(return_value=False)
    fake_tracer = MagicMock()
    fake_tracer.start_as_current_span.return_value = fake_span
    monkeypatch.setattr(_core, "_tracer", lambda: fake_tracer)
    with pytest.raises(RuntimeError, match="boom"):
        with _core.span("test") as sh:
            raise RuntimeError("boom")
    sh.record_exception.assert_called_once()
    args = sh.set_status.call_args[0]
    assert args[0].status_code == StatusCode.ERROR


# --- _format_attribute_value ---


def test_coerce_passes_primitives_through():
    assert _core._format_attribute_value("hello") == "hello"
    assert _core._format_attribute_value(42) == 42
    assert _core._format_attribute_value(3.14) == 3.14
    assert _core._format_attribute_value(True) is True


def test_coerce_repr_for_non_primitives():
    assert _core._format_attribute_value([1, 2]) == "[1, 2]"
    assert _core._format_attribute_value({"a": 1}) == "{'a': 1}"


# --- observe() async path ---


def test_observe_async_wraps_coroutine(monkeypatch):
    fake_span = MagicMock()
    fake_span.__enter__ = MagicMock(return_value=fake_span)
    fake_span.__exit__ = MagicMock(return_value=False)

    fake_tracer = MagicMock()
    fake_tracer.start_as_current_span.return_value = fake_span
    monkeypatch.setattr(_core, "_tracer", lambda: fake_tracer)

    @_core.observe
    async def greet(name: str) -> str: return f"hi {name}"

    assert greet.__name__ == "greet"
    result = asyncio.run(greet("world"))
    assert result == "hi world"


def test_observe_async_with_kwargs(monkeypatch):
    fake_span = MagicMock()
    fake_span.__enter__ = MagicMock(return_value=fake_span)
    fake_span.__exit__ = MagicMock(return_value=False)
    fake_tracer = MagicMock()
    fake_tracer.start_as_current_span.return_value = fake_span
    monkeypatch.setattr(_core, "_tracer", lambda: fake_tracer)

    @_core.observe(name="custom", capture_output=True)
    async def compute() -> int: return 99

    result = asyncio.run(compute())
    assert result == 99
    fake_tracer.start_as_current_span.assert_called_with("custom", attributes=None)
