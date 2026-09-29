import io
import zipfile

import cv2
import numpy as np
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def _image_bytes() -> bytes:
    grid = np.indices((40, 40)).sum(axis=0) % 2
    image = np.repeat((grid * 255).astype(np.uint8)[:, :, None], 3, axis=2)
    success, encoded = cv2.imencode(".jpg", image)
    assert success
    return encoded.tobytes()


def _archive_bytes() -> bytes:
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w") as archive:
        archive.writestr("foto_1.jpg", _image_bytes())
    return output.getvalue()


def test_process_endpoint_returns_filtered_zip() -> None:
    client = TestClient(create_app(Settings(sharpness_threshold=100.0)))

    response = client.post(
        "/api/process",
        files={"archive": ("vistoria.zip", _archive_bytes(), "application/zip")},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    assert response.headers["x-photos-accepted"] == "1"
    assert response.headers["x-photos-rejected"] == "0"
    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        assert archive.namelist() == ["foto_001.jpg", "manifesto.csv"]


def test_process_endpoint_accepts_threshold_override() -> None:
    client = TestClient(create_app(Settings(sharpness_threshold=999_999.0)))

    response = client.post(
        "/api/process",
        data={"threshold": "100"},
        files={"archive": ("vistoria.zip", _archive_bytes(), "application/zip")},
    )

    assert response.status_code == 200
    assert response.headers["x-photos-accepted"] == "1"
    assert response.headers["x-sharpness-threshold"] == "100.0"


def test_process_endpoint_rejects_non_zip_filename() -> None:
    response = TestClient(create_app()).post(
        "/api/process",
        files={"archive": ("foto.jpg", b"conteudo", "image/jpeg")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Envie um arquivo com extensão .zip."


def test_process_endpoint_rejects_upload_over_limit() -> None:
    client = TestClient(create_app(Settings(max_upload_size=10)))

    response = client.post(
        "/api/process",
        files={"archive": ("vistoria.zip", _archive_bytes(), "application/zip")},
    )

    assert response.status_code == 413
    assert "limite de upload" in response.json()["detail"]


def test_process_endpoint_reports_invalid_zip() -> None:
    response = TestClient(create_app()).post(
        "/api/process",
        files={"archive": ("vistoria.zip", b"invalido", "application/zip")},
    )

    assert response.status_code == 400
    assert "não é um ZIP válido" in response.json()["detail"]

