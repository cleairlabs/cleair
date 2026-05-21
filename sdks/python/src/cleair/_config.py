from __future__ import annotations

import os
from datetime import datetime, timezone
from dataclasses import dataclass


DEFAULT_BASE_URL = "https://api.cleair.ai"


def _generated_service_name() -> str:
    return f"agent-{datetime.now(timezone.utc).strftime('%H%M%S-%Y%m%d')}"


DEFAULT_SERVICE_NAME = _generated_service_name()


def _env_flag(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.lower() not in {"0", "false", "no", "off"}


@dataclass(frozen=True)
class CleairConfig:
    service_name: str = DEFAULT_SERVICE_NAME
    base_url: str = DEFAULT_BASE_URL
    api_key: str | None = None
    enabled: bool = True
    use_live: bool = True

    @staticmethod
    def from_env() -> "CleairConfig":
        return CleairConfig(
            service_name=os.getenv("CLEAIR_SERVICE_NAME") or DEFAULT_SERVICE_NAME,
            base_url=os.getenv("CLEAIR_BASE_URL", DEFAULT_BASE_URL),
            api_key=os.getenv("CLEAIR_API_KEY"),
            enabled=_env_flag("CLEAIR_ENABLED", True),
            use_live=_env_flag("CLEAIR_USE_LIVE", True),
        )
