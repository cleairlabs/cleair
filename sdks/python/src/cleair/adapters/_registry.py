from __future__ import annotations

from cleair.adapters._base import Adapter

_ADAPTERS: list[Adapter] = []


def add_adapter(adapter: Adapter) -> None:
    _ADAPTERS.append(adapter)


def instrument(target: object) -> object:
    for adapter in _ADAPTERS:
        if adapter.matches(target):
            return adapter.instrument(target)
    return target