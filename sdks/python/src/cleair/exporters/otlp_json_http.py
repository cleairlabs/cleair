"""OTLP/JSON HTTP span exporter.

Sends spans to any OTLP/HTTP endpoint using JSON encoding and stdlib urllib —
no extra dependencies beyond the OpenTelemetry SDK.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections.abc import Sequence

from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult


def _attribute_value(value: object) -> dict:
    if isinstance(value, bool):
        return {"boolValue": value}
    if isinstance(value, int):
        return {"intValue": str(value)}
    if isinstance(value, float):
        return {"doubleValue": value}
    return {"stringValue": str(value)}


def _span_to_otlp_dict(span: ReadableSpan) -> dict:
    ctx = span.context
    parent_span_id = ""
    if span.parent and hasattr(span.parent, "span_id"):
        parent_span_id = format(span.parent.span_id, "016x")

    attributes = [
        {"key": k, "value": _attribute_value(v)}
        for k, v in (span.attributes or {}).items()
    ]

    status_code = "STATUS_CODE_UNSET"
    if span.status and span.status.status_code.name == "ERROR":
        status_code = "STATUS_CODE_ERROR"
    elif span.status and span.status.status_code.name == "OK":
        status_code = "STATUS_CODE_OK"

    return {
        "traceId": format(ctx.trace_id, "032x") if ctx else "",
        "spanId": format(ctx.span_id, "016x") if ctx else "",
        "parentSpanId": parent_span_id,
        "name": span.name,
        "startTimeUnixNano": str(span.start_time or 0),
        "endTimeUnixNano": str(span.end_time or 0),
        "attributes": attributes,
        "status": {"code": status_code},
    }


def _build_otlp_payload(spans: Sequence[ReadableSpan], service_name: str) -> dict:
    return {
        "resourceSpans": [
            {
                "resource": {
                    "attributes": [
                        {"key": "service.name", "value": {"stringValue": service_name}}
                    ]
                },
                "scopeSpans": [
                    {
                        "scope": {"name": "cleair"},
                        "spans": [_span_to_otlp_dict(s) for s in spans],
                    }
                ],
            }
        ]
    }


class OtlpJsonHttpExporter(SpanExporter):
    """Export spans as OTLP/JSON to an HTTP endpoint."""

    def __init__(self, endpoint: str, service_name: str = "cleair-app") -> None:
        self._endpoint = endpoint
        self._service_name = service_name

    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        payload = _build_otlp_payload(spans, self._service_name)
        body = json.dumps(payload).encode()
        request = urllib.request.Request(
            self._endpoint,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=10):
                pass
            return SpanExportResult.SUCCESS
        except urllib.error.URLError:
            return SpanExportResult.FAILURE

    def shutdown(self) -> None:
        pass
