from __future__ import annotations

import inspect
import time
from contextlib import contextmanager
from dataclasses import dataclass

from opentelemetry import trace as otel_trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from cleair._config import CleairConfig
from cleair.adapters._base import Adapter
from cleair.adapters._registry import add_adapter, instrument

_initialized = False


def init(config: CleairConfig | None = None) -> None:
    global _initialized
    if _initialized: return

    resolved_config = config or CleairConfig.from_env()
    resource = Resource.create({"service.name": resolved_config.service_name})
    provider = TracerProvider(resource=resource)

    if resolved_config.exporter == "console":
        from opentelemetry.sdk.trace.export import ConsoleSpanExporter
        exporter = ConsoleSpanExporter()
        provider.add_span_processor(BatchSpanProcessor(exporter))
    elif resolved_config.exporter == "otlp_http":
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        exporter = OTLPSpanExporter(endpoint=resolved_config.otlp_http_endpoint)
        provider.add_span_processor(BatchSpanProcessor(exporter))
    else:
        raise ValueError(f"Unknown exporter: {resolved_config.exporter!r} (use 'otlp_http' or 'console')")

    otel_trace.set_tracer_provider(provider)
    _initialized = True


def _tracer():
    init()
    return otel_trace.get_tracer("cleair")


@dataclass(frozen=True)
class SpanSpec:
    name: str
    attributes: dict[str, str | int | float | bool] | None = None


@contextmanager
def span(name: str, *, attributes: dict[str, str | int | float | bool] | None = None):
    tracer = _tracer()
    with tracer.start_as_current_span(name) as span_handle:
        if attributes:
            for attribute_name, attribute_value in attributes.items():
                span_handle.set_attribute(attribute_name, attribute_value)
        try:
            yield span_handle
        except Exception as exception:
            span_handle.record_exception(exception)
            from opentelemetry.trace import Status, StatusCode
            span_handle.set_status(Status(StatusCode.ERROR))
            raise


def trace_call(function, /, *args, span_name: str | None = None, attributes: dict[str, str | int | float | bool] | None = None, **kwargs):
    resolved_span_name = span_name or getattr(function, "__qualname__", getattr(function, "__name__", "call"))
    tracer = _tracer()

    with tracer.start_as_current_span(resolved_span_name) as span_handle:
        if attributes:
            for attribute_name, attribute_value in attributes.items():
                span_handle.set_attribute(attribute_name, attribute_value)

        start_time = time.perf_counter()
        try:
            result_value = function(*args, **kwargs)
        except Exception as exception:
            span_handle.record_exception(exception)
            from opentelemetry.trace import Status, StatusCode
            span_handle.set_status(Status(StatusCode.ERROR))
            raise
        finally:
            span_handle.set_attribute("duration_ms", (time.perf_counter() - start_time) * 1000.0)

    return result_value


async def _trace_call_async(function, /, *args, span_name: str | None = None, attributes: dict[str, str | int | float | bool] | None = None, **kwargs):
    resolved_span_name = span_name or getattr(function, "__qualname__", getattr(function, "__name__", "call"))
    tracer = _tracer()

    with tracer.start_as_current_span(resolved_span_name) as span_handle:
        if attributes:
            for attribute_name, attribute_value in attributes.items():
                span_handle.set_attribute(attribute_name, attribute_value)

        start_time = time.perf_counter()
        try:
            return await function(*args, **kwargs)
        except Exception as exception:
            span_handle.record_exception(exception)
            from opentelemetry.trace import Status, StatusCode
            span_handle.set_status(Status(StatusCode.ERROR))
            raise
        finally:
            span_handle.set_attribute("duration_ms", (time.perf_counter() - start_time) * 1000.0)


def trace(function=None, /, *, span_name: str | None = None, attributes: dict[str, str | int | float | bool] | None = None):
    def decorator(target_function):
        if inspect.iscoroutinefunction(target_function):
            async def wrapped(*args, **kwargs):
                return await _trace_call_async(
                    target_function,
                    *args,
                    span_name=span_name,
                    attributes=attributes,
                    **kwargs,
                )
            return wrapped

        def wrapped(*args, **kwargs):
            return trace_call(
                target_function,
                *args,
                span_name=span_name,
                attributes=attributes,
                **kwargs,
            )

        return wrapped

    if function is None:
        return decorator
    return decorator(function)


def _merge_observe_attributes(
    *,
    attributes: dict[str, str | int | float | bool] | None,
    metadata: dict[str, str | int | float | bool] | None,
    session_id: str | None,
) -> dict[str, str | int | float | bool] | None:
    resolved_attributes: dict[str, str | int | float | bool] = {}
    if metadata:
        resolved_attributes.update(metadata)
    if attributes:
        resolved_attributes.update(attributes)
    if session_id is not None:
        resolved_attributes["session.id"] = session_id
    return resolved_attributes or None


def observe(
    function=None,
    /,
    *,
    span_name: str | None = None,
    name: str | None = None,
    attributes: dict[str, str | int | float | bool] | None = None,
    metadata: dict[str, str | int | float | bool] | None = None,
    session_id: str | None = None,
):
    resolved_span_name = span_name or name
    resolved_attributes = _merge_observe_attributes(
        attributes=attributes,
        metadata=metadata,
        session_id=session_id,
    )

    if function is None:
        return trace(span_name=resolved_span_name, attributes=resolved_attributes)
    return trace(function, span_name=resolved_span_name, attributes=resolved_attributes)


def trace_expr(expression_thunk, /, *, span_name: str = "expression", attributes: dict[str, str | int | float | bool] | None = None):
    return trace_call(expression_thunk, span_name=span_name, attributes=attributes)
