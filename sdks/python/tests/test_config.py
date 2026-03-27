from __future__ import annotations

import pytest

from cleair._config import CleairConfig, DEFAULT_CLEAIR_HTTP_ENDPOINT


def test_config_from_env_defaults_terminal_stream_to_false(monkeypatch) -> None:
    monkeypatch.delenv("CLEAIR_TERMINAL_STREAM", raising=False)
    config = CleairConfig.from_env()
    assert config.terminal_stream is False


def test_config_from_env_defaults_cleair_http_endpoint_to_hosted_api(monkeypatch) -> None:
    monkeypatch.delenv("CLEAIR_HTTP_ENDPOINT", raising=False)
    config = CleairConfig.from_env()
    assert config.cleair_http_endpoint == DEFAULT_CLEAIR_HTTP_ENDPOINT


def test_config_from_env_does_not_read_cleair_api_key(monkeypatch) -> None:
    monkeypatch.setenv("CLEAIR_API_KEY", "test-key")
    config = CleairConfig.from_env()
    assert config.cleair_api_key is None


def test_config_from_env_parses_terminal_stream_true(monkeypatch) -> None:
    monkeypatch.setenv("CLEAIR_TERMINAL_STREAM", "true")
    config = CleairConfig.from_env()
    assert config.terminal_stream is True


@pytest.mark.parametrize("value", ["1", "yes", "on", "TRUE", "  True  "])
def test_env_bool_truthy_variants(value) -> None:
    assert CleairConfig._env_bool("FAKE", default=False) is False  # baseline
    import os
    os.environ["FAKE"] = value
    try: assert CleairConfig._env_bool("FAKE") is True
    finally: del os.environ["FAKE"]


def test_env_bool_falsy_values() -> None:
    import os
    for value in ["0", "false", "no", "off", "random"]:
        os.environ["FAKE"] = value
        assert CleairConfig._env_bool("FAKE") is False
    del os.environ["FAKE"]


def test_config_from_env_reads_all_env_vars(monkeypatch) -> None:
    monkeypatch.setenv("OTEL_SERVICE_NAME", "my-svc")
    monkeypatch.setenv("CLEAIR_EXPORTER", "console")
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_TRACES_ENDPOINT", "http://example.com/traces")
    monkeypatch.setenv("CLEAIR_TERMINAL_STREAM", "1")

    config = CleairConfig.from_env()

    assert config.service_name == "my-svc"
    assert config.exporter == "console"
    assert config.otlp_http_endpoint == "http://example.com/traces"
    assert config.terminal_stream is True


def test_config_from_env_defaults_exporter_to_cleair_http(monkeypatch) -> None:
    monkeypatch.delenv("CLEAIR_EXPORTER", raising=False)
    config = CleairConfig.from_env()
    assert config.exporter == "cleair_http"
