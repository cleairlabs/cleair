from cleair_backend.otlp import otlp_payload_to_run_events


def test_otlp_payload_to_run_events_excludes_why_description() -> None:
    payload = {
        "resourceSpans": [
            {
                "resource": {
                    "attributes": [
                        {"key": "service.name", "value": {"stringValue": "frontend"}},
                    ]
                },
                "scopeSpans": [
                    {
                        "spans": [
                            {
                                "traceId": "trace-1",
                                "spanId": "span-1",
                                "name": "LoadDashboard",
                                "startTimeUnixNano": "1000",
                                "endTimeUnixNano": "2001000",
                                "attributes": [
                                    {"key": "cleair.kind", "value": {"stringValue": "agent"}},
                                    {"key": "cleair.what", "value": {"stringValue": "Loads dashboard data"}},
                                    {"key": "cleair.why", "value": {"stringValue": "No longer exposed"}},
                                ],
                            }
                        ]
                    }
                ],
            }
        ]
    }

    events = otlp_payload_to_run_events(payload)

    assert events == [
        (
            "trace-1",
            "frontend",
            [
                {
                    "type": "node_added",
                    "node": {
                        "id": "span-1",
                        "parentId": None,
                        "label": "LoadDashboard",
                        "subtitle": "frontend",
                        "kind": "agent",
                        "whatDescription": "Loads dashboard data",
                    },
                },
                {"type": "node_status_changed", "nodeId": "span-1", "status": "running"},
                {"type": "node_status_changed", "nodeId": "span-1", "status": "done"},
                {"type": "node_finished", "nodeId": "span-1", "durationMs": 2},
                {"type": "run_completed"},
            ],
        )
    ]
