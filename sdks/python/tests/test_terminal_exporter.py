from __future__ import annotations

from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode
from opentelemetry.trace.span import TraceFlags
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SimpleSpanProcessor

from cleair.exporters import CleairConsoleSpanExporter


def test_cleair_span_exporter_prints_nested_spans_as_tree(capsys) -> None:
    provider = TracerProvider()
    provider.add_span_processor(
        BatchSpanProcessor(CleairConsoleSpanExporter(use_rich=False))
    )
    tracer = provider.get_tracer("tests.terminal")

    with tracer.start_as_current_span("request"):
        with tracer.start_as_current_span("llm.decorator"):
            with tracer.start_as_current_span("llm.manual"):
                pass

    provider.shutdown()
    captured_output = capsys.readouterr().out

    assert "trace=" in captured_output
    assert "- request" in captured_output
    assert "  - llm.decorator" in captured_output
    assert "    - llm.manual" in captured_output


def test_cleair_span_exporter_trace_id_is_hex(capsys) -> None:
    provider = TracerProvider()
    provider.add_span_processor(
        BatchSpanProcessor(CleairConsoleSpanExporter(use_rich=False))
    )
    tracer = provider.get_tracer("tests.trace_id")

    with tracer.start_as_current_span("request"):
        pass

    provider.shutdown()
    captured_output = capsys.readouterr().out

    trace_line = captured_output.splitlines()[0]
    trace_id_hex = trace_line.split("trace=")[1].split(" ")[0]
    assert len(trace_id_hex) == 32
    assert all(character in "0123456789abcdef" for character in trace_id_hex)


def test_cleair_span_exporter_prints_status_events_and_selected_attributes(capsys) -> None:
    provider = TracerProvider()
    provider.add_span_processor(
        BatchSpanProcessor(CleairConsoleSpanExporter(use_rich=False))
    )
    tracer = provider.get_tracer("tests.metadata")

    with tracer.start_as_current_span(
        "agent.llm",
        attributes={
            "gen_ai.request.model": "unknown",
            "session.id": "session-1",
            "ignored.attr": "ignored-value",
        },
    ) as span:
        span.add_event("function.output", {"value": "ok"})
        span.set_status(Status(StatusCode.ERROR))

    provider.shutdown()
    captured_output = capsys.readouterr().out

    assert "status=UNSET" not in captured_output
    assert "status=ERROR" in captured_output
    assert "events=1" in captured_output
    assert "gen_ai.request.model=unknown" in captured_output
    assert "session.id=session-1" in captured_output
    assert "ignored.attr=ignored-value" not in captured_output


def test_cleair_span_exporter_selects_only_whitelisted_key_attributes() -> None:
    class FakeSpan:
        def __init__(self) -> None:
            self.attributes = {
                "gen_ai.request.model": "unknown",
                "session.id": "session-1",
                "ignored.attr": "ignored-value",
            }

    exporter = CleairConsoleSpanExporter(use_rich=False)
    selected_key_attributes = exporter._get_selected_key_attributes(FakeSpan())

    assert selected_key_attributes == [
        ("gen_ai.request.model", "unknown"),
        ("session.id", "session-1"),
    ]


def test_cleair_span_exporter_buffers_child_until_parent_is_exported(capsys) -> None:
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(CleairConsoleSpanExporter(use_rich=False)))
    tracer = provider.get_tracer("tests.split_batches")

    with tracer.start_as_current_span("request"):
        with tracer.start_as_current_span("llm.child"):
            pass

    provider.shutdown()
    captured_output = capsys.readouterr().out

    assert captured_output.count("trace=") == 1
    assert "- request" in captured_output
    assert "  - llm.child" in captured_output


def test_cleair_span_exporter_emits_remote_parent_traces_without_local_root(capsys) -> None:
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(CleairConsoleSpanExporter(use_rich=False)))
    tracer = provider.get_tracer("tests.remote_parent")

    remote_parent_context = trace.SpanContext(
        trace_id=0x11111111111111111111111111111111,
        span_id=0x2222222222222222,
        is_remote=True,
        trace_flags=TraceFlags(TraceFlags.SAMPLED),
        trace_state=trace.DEFAULT_TRACE_STATE,
    )
    parent_span = trace.NonRecordingSpan(remote_parent_context)
    parent_context = trace.set_span_in_context(parent_span)

    with tracer.start_as_current_span("server.span", context=parent_context):
        pass

    captured_output = capsys.readouterr().out
    provider.shutdown()

    assert captured_output.count("trace=") == 1
    assert "- server.span" in captured_output


def test_cleair_span_exporter_emits_trace_continuation_after_root_batch(capsys) -> None:
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(CleairConsoleSpanExporter(use_rich=False)))
    tracer = provider.get_tracer("tests.continuation")

    with tracer.start_as_current_span("request") as root_span:
        root_trace_id = root_span.get_span_context().trace_id
        root_span_id = root_span.get_span_context().span_id
        with tracer.start_as_current_span("child.initial"):
            pass

    continuation_parent_context = trace.SpanContext(
        trace_id=root_trace_id,
        span_id=root_span_id,
        is_remote=False,
        trace_flags=TraceFlags(TraceFlags.SAMPLED),
        trace_state=trace.DEFAULT_TRACE_STATE,
    )
    continuation_parent_span = trace.NonRecordingSpan(continuation_parent_context)
    continuation_context = trace.set_span_in_context(continuation_parent_span)

    with tracer.start_as_current_span("child.late", context=continuation_context):
        pass

    captured_output = capsys.readouterr().out
    provider.shutdown()

    assert captured_output.count("trace=") == 2
    assert "- request" in captured_output
    assert "- child.late" in captured_output
