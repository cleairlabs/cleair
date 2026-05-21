"""Transient live span-start ingestion for immediate UI updates."""
from __future__ import annotations


def live_payload_to_events(payload: dict) -> tuple[str, str, dict[str, str | int | float | bool], list[dict]]:
    run_id = str(payload["runId"])
    service_name = str(payload["serviceName"])
    raw_metadata = payload.get("metadata", {})
    metadata = raw_metadata if isinstance(raw_metadata, dict) else {}
    span = payload["span"]
    span_id = str(span["id"])
    parent_span_id = span.get("parentId")
    node_type = str(span.get("type", "tool"))
    node_label = str(span.get("label", span_id))
    return (
        run_id,
        service_name,
        metadata,
        [
            {
                "type": "node_added",
                "node": {
                    "id": span_id,
                    "parentId": None if parent_span_id in {None, ""} else str(parent_span_id),
                    "label": node_label,
                    "subtitle": service_name,
                    "type": node_type,
                },
            },
            {"type": "node_status_changed", "nodeId": span_id, "status": "running"},
        ],
    )
