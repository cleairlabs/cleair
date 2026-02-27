"""Cleair-native streaming span processor.

Unlike OTLP exporters (which send spans only on completion), this processor
posts events on both span start and span end, enabling the frontend to show
the "running" state in real time.

On start: node_added + node_status_changed(running)
On end:   node_status_changed(done/error) + node_finished [+ run_completed]
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Optional

from opentelemetry.context import Context
from opentelemetry.sdk.trace import ReadableSpan, Span
from opentelemetry.sdk.trace import SpanProcessor
from opentelemetry.trace import StatusCode

TRACE_ID_FORMAT = "032x"
SPAN_ID_FORMAT = "016x"
CONTENT_TYPE_HEADER = "application/json"
REQUEST_TIMEOUT_SECONDS = 5


def _str_attr(attributes: object, key: str, default: str = "") -> str:
    try:
        value = attributes.get(key)  # type: ignore[union-attr]
        return str(value) if value is not None else default
    except AttributeError:
        return default


class CleairHttpSpanProcessor(SpanProcessor):
    """Posts FlowGraphEvents to the cleAIr backend on span start and end."""

    def __init__(self, endpoint: str, service_name: str = "cleair-app", api_key: str | None = None) -> None:
        self._endpoint = endpoint
        self._service_name = service_name
        self._api_key = api_key


    def on_start(self, span: Span, parent_context: Optional[Context] = None) -> None:
        span_context = span.context
        if span_context is None or not span_context.is_valid: return

        run_id = format(span_context.trace_id, TRACE_ID_FORMAT)
        span_id = format(span_context.span_id, SPAN_ID_FORMAT)
        parent_span_id: str | None = (
            format(span.parent.span_id, SPAN_ID_FORMAT)
            if span.parent and span.parent.span_id
            else None
        )
        is_root = parent_span_id is None
        attrs = span.attributes or {}

        events: list[dict] = []
        if is_root: events.append({"type": "run_started", "runId": run_id, "runLabel": self._service_name})
        events.append({
            "type": "node_added",
            "node": {
                "id": span_id,
                "parentId": parent_span_id,
                "label": span.name,
                "subtitle": self._service_name,
                "kind": _str_attr(attrs, "cleair.kind", "tool"),
                "whatDescription": _str_attr(attrs, "cleair.what", span.name),
                "whyDescription": _str_attr(attrs, "cleair.why"),
            },
        })
        events.append({"type": "node_status_changed", "nodeId": span_id, "status": "running"})
        self._post(run_id, events)


    def on_end(self, span: ReadableSpan) -> None:
        span_context = span.context
        if span_context is None or not span_context.is_valid: return

        run_id = format(span_context.trace_id, TRACE_ID_FORMAT)
        span_id = format(span_context.span_id, SPAN_ID_FORMAT)
        is_root = span.parent is None or not span.parent.span_id
        status = "error" if span.status and span.status.status_code == StatusCode.ERROR else "done"
        duration_ms = max(0, ((span.end_time or 0) - (span.start_time or 0)) // 1_000_000)

        output: str | None = None
        for span_event in span.events or []:
            if span_event.name == "function.output":
                raw = (span_event.attributes or {}).get("value")
                if raw is not None: output = str(raw)
                break

        finished: dict = {"type": "node_finished", "nodeId": span_id, "durationMs": duration_ms}
        if output is not None: finished["output"] = output

        events: list[dict] = [{"type": "node_status_changed", "nodeId": span_id, "status": status}, finished]
        if is_root: events.append({"type": "run_completed"})
        self._post(run_id, events)


    def _post(self, run_id: str, events: list[dict]) -> None:
        body = json.dumps({"runId": run_id, "events": events}).encode()
        headers: dict[str, str] = {"Content-Type": CONTENT_TYPE_HEADER}
        if self._api_key:
            headers["X-Channel-API-Key"] = self._api_key
        request = urllib.request.Request(
            self._endpoint,
            data=body,
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS):
                pass
        except urllib.error.URLError:
            pass  # best-effort; do not block the caller


    def shutdown(self) -> None: pass

    def force_flush(self, timeout_millis: int = 30_000) -> bool: return True
