from fastapi.testclient import TestClient

from gateway.main import app


def test_health() -> None:
    client = TestClient(app)
    response = client.get("/health/live")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
