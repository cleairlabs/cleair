"""Provider-specific OTLP presentation adapters registered by cleAIr."""
from __future__ import annotations

from cleair_backend.providers.claude_code import ClaudeCodeAdapter
from cleair_backend.providers.models import ProviderAdapter, SpanAttributeValue, SpanPresentation


PROVIDER_ADAPTERS: tuple[ProviderAdapter, ...] = (ClaudeCodeAdapter(),)


def provider_span_presentation(span_name: str, span_attributes: dict[str, SpanAttributeValue], service_name: str) -> SpanPresentation | None:
    for provider_adapter in PROVIDER_ADAPTERS:
        if provider_adapter.supports(span_name):
            return provider_adapter.present(span_name, span_attributes, service_name)
    return None
