import csv
import io
import zipfile
from pathlib import Path

import cv2
import numpy as np
import pytest

from app.processing import ProcessingError, ProcessingLimits, process_zip


def _encoded_image(*, sharp: bool) -> bytes:
    if sharp:
        grid = np.indices((80, 80)).sum(axis=0) % 2
        image = np.repeat((grid * 255).astype(np.uint8)[:, :, None], 3, axis=2)
    else:
        image = np.full((80, 80, 3), 127, dtype=np.uint8)
    success, encoded = cv2.imencode(".jpg", image)
    assert success
    return encoded.tobytes()


def _create_zip(path: Path, files: dict[str, bytes]) -> None:
    with zipfile.ZipFile(path, "w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)


def test_processes_filters_and_reindexes_in_natural_order(tmp_path: Path) -> None:
    source = tmp_path / "vistoria.zip"
    destination = tmp_path / "resultado.zip"
    _create_zip(
        source,
        {
            "fotos/foto_10.jpg": _encoded_image(sharp=True),
            "fotos/foto_2.jpg": _encoded_image(sharp=False),
            "fotos/foto_1.png": _encoded_image(sharp=True),
            "observacoes.txt": b"ignorar",
        },
    )

    result = process_zip(source, destination, threshold=100.0)

    assert result.accepted_count == 2
    assert result.rejected_count == 1
    assert [photo.original_name for photo in result.photos] == [
        "fotos/foto_1.png",
        "fotos/foto_2.jpg",
        "fotos/foto_10.jpg",
    ]
    assert [photo.output_name for photo in result.photos] == [
        "foto_001.png",
        None,
        "foto_002.jpg",
    ]

    with zipfile.ZipFile(destination) as output:
        assert output.namelist() == [
            "foto_001.png",
            "foto_002.jpg",
            "manifesto.csv",
        ]
        manifest = list(csv.DictReader(io.TextIOWrapper(output.open("manifesto.csv"))))
        assert [row["motivo"] for row in manifest] == [
            "aprovada",
            "abaixo_do_limiar",
            "aprovada",
        ]


def test_records_corrupted_supported_image_as_rejected(tmp_path: Path) -> None:
    source = tmp_path / "vistoria.zip"
    destination = tmp_path / "resultado.zip"
    _create_zip(source, {"foto_1.jpg": b"nao e uma imagem"})

    result = process_zip(source, destination)

    assert result.accepted_count == 0
    assert result.photos[0].reason == "imagem_invalida"
    with zipfile.ZipFile(destination) as output:
        assert output.namelist() == ["manifesto.csv"]


@pytest.mark.parametrize(
    ("files", "message"),
    [
        ({"leia-me.txt": b"texto"}, "não contém imagens"),
        ({"../foto.jpg": b"conteudo"}, "caminho inseguro"),
    ],
)
def test_rejects_invalid_archive_contents(
    tmp_path: Path, files: dict[str, bytes], message: str
) -> None:
    source = tmp_path / "vistoria.zip"
    _create_zip(source, files)

    with pytest.raises(ProcessingError, match=message):
        process_zip(source, tmp_path / "resultado.zip")


def test_rejects_archive_over_configured_size_limit(tmp_path: Path) -> None:
    source = tmp_path / "vistoria.zip"
    _create_zip(source, {"foto.jpg": _encoded_image(sharp=True)})

    with pytest.raises(ProcessingError, match="conteúdo descompactado"):
        process_zip(
            source,
            tmp_path / "resultado.zip",
            limits=ProcessingLimits(max_uncompressed_size=10),
        )


def test_rejects_invalid_zip(tmp_path: Path) -> None:
    source = tmp_path / "vistoria.zip"
    source.write_bytes(b"arquivo invalido")

    with pytest.raises(ProcessingError, match="não é um ZIP válido"):
        process_zip(source, tmp_path / "resultado.zip")
