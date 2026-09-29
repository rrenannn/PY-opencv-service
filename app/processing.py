from __future__ import annotations

import csv
import io
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

import cv2
import numpy as np

SUPPORTED_EXTENSIONS = {".jpeg", ".jpg", ".png"}
DEFAULT_SHARPNESS_THRESHOLD = 100.0
DEFAULT_MAX_FILES = 1_000
DEFAULT_MAX_FILE_SIZE = 25 * 1024 * 1024
DEFAULT_MAX_UNCOMPRESSED_SIZE = 500 * 1024 * 1024
DEFAULT_MAX_COMPRESSION_RATIO = 100.0


class ProcessingError(ValueError):
    """Erro esperado durante a validação ou o processamento de um pacote."""


@dataclass(frozen=True)
class ProcessingLimits:
    max_files: int = DEFAULT_MAX_FILES
    max_file_size: int = DEFAULT_MAX_FILE_SIZE
    max_uncompressed_size: int = DEFAULT_MAX_UNCOMPRESSED_SIZE
    max_compression_ratio: float = DEFAULT_MAX_COMPRESSION_RATIO


@dataclass(frozen=True)
class PhotoResult:
    original_name: str
    output_name: str | None
    sharpness: float | None
    accepted: bool
    reason: str


@dataclass(frozen=True)
class ProcessingResult:
    photos: tuple[PhotoResult, ...]

    @property
    def accepted_count(self) -> int:
        return sum(photo.accepted for photo in self.photos)

    @property
    def rejected_count(self) -> int:
        return len(self.photos) - self.accepted_count


def natural_sort_key(name: str) -> tuple[tuple[int, int | str], ...]:
    """Cria uma chave que ordena foto_2 antes de foto_10."""
    parts = re.split(r"(\d+)", name.casefold())
    return tuple(
        (0, int(part)) if part.isdigit() else (1, part) for part in parts if part
    )


def calculate_sharpness(image: np.ndarray) -> float:
    if image.size == 0:
        raise ProcessingError("A imagem está vazia.")
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def process_zip(
    source: Path,
    destination: Path,
    *,
    threshold: float = DEFAULT_SHARPNESS_THRESHOLD,
    limits: ProcessingLimits | None = None,
) -> ProcessingResult:
    if threshold < 0:
        raise ProcessingError("O limiar de nitidez não pode ser negativo.")

    active_limits = limits or ProcessingLimits()
    try:
        with zipfile.ZipFile(source, "r") as input_zip:
            members = _validated_image_members(input_zip, active_limits)
            photos = _analyse_photos(input_zip, members, threshold)
            _write_result_zip(input_zip, members, photos, destination)
    except zipfile.BadZipFile as exc:
        raise ProcessingError("O arquivo enviado não é um ZIP válido.") from exc

    return ProcessingResult(tuple(photos))


def _validated_image_members(
    archive: zipfile.ZipFile, limits: ProcessingLimits
) -> list[zipfile.ZipInfo]:
    files = [member for member in archive.infolist() if not member.is_dir()]
    if len(files) > limits.max_files:
        raise ProcessingError(f"O ZIP excede o limite de {limits.max_files} arquivos.")

    total_size = sum(member.file_size for member in files)
    if total_size > limits.max_uncompressed_size:
        raise ProcessingError("O conteúdo descompactado excede o limite permitido.")

    for member in files:
        _validate_member_path(member.filename)
        if member.file_size > limits.max_file_size:
            raise ProcessingError(f"O arquivo {member.filename!r} excede o limite.")
        if member.file_size and member.compress_size == 0:
            raise ProcessingError(
                f"O arquivo {member.filename!r} tem compressão inválida."
            )
        if member.compress_size:
            ratio = member.file_size / member.compress_size
            if ratio > limits.max_compression_ratio:
                raise ProcessingError(
                    f"O arquivo {member.filename!r} excede a taxa de compressão segura."
                )

    images = [
        member
        for member in files
        if PurePosixPath(member.filename).suffix.casefold() in SUPPORTED_EXTENSIONS
        and "__MACOSX" not in PurePosixPath(member.filename).parts
    ]
    if not images:
        raise ProcessingError("O ZIP não contém imagens JPEG ou PNG.")
    return sorted(images, key=lambda member: natural_sort_key(member.filename))


def _validate_member_path(filename: str) -> None:
    path = PurePosixPath(filename)
    if path.is_absolute() or ".." in path.parts or "\\" in filename:
        raise ProcessingError(f"O ZIP contém um caminho inseguro: {filename!r}.")


def _analyse_photos(
    archive: zipfile.ZipFile,
    members: list[zipfile.ZipInfo],
    threshold: float,
) -> list[PhotoResult]:
    photos: list[PhotoResult] = []
    next_index = 1

    for member in members:
        raw_image = archive.read(member)
        image = cv2.imdecode(np.frombuffer(raw_image, dtype=np.uint8), cv2.IMREAD_COLOR)
        if image is None:
            photos.append(
                PhotoResult(member.filename, None, None, False, "imagem_invalida")
            )
            continue

        sharpness = calculate_sharpness(image)
        accepted = sharpness >= threshold
        output_name = None
        reason = "abaixo_do_limiar"
        if accepted:
            suffix = PurePosixPath(member.filename).suffix.casefold()
            suffix = ".jpg" if suffix == ".jpeg" else suffix
            output_name = f"foto_{next_index:03d}{suffix}"
            next_index += 1
            reason = "aprovada"

        photos.append(
            PhotoResult(
                original_name=member.filename,
                output_name=output_name,
                sharpness=sharpness,
                accepted=accepted,
                reason=reason,
            )
        )

    return photos


def _write_result_zip(
    input_zip: zipfile.ZipFile,
    members: list[zipfile.ZipInfo],
    photos: list[PhotoResult],
    destination: Path,
) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    members_by_name = {member.filename: member for member in members}
    with zipfile.ZipFile(
        destination, "w", compression=zipfile.ZIP_DEFLATED
    ) as output_zip:
        for photo in photos:
            if photo.accepted and photo.output_name:
                output_zip.writestr(
                    photo.output_name,
                    input_zip.read(members_by_name[photo.original_name]),
                )
        output_zip.writestr("manifesto.csv", _build_manifest(photos))


def _build_manifest(photos: list[PhotoResult]) -> str:
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(
        ["nome_original", "novo_nome", "nitidez", "aprovada", "motivo"]
    )
    for photo in photos:
        writer.writerow(
            [
                photo.original_name,
                photo.output_name or "",
                f"{photo.sharpness:.4f}" if photo.sharpness is not None else "",
                "sim" if photo.accepted else "nao",
                photo.reason,
            ]
        )
    return output.getvalue()
