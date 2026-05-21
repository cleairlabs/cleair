from __future__ import annotations

import re

from cleair._config import CleairConfig, DEFAULT_BASE_URL


def test_config_from_env_defaults():
    config = CleairConfig.from_env()
    assert re.fullmatch(r"agent-\d{6}-\d{8}", config.service_name)
    assert config.base_url == DEFAULT_BASE_URL
    assert config.api_key is None
    assert config.enabled is True
    assert config.use_live is True


def test_config_from_env_reads_all_env_vars(monkeypatch) -> None:
    monkeypatch.setenv("CLEAIR_SERVICE_NAME", "my-svc")
    monkeypatch.setenv("CLEAIR_BASE_URL", "https://example.com")
    monkeypatch.setenv("CLEAIR_API_KEY", "test-key")
    monkeypatch.setenv("CLEAIR_ENABLED", "false")
    monkeypatch.setenv("CLEAIR_USE_LIVE", "false")

    config = CleairConfig.from_env()

    assert config.service_name == "my-svc"
    assert config.base_url == "https://example.com"
    assert config.api_key == "test-key"
    assert config.enabled is False
    assert config.use_live is False
