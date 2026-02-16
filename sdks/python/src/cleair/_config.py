from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class CleairConfig:
    service_name: str = "cleair-app"
    exporter: str = "otlp_http"  # "otlp_http", "console", or "terminal"
    otlp_http_endpoint: str = "http://localhost:4318/v1/traces"
    terminal_stream: bool = False

    @staticmethod
    def _env_bool(name: str, default: bool = False) -> bool:
        value = os.getenv(name)
        if value is None:
            return default
        return value.strip().lower() in ("1", "true", "yes", "on")

    @staticmethod
    def from_env() -> "CleairConfig":
        return CleairConfig(
            service_name=os.getenv("OTEL_SERVICE_NAME", "cleair-app"),
            exporter=os.getenv("CLEAIR_EXPORTER", "otlp_http"),
            otlp_http_endpoint=os.getenv(
                "OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", "http://localhost:4318/v1/traces"
            ),
            terminal_stream=CleairConfig._env_bool("CLEAIR_TERMINAL_STREAM", default=False),
        )
