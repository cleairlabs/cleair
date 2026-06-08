from __future__ import annotations

import functools
import inspect
import threading
import time
from contextvars import ContextVar
from contextlib import contextmanager

from opentelemetry import trace as otel_trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import INVALID_SPAN, Status, StatusCode, set_span_in_context

from cleair._config import CleairConfig
from cleair.adapters._base import Adapter
from cleair.adapters._registry import add_adapter, instrument
from cleair.exporters.live_http import CleairLiveSpanProcessor

_config: CleairConfig | None = None
_provider: TracerProvider | None = None
_provider_lock = threading.Lock()
_run_attributes: ContextVar[dict[str, str | int | float | bool] | None] = ContextVar("cleair_run_attributes", default=None)
OTLP_SCHEDULE_DELAY_MILLIS = 200


def _traces_endpoint(base_url: str) -> str:
    return f"{base_url.rstrip('/')}/v1/traces"


def _format_attribute_value(value: object) -> str | int | float | bool:
    if isinstance(value, (str, int, float, bool)):
        return value
    return repr(value)


def _merge_observe_attributes(*,
                              attributes: dict[str, str | int | float | bool] | None,
                              metadata: dict[str, str | int | float | bool] | None,
                              agent_id: str | None,
                              batch_id: str | None,
                              session_id: str | None,) -> dict[str, str | int | float | bool] | None:
    resolved_attributes: dict[str, str | int | float | bool] = {}
    if metadata:
        resolved_attributes.update(metadata)
    if attributes:
        resolved_attributes.update(attributes)
    if agent_id is not None:
        resolved_attributes["agent.id"] = agent_id
    if batch_id is not None:
        resolved_attributes["batch.id"] = batch_id
    if session_id is not None:
        resolved_attributes["session.id"] = session_id
    return resolved_attributes or None


def _resolve_span_attributes(attributes: dict[str, str | int | float | bool] | None) -> dict[str, str | int | float | bool] | None:
    inherited_attributes = _run_attributes.get()
    if inherited_attributes is None:
        return attributes
    if attributes is None:
        return dict(inherited_attributes)
    return {**inherited_attributes, **attributes}


def _run_child_attributes(attributes: dict[str, str | int | float | bool] | None) -> dict[str, str | int | float | bool] | None:
    if attributes is None:
        return None
    return {key: value for key, value in attributes.items() if key != "cleair.type"} or None


def _resolve_config() -> CleairConfig:
    return _config or CleairConfig.from_env()


def init(config: CleairConfig | None = None, *,
         service_name: str | None = None,
         base_url: str | None = None,
         cleair_api_key: str | None = None,
         enabled: bool | None = None,
         use_live: bool | None = None,) -> None:
    global _config
    base_config = config or CleairConfig.from_env()
    candidate_config = CleairConfig(
        service_name=base_config.service_name if service_name is None else service_name,
        base_url=base_config.base_url if base_url is None else base_url,
        api_key=base_config.api_key if cleair_api_key is None else cleair_api_key,
        enabled=base_config.enabled if enabled is None else enabled,
        use_live=base_config.use_live if use_live is None else use_live,
    )
    with _provider_lock:
        if _config is not None and _config != candidate_config:
            raise ValueError("cleair.init() has already been called with different settings.")
        _config = candidate_config


def _ensure_provider() -> TracerProvider | None:
    global _provider
    config = _resolve_config()
    if not config.enabled:
        return None
    if _provider is not None:
        return _provider
    with _provider_lock:
        if _provider is not None:
            return _provider
        if not config.api_key:
            raise ValueError("api_key is required when cleair is enabled. Call cleair.init(api_key='<key>').")
        resource = Resource.create({"service.name": config.service_name})
        provider = TracerProvider(resource=resource)
        if config.use_live:
            provider.add_span_processor(
                CleairLiveSpanProcessor(base_url=config.base_url, api_key=config.api_key, service_name=config.service_name)
            )
        span_exporter = OTLPSpanExporter(endpoint=_traces_endpoint(config.base_url), headers={"Authorization": f"Bearer {config.api_key}"})
        provider.add_span_processor(BatchSpanProcessor(span_exporter, schedule_delay_millis=OTLP_SCHEDULE_DELAY_MILLIS))
        otel_trace.set_tracer_provider(provider)
        _provider = provider
    return _provider


def _tracer():
    _ensure_provider()
    return otel_trace.get_tracer("cleair")


@contextmanager
def span(name: str, *, attributes: dict[str, str | int | float | bool] | None = None, new_root: bool = False):
    config = _resolve_config()
    if not config.enabled:
        yield None
        return
    tracer = _tracer()
    span_attributes = _resolve_span_attributes(attributes)
    span_kwargs = {"attributes": span_attributes}
    if new_root:
        span_kwargs["context"] = set_span_in_context(INVALID_SPAN) # type: ignore
    with tracer.start_as_current_span(name, **span_kwargs) as span_handle: # type: ignore
        try:
            yield span_handle
        except Exception as exception:
            span_handle.record_exception(exception)
            span_handle.set_status(Status(StatusCode.ERROR))
            raise


@contextmanager
def start_run(name: str,
              *,
              agent_id: str | None = None,
              batch_id: str | None = None,
              session_id: str | None = None,
              metadata: dict[str, str | int | float | bool] | None = None,):
    run_attributes = _merge_observe_attributes(
        attributes={"cleair.type": "trace"},
        metadata=metadata,
        agent_id=agent_id,
        batch_id=batch_id,
        session_id=session_id,
    )
    token = _run_attributes.set(_run_child_attributes(run_attributes))
    try:
        with span(name, attributes=run_attributes, new_root=True) as span_handle:
            yield span_handle
    finally:
        _run_attributes.reset(token)


def trace_call(function,
               /,
               *args,
               span_name: str | None = None,
               attributes: dict[str, str | int | float | bool] | None = None,
               capture_output: bool = False,
               **kwargs,):
    config = _resolve_config()
    if not config.enabled:
        return function(*args, **kwargs)
    name = span_name or getattr(function, "__qualname__", getattr(function, "__name__", "call"))
    with span(name, attributes=attributes) as span_handle:
        start = time.perf_counter()
        try:
            result = function(*args, **kwargs)
            if capture_output and span_handle is not None:
                span_handle.add_event("function.output", {"value": _format_attribute_value(result)})
            return result
        finally:
            if span_handle is not None:
                span_handle.set_attribute("duration_ms", (time.perf_counter() - start) * 1000.0)


async def _trace_call_async(function,
                            /,
                            *args,
                            span_name: str | None = None,
                            attributes: dict[str, str | int | float | bool] | None = None,
                            capture_output: bool = False,
                            **kwargs,):
    config = _resolve_config()
    if not config.enabled:
        return await function(*args, **kwargs)
    name = span_name or getattr(function, "__qualname__", getattr(function, "__name__", "call"))
    with span(name, attributes=attributes) as span_handle:
        start = time.perf_counter()
        try:
            result = await function(*args, **kwargs)
            if capture_output and span_handle is not None:
                span_handle.add_event("function.output", {"value": _format_attribute_value(result)})
            return result
        finally:
            if span_handle is not None:
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
            return await _trace_call_async(
                function, *args, span_name=span_name, attributes=attributes, capture_output=capture_output, **kwargs
            )
        return wrapped_async

    @functools.wraps(function)
    def wrapped_sync(*args, **kwargs):
        return trace_call(function, *args, span_name=span_name, attributes=attributes, capture_output=capture_output, **kwargs)
    return wrapped_sync


def observe(function=None,
            /,
            *,
            span_name: str | None = None,
            name: str | None = None,
            as_type: dict[str, str | int | float | bool] | None = None,
            metadata: dict[str, str | int | float | bool] | None = None,
            agent_id: str | None = None,
            batch_id: str | None = None,
            session_id: str | None = None,
            capture_output: bool = False,):
    resolved_span_name = span_name or name
    resolved_attributes = _merge_observe_attributes(
        attributes=as_type,
        metadata=metadata,
        agent_id=agent_id,
        batch_id=batch_id,
        session_id=session_id,
    )
    if function is None:
        return functools.partial(
            _wrap_observed_function,
            span_name=resolved_span_name,
            attributes=resolved_attributes,
            capture_output=capture_output,
        )
    return _wrap_observed_function(
        function, span_name=resolved_span_name, attributes=resolved_attributes, capture_output=capture_output
    )


def flush() -> None:
    provider = _ensure_provider()
    if provider is not None:
        provider.force_flush()
