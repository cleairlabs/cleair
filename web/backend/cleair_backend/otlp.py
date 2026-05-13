"""OTLP/JSON → FlowGraphEvent converter.

Receives an OTLP/JSON trace payload (as parsed dict) and produces a list of
(trace_id, service_name, events) tuples ready for the TraceStore.

Spans are sorted by startTimeUnixNano so parents always appear before children
in the event stream (OTLP exporters emit children before parents on completion).
"""
from __future__ import annotations


def _span_type(attributes: list[dict]) -> str:
    """Map cleair.type span attribute to a FlowNode type, defaulting to 'tool'."""
    for attr in attributes:
        if attr.get("key") == "cleair.type":
            return str(attr.get("value", {}).get("stringValue", "tool"))
    return "tool"


def _str_attr(attributes: list[dict], key: str, default: str = "") -> str:
    for attr in attributes:
        if attr.get("key") == key:
            return str(attr.get("value", {}).get("stringValue", default))
    return default


def _span_to_events(span: dict, service_name: str) -> list[dict]:
    """Convert a single OTLP span to a sequence of FlowGraphEvents."""
    span_id = span.get("spanId", "")
    parent_span_id = span.get("parentSpanId") or None
    name = span.get("name", span_id)
    attributes: list[dict] = span.get("attributes", [])
    start_ns = int(span.get("startTimeUnixNano", 0))
    end_ns = int(span.get("endTimeUnixNano", 0))
    duration_ms = max(0, (end_ns - start_ns) // 1_000_000)

    status_code = span.get("status", {}).get("code", "STATUS_CODE_UNSET")
    node_status = "error" if status_code == "STATUS_CODE_ERROR" else "done"

    return [
        {
            "type": "node_added",
            "node": {
                "id": span_id,
                "parentId": parent_span_id,
                "label": name,
                "subtitle": service_name,
                "type": _span_type(attributes),
                "whatDescription": _str_attr(attributes, "cleair.what", name),
            },
        },
        {"type": "node_status_changed", "nodeId": span_id, "status": "running"},
        {"type": "node_status_changed", "nodeId": span_id, "status": node_status},
        {"type": "node_finished", "nodeId": span_id, "durationMs": duration_ms},
    ]


def otlp_payload_to_run_events(payload: dict) -> list[tuple[str, str, list[dict]]]:
    """Parse an OTLP/JSON ExportTraceServiceRequest into per-trace event lists.

    Returns a list of (trace_id, service_name, events) tuples, one per trace found
    in the payload. Events within each trace are sorted by span start time.
    """
    results: list[tuple[str, str, list[dict]]] = []

    for resource_span in payload.get("resourceSpans", []):
        resource = resource_span.get("resource", {})
        resource_attributes: list[dict] = resource.get("attributes", [])
        service_name = _str_attr(resource_attributes, "service.name", "unknown")

        for scope_span in resource_span.get("scopeSpans", []):
            spans: list[dict] = scope_span.get("spans", [])
            if not spans:
                continue

            # All spans in a scopeSpan share the same traceId.
            trace_id = spans[0].get("traceId", "unknown")

            # Sort by start time so parents appear before children.
            sorted_spans = sorted(spans, key=lambda s: int(s.get("startTimeUnixNano", 0)))

            events: list[dict] = []
            has_root_span = False
            for span in sorted_spans:
                events.extend(_span_to_events(span, service_name))
                if not span.get("parentSpanId"):
                    has_root_span = True

            if has_root_span:
                events.append({"type": "run_completed"})

            results.append((trace_id, service_name, events))

    return results
