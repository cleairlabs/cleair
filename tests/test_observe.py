from __future__ import annotations

import unittest
from unittest import mock

import cleair
from cleair import _core


class TestObserve(unittest.TestCase):
    def test_observe_without_parentheses_calls_trace(self) -> None:
        def target() -> str:
            return "ok"

        with mock.patch("cleair._core.trace") as trace_mock:
            trace_mock.side_effect = lambda *args, **kwargs: args[0] if args else (lambda function: function)
            wrapped = _core.observe(target)

        self.assertIs(wrapped, target)
        trace_mock.assert_called_once_with(target, span_name=None, attributes=None)

    def test_observe_with_langfuse_style_arguments(self) -> None:
        def target() -> str:
            return "ok"

        with mock.patch("cleair._core.trace") as trace_mock:
            trace_mock.side_effect = lambda *args, **kwargs: args[0] if args else (lambda function: function)
            decorator = _core.observe(
                name="story",
                metadata={"source": "langfuse", "override": "metadata"},
                attributes={"override": "attributes"},
                session_id="session-1",
            )
            wrapped = decorator(target)

        self.assertIs(wrapped, target)
        trace_mock.assert_called_once_with(
            span_name="story",
            attributes={
                "source": "langfuse",
                "override": "attributes",
                "session.id": "session-1",
            },
        )

    def test_observe_is_exposed_on_package(self) -> None:
        self.assertTrue(hasattr(cleair, "observe"))


if __name__ == "__main__":
    unittest.main()
