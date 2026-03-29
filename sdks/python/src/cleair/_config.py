from __future__ import annotations

import os
from dataclasses import dataclass


DEFAULT_CLEAIR_HTTP_ENDPOINT = "https://api.cleair.ai/v1/events"


@dataclass(frozen=True)
class CleairConfig:
    service_name: str = "cleair-app"
    exporter: str = "cleair_http"  # "cleair_http" or "console"
    cleair_http_endpoint: str = DEFAULT_CLEAIR_HTTP_ENDPOINT
    cleair_api_key: str | None = None

    @staticmethod
    def from_env() -> "CleairConfig":
        return CleairConfig(
            service_name=os.getenv("OTEL_SERVICE_NAME", "cleair-app"),
            exporter=os.getenv("CLEAIR_EXPORTER", "cleair_http"),
            cleair_http_endpoint=os.getenv("CLEAIR_HTTP_ENDPOINT", DEFAULT_CLEAIR_HTTP_ENDPOINT),
        )
