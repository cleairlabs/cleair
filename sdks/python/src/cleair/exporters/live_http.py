"""Best-effort live span-start notifications for the cleAIr UI."""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections.abc import Mapping
from typing import Optional

from opentelemetry.context import Context
from opentelemetry.sdk.trace import Span
from opentelemetry.sdk.trace import SpanProcessor

TRACE_ID_FORMAT = "032x"
SPAN_ID_FORMAT = "016x"
REQUEST_TIMEOUT_SECONDS = 1


def _str_attr(attributes: object, key: str, default: str = "") -> str:
    if not isinstance(attributes, Mapping):
        return default
    value = attributes.get(key)
    return default if value is None else str(value)


def _run_metadata(attributes: object) -> dict[str, str | int | float | bool]:
    if not isinstance(attributes, Mapping):
        return {}
    return {key: value for key, value in attributes.items() if key not in {"cleair.type", "duration_ms"}}


class CleairLiveSpanProcessor(SpanProcessor):
    def __init__(self, base_url: str, api_key: str, service_name: str) -> None:
        self._live_url = f"{base_url.rstrip('/')}/v1/live"
        self._api_key = api_key
        self._service_name = service_name

    def on_start(self, span: Span, parent_context: Optional[Context] = None) -> None:
        span_context = span.context
        if span_context is None or not span_context.is_valid:
            return
        span_attributes = span.attributes or {}
        run_id = format(span_context.trace_id, TRACE_ID_FORMAT)
        span_id = format(span_context.span_id, SPAN_ID_FORMAT)
        parent_span_id = format(span.parent.span_id, SPAN_ID_FORMAT) if span.parent and span.parent.span_id else None
        payload = {
            "runId": run_id,
            "serviceName": self._service_name,
            "metadata": _run_metadata(span_attributes) if parent_span_id is None else {},
            "span": {
                "id": span_id,
                "parentId": parent_span_id,
                "label": span.name,
                "type": _str_attr(span_attributes, "cleair.type", "tool"),
            },
        }
        self._post(payload)

    def on_end(self, span) -> None:
        return None

    def shutdown(self) -> None:
        return None

    def force_flush(self, timeout_millis: int = 30_000) -> bool:
        return True

    def _post(self, payload: dict) -> None:
        request = urllib.request.Request(
            self._live_url,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json", "X-Channel-API-Key": self._api_key},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS):
                pass
        except urllib.error.URLError:
            pass
