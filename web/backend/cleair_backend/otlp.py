"""OTLP trace payload mapping for the cleAIr UI event model."""
from __future__ import annotations

import base64
from dataclasses import dataclass


RUN_METADATA_EXCLUDED_KEYS = frozenset({"cleair.type", "duration_ms"})


@dataclass(frozen=True)
class ParsedTraceRun:
    trace_id: str
    service_name: str
    metadata: dict[str, str | int | float | bool]
    events: list[dict]
    is_completed: bool


@dataclass
class TraceAccumulator:
    service_name: str
    spans: list[dict]


def _attribute_value(value: dict | None) -> str | int | float | bool | None:
    if not isinstance(value, dict):
        return None
    if "stringValue" in value:
        return str(value["stringValue"])
    if "boolValue" in value:
        return bool(value["boolValue"])
    if "intValue" in value:
        return int(value["intValue"])
    if "doubleValue" in value:
        return float(value["doubleValue"])
    return None


def _attribute_map(attributes: list[dict] | None) -> dict[str, str | int | float | bool]:
    attribute_map: dict[str, str | int | float | bool] = {}
    for attribute in attributes or []:
        key = attribute.get("key")
        if not isinstance(key, str):
            continue
        resolved_value = _attribute_value(attribute.get("value"))
        if resolved_value is None:
            continue
        attribute_map[key] = resolved_value
    return attribute_map


def _normalized_id(value: object) -> str:
    if not isinstance(value, str) or value == "":
        return ""
    lowered_value = value.lower()
    if len(lowered_value) in {16, 32} and all(character in "0123456789abcdef" for character in lowered_value):
        return lowered_value
    try:
        return base64.b64decode(value, validate=True).hex()
    except (ValueError, base64.binascii.Error): # type: ignore
        return value


def _span_type(span_attributes: dict[str, str | int | float | bool]) -> str:
    span_type = span_attributes.get("cleair.type")
    return str(span_type) if span_type is not None else "tool"


def _run_metadata(span_attributes: dict[str, str | int | float | bool]) -> dict[str, str | int | float | bool]:
    return {key: value for key, value in span_attributes.items() if key not in RUN_METADATA_EXCLUDED_KEYS}


def _span_event_value(span: dict, event_name: str) -> str | None:
    for span_event in span.get("events", []):
        if span_event.get("name") != event_name:
            continue
        event_value = _attribute_map(span_event.get("attributes", [])).get("value")
        return None if event_value is None else str(event_value)
    return None


def _span_to_events(span: dict, service_name: str) -> tuple[list[dict], dict[str, str | int | float | bool], bool]:
    span_id = _normalized_id(span.get("spanId", ""))
    parent_span_id = _normalized_id(span.get("parentSpanId", "")) or None
    name = str(span.get("name", span_id))
    span_attributes = _attribute_map(span.get("attributes", []))
    start_ns = int(span.get("startTimeUnixNano", 0))
    end_ns = int(span.get("endTimeUnixNano", 0))
    duration_ms = max(0, (end_ns - start_ns) // 1_000_000)
    status_code = span.get("status", {}).get("code", "STATUS_CODE_UNSET")
    node_status = "error" if status_code == "STATUS_CODE_ERROR" else "done"
    node = {
        "id": span_id,
        "parentId": parent_span_id,
        "label": name,
        "subtitle": service_name,
        "type": _span_type(span_attributes),
    }
    input_value = _span_event_value(span, "function.input")
    if input_value is not None:
        node["input"] = input_value
    node_finished_event: dict[str, str | int] = {"type": "node_finished", "nodeId": span_id, "durationMs": duration_ms}
    output = _span_event_value(span, "function.output")
    if output is not None:
        node_finished_event["output"] = output
    return ([{"type": "node_added", "node": node,},
             {"type": "node_status_changed", "nodeId": span_id, "status": "running"},
             {"type": "node_status_changed", "nodeId": span_id, "status": node_status},
             node_finished_event],
             _run_metadata(span_attributes),
             not parent_span_id)


def otlp_payload_to_run_events(payload: dict) -> list[ParsedTraceRun]:
    traces_by_id: dict[str, TraceAccumulator] = {}
    for resource_span in payload.get("resourceSpans", []):
        resource_attributes = _attribute_map(resource_span.get("resource", {}).get("attributes", []))
        service_name = str(resource_attributes.get("service.name", "unknown"))
        for scope_span in resource_span.get("scopeSpans", []):
            for span in scope_span.get("spans", []):
                trace_id = _normalized_id(span.get("traceId", "")) or "unknown"
                trace_entry = traces_by_id.setdefault(trace_id, TraceAccumulator(service_name=service_name, spans=[]))
                trace_entry.service_name = service_name
                trace_entry.spans.append(span)
    parsed_trace_runs: list[ParsedTraceRun] = []
    for trace_id, trace_entry in traces_by_id.items():
        service_name = trace_entry.service_name
        sorted_spans = sorted(trace_entry.spans, key=lambda span: int(span.get("startTimeUnixNano", 0)))
        events: list[dict] = []
        metadata: dict[str, str | int | float | bool] = {}
        is_completed = False
        for span in sorted_spans:
            span_events, span_metadata, is_root_span = _span_to_events(span, service_name)
            events.extend(span_events)
            if is_root_span:
                metadata.update(span_metadata)
            is_completed = is_completed or is_root_span
        if is_completed:
            events.append({"type": "run_completed"})
        parsed_trace_runs.append(
            ParsedTraceRun(
                trace_id=trace_id,
                service_name=service_name,
                metadata=metadata,
                events=events,
                is_completed=is_completed,
            )
        )
    return parsed_trace_runs
