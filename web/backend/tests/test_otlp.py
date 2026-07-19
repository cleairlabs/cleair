from cleair_backend.otlp import ParsedTraceRun, otlp_payload_to_run_events


def test_otlp_payload_to_run_events_preserves_ui_fields_from_otlp() -> None:
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
                                    {"key": "agent.id", "value": {"stringValue": "agent-1"}},
                                    {"key": "batch.id", "value": {"stringValue": "batch-1"}},
                                    {"key": "cleair.type", "value": {"stringValue": "agent"}},
                                ],
                                "events": [
                                    {
                                        "name": "function.input",
                                        "attributes": [{"key": "value", "value": {"stringValue": "{'query': 'weather'}"}}],
                                    },
                                    {
                                        "name": "function.output",
                                        "attributes": [{"key": "value", "value": {"stringValue": "done"}}],
                                    }
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
        ParsedTraceRun(
            trace_id="trace-1",
            service_name="frontend",
            metadata={"agent.id": "agent-1", "batch.id": "batch-1"},
            events=[
                {
                    "type": "node_added",
                    "node": {
                        "id": "span-1",
                        "parentId": None,
                        "label": "LoadDashboard",
                        "subtitle": "frontend",
                        "type": "agent",
                        "input": "{'query': 'weather'}",
                    },
                },
                {"type": "node_status_changed", "nodeId": "span-1", "status": "running"},
                {"type": "node_status_changed", "nodeId": "span-1", "status": "done"},
                {"type": "node_finished", "nodeId": "span-1", "durationMs": 2, "output": "done"},
                {"type": "run_completed"},
            ],
            is_completed=True,
        )
    ]


def test_otlp_payload_to_run_events_uses_only_root_span_metadata() -> None:
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
                                "spanId": "root-span",
                                "name": "RootSpan",
                                "startTimeUnixNano": "1000",
                                "endTimeUnixNano": "2001000",
                                "attributes": [
                                    {"key": "agent.id", "value": {"stringValue": "agent-1"}},
                                    {"key": "cleair.type", "value": {"stringValue": "agent"}},
                                ],
                            },
                            {
                                "traceId": "trace-1",
                                "spanId": "child-span",
                                "parentSpanId": "root-span",
                                "name": "ChildSpan",
                                "startTimeUnixNano": "2000",
                                "endTimeUnixNano": "3001000",
                                "attributes": [
                                    {"key": "session.id", "value": {"stringValue": "session-1"}},
                                    {"key": "cleair.type", "value": {"stringValue": "tool"}},
                                ],
                            },
                        ]
                    }
                ],
            }
        ]
    }

    events = otlp_payload_to_run_events(payload)

    assert events == [
        ParsedTraceRun(
            trace_id="trace-1",
            service_name="frontend",
            metadata={"agent.id": "agent-1"},
            events=[
                {
                    "type": "node_added",
                    "node": {
                        "id": "root-span",
                        "parentId": None,
                        "label": "RootSpan",
                        "subtitle": "frontend",
                        "type": "agent",
                    },
                },
                {"type": "node_status_changed", "nodeId": "root-span", "status": "running"},
                {"type": "node_status_changed", "nodeId": "root-span", "status": "done"},
                {"type": "node_finished", "nodeId": "root-span", "durationMs": 2},
                {
                    "type": "node_added",
                    "node": {
                        "id": "child-span",
                        "parentId": "root-span",
                        "label": "ChildSpan",
                        "subtitle": "frontend",
                        "type": "tool",
                    },
                },
                {"type": "node_status_changed", "nodeId": "child-span", "status": "running"},
                {"type": "node_status_changed", "nodeId": "child-span", "status": "done"},
                {"type": "node_finished", "nodeId": "child-span", "durationMs": 2},
                {"type": "run_completed"},
            ],
            is_completed=True,
        )
    ]


def test_otlp_payload_to_run_events_presents_claude_code_spans() -> None:
    payload = {
        "resourceSpans": [
            {
                "resource": {"attributes": [{"key": "service.name", "value": {"stringValue": "claude-code"}}]},
                "scopeSpans": [
                    {
                        "spans": [
                            {
                                "traceId": "trace-1",
                                "spanId": "0000000000000001",
                                "name": "claude_code.interaction",
                                "startTimeUnixNano": "1000",
                                "endTimeUnixNano": "2001000",
                                "attributes": [{"key": "session.id", "value": {"stringValue": "session-1"}}],
                            },
                            {
                                "traceId": "trace-1",
                                "spanId": "0000000000000002",
                                "parentSpanId": "0000000000000001",
                                "name": "claude_code.tool",
                                "startTimeUnixNano": "2000",
                                "endTimeUnixNano": "3001000",
                                "attributes": [
                                    {"key": "tool_name", "value": {"stringValue": "Bash"}},
                                    {"key": "full_command", "value": {"stringValue": "pytest"}},
                                ],
                                "events": [
                                    {
                                        "name": "tool.output",
                                        "attributes": [{"key": "output", "value": {"stringValue": "3 passed"}}],
                                    }
                                ],
                            },
                        ]
                    }
                ],
            }
        ]
    }

    events = otlp_payload_to_run_events(payload)

    assert events[0].metadata == {"session.id": "session-1", "batch.id": "session-1"}
    assert events[0].events[0]["node"] == {
        "id": "0000000000000001",
        "parentId": None,
        "label": "Claude Code",
        "subtitle": "Interaction",
        "type": "agent",
    }
    assert events[0].events[4]["node"] == {
        "id": "0000000000000002",
        "parentId": "0000000000000001",
        "label": "Bash",
        "subtitle": "Claude Code",
        "type": "tool",
        "input": "Command: pytest",
    }
    assert events[0].events[7] == {
        "type": "node_finished",
        "nodeId": "0000000000000002",
        "durationMs": 2,
        "output": "3 passed",
    }
