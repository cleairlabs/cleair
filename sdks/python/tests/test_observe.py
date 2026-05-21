from __future__ import annotations

import cleair
from cleair import _core, observe


def test_module_observe_without_parentheses_wraps_function(monkeypatch) -> None:
    def target() -> str:
        return "ok"

    wrap_calls: list[tuple[tuple[object, ...], dict[str, object]]] = []

    def fake_wrap(*args, **kwargs):
        wrap_calls.append((args, kwargs))
        return args[0]

    monkeypatch.setattr(_core, "_wrap_observed_function", fake_wrap)
    wrapped = observe(target)

    assert wrapped is target
    assert wrap_calls == [((target,), {"span_name": None, "attributes": None, "capture_output": False})]


def test_module_observe_merges_attributes_and_metadata(monkeypatch) -> None:
    def target() -> str:
        return "ok"

    wrap_calls: list[tuple[tuple[object, ...], dict[str, object]]] = []

    def fake_wrap(*args, **kwargs):
        wrap_calls.append((args, kwargs))
        return args[0]

    monkeypatch.setattr(_core, "_wrap_observed_function", fake_wrap)
    decorator = observe(
        name="story",
        metadata={"source": "langfuse", "override": "metadata"},
        as_type={"override": "attributes"},
        agent_id="agent-1",
        batch_id="batch-1",
        session_id="session-1",
    )
    wrapped = decorator(target)

    assert wrapped is target
    assert wrap_calls == [
        (
            (target,),
            {
                "span_name": "story",
                "attributes": {
                    "source": "langfuse",
                    "override": "attributes",
                    "agent.id": "agent-1",
                    "batch.id": "batch-1",
                    "session.id": "session-1",
                },
                "capture_output": False,
            },
        )
    ]


def test_module_observe_capture_output_passes_through(monkeypatch) -> None:
    wrap_calls: list[tuple[tuple[object, ...], dict[str, object]]] = []
    target = lambda: None

    def fake_wrap(*args, **kwargs):
        wrap_calls.append((args, kwargs))
        return args[0]

    monkeypatch.setattr(_core, "_wrap_observed_function", fake_wrap)
    decorator = observe(capture_output=True)
    decorator(target)

    assert wrap_calls == [((target,), {"span_name": None, "attributes": None, "capture_output": True})]


def test_module_observe_is_exposed_on_package() -> None:
    assert hasattr(cleair, "observe")


def test_init_is_exposed_on_package() -> None:
    assert hasattr(cleair, "init")


def test_type_constants_are_exposed_on_package() -> None:
    assert cleair.type.AGENT == {"cleair.type": "agent"}


def test_direct_observe_import_is_usable(monkeypatch) -> None:
    monkeypatch.setattr(_core, "trace_call", lambda function, *args, **kwargs: function(*args))

    @observe()
    def target() -> str:
        return "ok"

    assert target() == "ok"
