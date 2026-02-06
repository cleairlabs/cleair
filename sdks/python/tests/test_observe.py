from __future__ import annotations

import cleair
from cleair import _core


def test_observe_without_parentheses_calls_trace(monkeypatch) -> None:
    def target() -> str: return "ok"

    trace_calls: list[tuple[tuple[object, ...], dict[str, object]]] = []

    def fake_trace(*args, **kwargs):
        trace_calls.append((args, kwargs))
        if args: return args[0]
        return lambda function: function

    monkeypatch.setattr(_core, "trace", fake_trace)
    wrapped = _core.observe(target)

    assert wrapped is target
    assert trace_calls == [((target,), {"span_name": None, "attributes": None, "capture_output": False})]


def test_observe_merges_attributes_and_metadata(monkeypatch) -> None:
    def target() -> str: return "ok"

    trace_calls: list[tuple[tuple[object, ...], dict[str, object]]] = []

    def fake_trace(*args, **kwargs):
        trace_calls.append((args, kwargs))
        if args: return args[0]
        return lambda function: function

    monkeypatch.setattr(_core, "trace", fake_trace)
    decorator = _core.observe(
        name="story",
        metadata={"source": "langfuse", "override": "metadata"},
        attributes={"override": "attributes"},
        session_id="session-1",
    )
    wrapped = decorator(target)

    assert wrapped is target
    assert trace_calls == [
        (
            (),
            {
                "span_name": "story",
                "attributes": {
                    "source": "langfuse",
                    "override": "attributes",
                    "session.id": "session-1",
                },
                "capture_output": False,
            },
        )
    ]


def test_observe_capture_output_passes_through(monkeypatch) -> None:
    trace_calls: list[tuple[tuple[object, ...], dict[str, object]]] = []

    def fake_trace(*args, **kwargs):
        trace_calls.append((args, kwargs))
        if args: return args[0]
        return lambda function: function

    monkeypatch.setattr(_core, "trace", fake_trace)
    _core.observe(capture_output=True)

    assert trace_calls == [
        (
            (),
            {
                "span_name": None,
                "attributes": None,
                "capture_output": True,
            },
        )
    ]


def test_trace_call_capture_output_adds_event(monkeypatch) -> None:
    class FakeSpan:
        def __init__(self) -> None:
            self.events: list[tuple[str, dict[str, object]]] = []
            self.attributes: dict[str, object] = {}

        def __enter__(self) -> "FakeSpan":
            return self

        def __exit__(self, _exc_type, _exc, _tb) -> bool:
            return False

        def set_attribute(self, name: str, value: object) -> None:
            self.attributes[name] = value

        def record_exception(self, _exception: Exception) -> None:
            return None

        def set_status(self, _status: object) -> None:
            return None

        def add_event(self, name: str, attributes: dict[str, object] | None = None) -> None:
            self.events.append((name, attributes or {}))

    class FakeTracer:
        def __init__(self, span: FakeSpan) -> None:
            self.span = span

        def start_as_current_span(self, _name: str) -> FakeSpan:
            return self.span

    span = FakeSpan()
    monkeypatch.setattr(_core, "_tracer", lambda: FakeTracer(span))

    def target() -> str: return "ok"

    result = _core.trace_call(target, capture_output=True)

    assert result == "ok"
    assert span.events == [("function.output", {"value": "ok"})]


def test_observe_is_exposed_on_package() -> None:
    assert hasattr(cleair, "observe")
