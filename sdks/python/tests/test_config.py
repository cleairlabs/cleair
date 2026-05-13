from __future__ import annotations

from cleair._config import CleairConfig, DEFAULT_BASE_URL


def test_config_from_env_defaults():
    config = CleairConfig.from_env()
    assert config.service_name == "cleair-app"
    assert config.base_url == DEFAULT_BASE_URL
    assert config.api_key is None
    assert config.enabled is True


def test_config_from_env_reads_all_env_vars(monkeypatch) -> None:
    monkeypatch.setenv("CLEAIR_SERVICE_NAME", "my-svc")
    monkeypatch.setenv("CLEAIR_BASE_URL", "https://example.com")
    monkeypatch.setenv("CLEAIR_API_KEY", "test-key")
    monkeypatch.setenv("CLEAIR_ENABLED", "false")

    config = CleairConfig.from_env()

    assert config.service_name == "my-svc"
    assert config.base_url == "https://example.com"
    assert config.api_key == "test-key"
    assert config.enabled is False
