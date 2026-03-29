from __future__ import annotations

import functools
import inspect
import threading
import time
from contextlib import contextmanager

from opentelemetry import trace as otel_trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import Status, StatusCode

from cleair._config import CleairConfig
from cleair.adapters._base import Adapter
from cleair.adapters._registry import add_adapter, instrument

_initialized = False
_init_lock = threading.Lock()


def _resolve_config(config: CleairConfig | None = None,
                    *,
                    service_name: str | None = None,
                    exporter: str | None = None,
                    cleair_http_endpoint: str | None = None,
                    cleair_api_key: str | None = None,) -> CleairConfig:
    base_config = config or CleairConfig.from_env()
    return CleairConfig(
        service_name=base_config.service_name if service_name is None else service_name,
        exporter=base_config.exporter if exporter is None else exporter,
        cleair_http_endpoint=base_config.cleair_http_endpoint if cleair_http_endpoint is None else cleair_http_endpoint,
        cleair_api_key=base_config.cleair_api_key if cleair_api_key is None else cleair_api_key,
    )


def _build_span_processor(config: CleairConfig):
    if config.exporter == "console":
        from opentelemetry.sdk.trace.export import ConsoleSpanExporter
        return BatchSpanProcessor(ConsoleSpanExporter())

    if config.exporter == "cleair_http":
        if not config.cleair_api_key:
            raise ValueError(
                "cleair_api_key is required when using exporter='cleair_http'.\n"
                "Create a pane in the cleair UI and pass its key:\n"
                "  CleairConfig(exporter='cleair_http', cleair_api_key='<key>')\n"
                "or pass cleair_api_key='<key>' to cleair.init(...).")
        from cleair.exporters.cleair_http import CleairHttpSpanProcessor
        return CleairHttpSpanProcessor(endpoint=config.cleair_http_endpoint, service_name=config.service_name, api_key=config.cleair_api_key)
    raise ValueError(f"Unknown exporter: {config.exporter!r} (use 'cleair_http' or 'console')")


def init(config: CleairConfig | None = None, 
         *,
         service_name: str | None = None,
         exporter: str | None = None,
         cleair_http_endpoint: str | None = None,
         cleair_api_key: str | None = None,) -> None:
    global _initialized
    if _initialized: return # fast path (double-check locking pattern)
    with _init_lock:
        if _initialized: return # re-check
        resolved_config = _resolve_config(config, service_name=service_name, exporter=exporter, cleair_http_endpoint=cleair_http_endpoint,
                                          cleair_api_key=cleair_api_key)
        resource = Resource.create({"service.name": resolved_config.service_name})
        provider = TracerProvider(resource=resource)
        provider.add_span_processor(_build_span_processor(resolved_config))
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


def _format_attribute_value(value: object) -> str | int | float | bool:
    if isinstance(value, (str, int, float, bool)):
        return value
    return repr(value)


def trace_call(function, 
               /,
               *args,
               span_name: str | None = None,
               attributes: dict[str, str | int | float | bool] | None = None,
               capture_output: bool = False,
               **kwargs,):
    name = span_name or getattr(function, "__qualname__", getattr(function, "__name__", "call"))
    with span(name, attributes=attributes) as span_handle:
        start = time.perf_counter()
        try:
            result = function(*args, **kwargs)
            if capture_output:
                span_handle.add_event("function.output", {"value": _format_attribute_value(result)})
            return result
        finally:
            span_handle.set_attribute("duration_ms", (time.perf_counter() - start) * 1000.0)


async def _trace_call_async(function, 
                            /, 
                            *args,
                            span_name: str | None = None, 
                            attributes: dict[str, str | int | float | bool] | None = None, 
                            capture_output: bool = False,
                            **kwargs,):
    name = span_name or getattr(function, "__qualname__", getattr(function, "__name__", "call"))
    with span(name, attributes=attributes) as span_handle:
        start = time.perf_counter()
        try:
            result = await function(*args, **kwargs)
            if capture_output:
                span_handle.add_event("function.output", {"value": _format_attribute_value(result)})
            return result
        finally:
            span_handle.set_attribute("duration_ms", (time.perf_counter() - start) * 1000.0)


def _wrap_observed_function(function,
                            /,
                            *,
                            span_name: str | None = None,
                            attributes: dict[str, str | int | float | bool] | None = None,
                            capture_output: bool = False,):
    if inspect.iscoroutinefunction(function):
        @functools.wraps(function)
        async def wrapped_async(*args, **kwargs):
            return await _trace_call_async(function, *args, span_name=span_name, attributes=attributes, capture_output=capture_output, **kwargs)
        return wrapped_async

    @functools.wraps(function)
    def wrapped_sync(*args, **kwargs):
        return trace_call(function, *args, span_name=span_name, attributes=attributes, capture_output=capture_output, **kwargs)
    return wrapped_sync


def _merge_observe_attributes(*,
                              attributes: dict[str, str | int | float | bool] | None, 
                              metadata: dict[str, str | int | float | bool] | None, 
                              session_id: str | None,) -> dict[str, str | int | float | bool] | None:
    resolved_attributes: dict[str, str | int | float | bool] = {}
    if metadata: resolved_attributes.update(metadata)
    if attributes: resolved_attributes.update(attributes)
    if session_id is not None: resolved_attributes["session.id"] = session_id
    return resolved_attributes or None


def observe(function=None, 
            /,
            *,
            span_name: str | None = None,
            name: str | None = None,
            attributes: dict[str, str | int | float | bool] | None = None,
            metadata: dict[str, str | int | float | bool] | None = None,
            session_id: str | None = None,
            capture_output: bool = False,):
    resolved_span_name = span_name or name
    resolved_attributes = _merge_observe_attributes(attributes=attributes, metadata=metadata, session_id=session_id)
    if function is None:
        return functools.partial(_wrap_observed_function, span_name=resolved_span_name, attributes=resolved_attributes, capture_output=capture_output)
    return _wrap_observed_function(function, span_name=resolved_span_name, attributes=resolved_attributes, capture_output=capture_output)
