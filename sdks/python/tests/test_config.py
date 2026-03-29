from __future__ import annotations

import pytest

from cleair._config import CleairConfig, DEFAULT_CLEAIR_HTTP_ENDPOINT


def test_config_from_env_defaults_cleair_http_endpoint_to_hosted_api(monkeypatch) -> None:
    monkeypatch.delenv("CLEAIR_HTTP_ENDPOINT", raising=False)
    config = CleairConfig.from_env()
    assert config.cleair_http_endpoint == DEFAULT_CLEAIR_HTTP_ENDPOINT


def test_config_from_env_does_not_read_cleair_api_key(monkeypatch) -> None:
    monkeypatch.setenv("CLEAIR_API_KEY", "test-key")
    config = CleairConfig.from_env()
    assert config.cleair_api_key is None

def test_config_from_env_reads_all_env_vars(monkeypatch) -> None:
    monkeypatch.setenv("OTEL_SERVICE_NAME", "my-svc")
    monkeypatch.setenv("CLEAIR_EXPORTER", "console")

    config = CleairConfig.from_env()

    assert config.service_name == "my-svc"
    assert config.exporter == "console"


def test_config_from_env_defaults_exporter_to_cleair_http(monkeypatch) -> None:
    monkeypatch.delenv("CLEAIR_EXPORTER", raising=False)
    config = CleairConfig.from_env()
    assert config.exporter == "cleair_http"
