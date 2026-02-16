from __future__ import annotations

from dataclasses import dataclass

from cleair.adapters._base import Adapter
from cleair.adapters._registry import _ADAPTERS, add_adapter, instrument


@dataclass(frozen=True)
class UpperAdapter(Adapter):
    def matches(self, target: object) -> bool:
        return isinstance(target, str)

    def instrument(self, target: object) -> object:
        return str(target).upper()


def setup_function():
    _ADAPTERS.clear()


def test_add_adapter_and_instrument():
    add_adapter(UpperAdapter(name="upper"))
    assert instrument("hello") == "HELLO"


def test_instrument_returns_passthrough_when_no_match():
    add_adapter(UpperAdapter(name="upper"))
    assert instrument(42) == 42


def test_instrument_returns_passthrough_when_no_adapters():
    assert instrument("hello") == "hello"
