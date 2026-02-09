from fastapi.testclient import TestClient

from gateway.main import app


class DummyTask:
    id = "job-123"


def test_submit_inference_returns_job_id(monkeypatch) -> None:
    client = TestClient(app)

    def fake_delay(*, model_name: str, prompt: str, provider: str) -> DummyTask:
        assert model_name == "gpt-4.1-mini"
        assert prompt == "hello"
        assert provider == "mock"
        return DummyTask()

    monkeypatch.setattr("gateway.main.run_inference_task.delay", fake_delay)

    response = client.post(
        "/inferences",
        json={
            "model_name": "gpt-4.1-mini",
            "prompt": "hello",
            "provider": "mock",
        },
    )

    assert response.status_code == 202
    assert response.json() == {"job_id": "job-123", "status": "queued"}
