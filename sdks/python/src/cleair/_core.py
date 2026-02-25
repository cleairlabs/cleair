from __future__ import annotations

import functools
import inspect
import threading
import time
from contextlib import contextmanager

from opentelemetry import trace as otel_trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SimpleSpanProcessor
from opentelemetry.trace import Status, StatusCode

from cleair._config import CleairConfig
from cleair.adapters._base import Adapter
from cleair.adapters._registry import add_adapter, instrument

_initialized = False
_init_lock = threading.Lock()


def init(config: CleairConfig | None = None) -> None:
    global _initialized
    if _initialized: return # fast path (double-check locking pattern)
    with _init_lock:
        if _initialized: return # re-check

        resolved_config = config or CleairConfig.from_env()
        resource = Resource.create({"service.name": resolved_config.service_name})
        provider = TracerProvider(resource=resource)
        if resolved_config.exporter == "console":
            from opentelemetry.sdk.trace.export import ConsoleSpanExporter
            exporter = ConsoleSpanExporter()
            provider.add_span_processor(BatchSpanProcessor(exporter))
        elif resolved_config.exporter == "terminal":
            from cleair.exporters import CleairConsoleSpanExporter
            exporter = CleairConsoleSpanExporter(stream=resolved_config.terminal_stream)
            provider.add_span_processor(SimpleSpanProcessor(exporter))
        elif resolved_config.exporter == "otlp_http":
            from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
            exporter = OTLPSpanExporter(endpoint=resolved_config.otlp_http_endpoint)
            provider.add_span_processor(BatchSpanProcessor(exporter))
        elif resolved_config.exporter == "cleair_http":
            from cleair.exporters.cleair_http import CleairHttpSpanProcessor
            provider.add_span_processor(CleairHttpSpanProcessor(
                endpoint=resolved_config.cleair_http_endpoint,
                service_name=resolved_config.service_name,
            ))
        else:
            raise ValueError(f"Unknown exporter: {resolved_config.exporter!r} (use 'otlp_http', 'cleair_http', 'console', or 'terminal')")

        otel_trace.set_tracer_provider(provider)
        _initialized = True


def _tracer():
    init()
    return otel_trace.get_tracer("cleair")


@contextmanager
def span(name: str, *, attributes: dict[str, str | int | float | bool] | None = None):
    tracer = _tracer()
    with tracer.start_as_current_span(name, attributes=attributes) as span_handle:
        try:
            yield span_handle
        except Exception as exception:
            span_handle.record_exception(exception)
            span_handle.set_status(Status(StatusCode.ERROR))
            raise


def _coerce_attribute_value(value: object) -> str | int | float | bool:
    if isinstance(value, (str, int, float, bool)):
        return value
    return repr(value)


def trace_call(function, /,
               *args,
               span_name: str | None = None,
               attributes: dict[str, str | int | float | bool] | None = None,
               capture_output: bool = False,
               **kwargs,
):
    name = span_name or getattr(function, "__qualname__", getattr(function, "__name__", "call"))
    with span(name, attributes=attributes) as sh:
        start = time.perf_counter()
        try:
            result = function(*args, **kwargs)
            if capture_output:
                sh.add_event("function.output", {"value": _coerce_attribute_value(result)})
            return result
        finally:
            sh.set_attribute("duration_ms", (time.perf_counter() - start) * 1000.0)


async def _trace_call_async(function, /, 
                            *args,
                            span_name: str | None = None, 
                            attributes: dict[str, str | int | float | bool] | None = None, 
                            capture_output: bool = False,
                            **kwargs,
):
    name = span_name or getattr(function, "__qualname__", getattr(function, "__name__", "call"))
    with span(name, attributes=attributes) as sh:
        start = time.perf_counter()
        try:
            result = await function(*args, **kwargs)
            if capture_output:
                sh.add_event("function.output", {"value": _coerce_attribute_value(result)})
            return result
        finally:
            sh.set_attribute("duration_ms", (time.perf_counter() - start) * 1000.0)


def trace(function=None, /, *,
          span_name: str | None = None,
          attributes: dict[str, str | int | float | bool] | None = None,
          capture_output: bool = False,
):
    def decorator(target_function):
        if inspect.iscoroutinefunction(target_function):
            @functools.wraps(target_function)
            async def wrapped(*args, **kwargs):
                return await _trace_call_async(target_function, *args, span_name=span_name, attributes=attributes, 
                                               capture_output=capture_output, **kwargs)
            return wrapped

        @functools.wraps(target_function)
        def wrapped(*args, **kwargs):
            return trace_call(target_function, *args, span_name=span_name, attributes=attributes, capture_output=capture_output, **kwargs)
        return wrapped
    if function is None: return decorator
    return decorator(function)


def _merge_observe_attributes(*, attributes: dict[str, str | int | float | bool] | None, 
                              metadata: dict[str, str | int | float | bool] | None, 
                              session_id: str | None,
) -> dict[str, str | int | float | bool] | None:
    resolved_attributes: dict[str, str | int | float | bool] = {}
    if metadata: resolved_attributes.update(metadata)
    if attributes: resolved_attributes.update(attributes)
    if session_id is not None: resolved_attributes["session.id"] = session_id
    return resolved_attributes or None


def observe(function=None, /, *,
            span_name: str | None = None,
            name: str | None = None,
            attributes: dict[str, str | int | float | bool] | None = None,
            metadata: dict[str, str | int | float | bool] | None = None,
            session_id: str | None = None,
            capture_output: bool = False,
):
    resolved_span_name = span_name or name
    resolved_attributes = _merge_observe_attributes(attributes=attributes, metadata=metadata, session_id=session_id)
    if function is None:
        return trace(span_name=resolved_span_name, attributes=resolved_attributes, capture_output=capture_output)
    return trace(function, span_name=resolved_span_name, attributes=resolved_attributes, capture_output=capture_output)
