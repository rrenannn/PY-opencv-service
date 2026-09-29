import re

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
    assert 'id="root"' in response.text
    asset_path = re.search(r'src="(/static/assets/[^\"]+\.js)"', response.text)
    assert asset_path is not None
    assert client.get(asset_path.group(1)).status_code == 200
