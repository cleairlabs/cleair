from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Adapter:
    name: str

    def matches(self, target: object) -> bool:
        raise NotImplementedError

    def instrument(self, target: object) -> object:
        raise NotImplementedError