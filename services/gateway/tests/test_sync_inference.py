from fastapi.testclient import TestClient

from gateway.main import app


class DummyTask:
    id = "llmshap-123"


def test_sync_inference_fast_returns_response_and_attribution(monkeypatch) -> None:
    client = TestClient(app)

    def fake_run_provider_inference(*, model_name: str, prompt: str, provider: str) -> dict:
        assert model_name == "gpt-4.1-mini"
        assert prompt == "hello world"
        assert provider == "openai"
        return {"provider": provider, "model_name": model_name, "echo": "output text"}

    def fake_run_llmshap_attribution(
        *,
        prompt: str,
        provider: str,
        model_name: str,
    ) -> dict:
        assert prompt == "hello world"
        assert provider == "openai"
        assert model_name == "gpt-4.1-mini"
        return {
            "result": {"attribution": {"0": 1.0}, "output": "output text"},
            "attribution_meta": {
                "status": "complete",
                "method": "llmshap",
                "latency_ms": 2,
            },
        }

    monkeypatch.setattr("gateway.main.run_provider_inference", fake_run_provider_inference)
    monkeypatch.setattr("gateway.main.run_llmshap_attribution", fake_run_llmshap_attribution)

    response = client.post(
        "/v1/inference",
        json={
            "model_name": "gpt-4.1-mini",
            "prompt": "hello world",
            "provider": "openai",
            "attribution": {"delivery_mode": "fast"},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["request_id"]
    assert payload["response"]["echo"] == "output text"
    assert payload["attribution"]["output"] == "output text"
    assert payload["attribution_meta"]["status"] == "complete"
    assert payload["attribution_meta"]["quality"] is None


def test_sync_inference_deferred_queues_llmshap(monkeypatch) -> None:
    client = TestClient(app)

    def fake_run_provider_inference(*, model_name: str, prompt: str, provider: str) -> dict:
        return {"provider": provider, "model_name": model_name, "echo": prompt}

    def fake_delay(
        *,
        request_id: str,
        prompt: str,
        provider: str,
        model_name: str,
    ) -> DummyTask:
        assert request_id
        assert prompt == "hello"
        assert provider == "openai"
        assert model_name == "gpt-4.1-mini"
        return DummyTask()

    monkeypatch.setattr("gateway.main.run_provider_inference", fake_run_provider_inference)
    monkeypatch.setattr("gateway.main.run_llmshap_task.delay", fake_delay)

    response = client.post(
        "/v1/inference",
        json={
            "model_name": "gpt-4.1-mini",
            "prompt": "hello",
            "provider": "openai",
            "attribution": {"delivery_mode": "deferred"},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["request_id"]
    assert payload["response"]["echo"] == "hello"
    assert payload["attribution"] is None
    assert payload["attribution_meta"]["status"] == "queued"
    assert payload["attribution_meta"]["quality"] == "deferred"
    assert payload["attribution_meta"]["job_id"] == "llmshap-123"


def test_sync_inference_rejects_unsupported_provider() -> None:
    client = TestClient(app)

    response = client.post(
        "/v1/inference",
        json={
            "model_name": "gpt-4.1-mini",
            "prompt": "hello",
            "provider": "mock",
            "attribution": {"delivery_mode": "fast"},
        },
    )

    assert response.status_code == 422
