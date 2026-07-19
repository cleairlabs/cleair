"""Types shared by provider-specific OTLP presentation adapters."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


SpanAttributeValue = str | int | float | bool


@dataclass(frozen=True)
class SpanPresentation:
    label: str
    node_type: str
    subtitle: str
    input_value: str | None = None
    output_event_name: str | None = None
    output_attribute_name: str = "value"


class ProviderAdapter(Protocol):
    def supports(self, span_name: str) -> bool:
        """Logic for identifying provider-owned span names."""
        ...

    def present(self, span_name: str, span_attributes: dict[str, SpanAttributeValue], service_name: str) -> SpanPresentation | None:
        """Logic for presenting a provider span in the trace UI."""
        ...

    def run_metadata(self, span_name: str, span_attributes: dict[str, SpanAttributeValue]) -> dict[str, SpanAttributeValue]:
        """Logic for extracting provider-specific run metadata."""
        ...
