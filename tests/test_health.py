from fastapi.testclient import TestClient

from app.main import app


def test_health_check() -> None:
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_home_page_loads_frontend() -> None:
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert "Separe as fotos nítidas" in response.text
    assert client.get("/static/app.js").status_code == 200
