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
    assert trace_calls == [((target,), {"span_name": None, "attributes": None})]


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
            },
        )
    ]


def test_observe_is_exposed_on_package() -> None:
    assert hasattr(cleair, "observe")
