from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class GatewaySettings(BaseSettings):
    gateway_name: str = "cleair-gateway"
    redis_url: str = "redis://localhost:6379/0"

    model_config = SettingsConfigDict(
        env_prefix="CLEAIR_",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> GatewaySettings:
    return GatewaySettings()
