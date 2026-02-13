import pytest

from gateway.tasks import run_llmshap_task


def test_run_llmshap_task_raises_on_failed_attribution(monkeypatch) -> None:
    def fake_run_llmshap_attribution(*, prompt: str, provider: str, model_name: str) -> dict:
        assert prompt == "hello"
        assert provider == "openai"
        assert model_name == "gpt-4.1-mini"
        return {
            "result": None,
            "attribution_meta": {
                "status": "failed",
                "method": "llmshap",
                "latency_ms": 1,
                "error": "boom",
            },
        }

    monkeypatch.setattr("gateway.tasks.run_llmshap_attribution", fake_run_llmshap_attribution)

    with pytest.raises(RuntimeError, match="boom"):
        run_llmshap_task(
            request_id="req-1",
            prompt="hello",
            provider="openai",
            model_name="gpt-4.1-mini",
        )
