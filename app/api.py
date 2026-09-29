from __future__ import annotations

import shutil
import tempfile
from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from app.config import Settings
from app.processing import ProcessingError, process_zip

router = APIRouter(prefix="/api", tags=["processamento"])
UPLOAD_CHUNK_SIZE = 1024 * 1024


@router.post("/process", response_class=FileResponse)
async def process_photos(
    request: Request,
    archive: Annotated[UploadFile, File(description="Arquivo ZIP com as fotos")],
    threshold: Annotated[float | None, Form(ge=0)] = None,
) -> FileResponse:
    settings: Settings = request.app.state.settings
    if not archive.filename or Path(archive.filename).suffix.casefold() != ".zip":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Envie um arquivo com extensão .zip.",
        )

    work_dir = Path(tempfile.mkdtemp(prefix="vistoria-"))
    source = work_dir / "entrada.zip"
    destination = work_dir / "fotos_filtradas.zip"

    try:
        await _save_upload(archive, source, settings.max_upload_size)
        selected_threshold = (
            settings.sharpness_threshold if threshold is None else threshold
        )
        result = await run_in_threadpool(
            process_zip,
            source,
            destination,
            threshold=selected_threshold,
        )
    except HTTPException:
        shutil.rmtree(work_dir, ignore_errors=True)
        raise
    except ProcessingError as exc:
        shutil.rmtree(work_dir, ignore_errors=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    except Exception:
        shutil.rmtree(work_dir, ignore_errors=True)
        raise
    finally:
        await archive.close()

    return FileResponse(
        destination,
        media_type="application/zip",
        filename="fotos_filtradas.zip",
        headers={
            "X-Photos-Accepted": str(result.accepted_count),
            "X-Photos-Rejected": str(result.rejected_count),
            "X-Sharpness-Threshold": str(selected_threshold),
        },
        background=BackgroundTask(shutil.rmtree, work_dir, ignore_errors=True),
    )


async def _save_upload(upload: UploadFile, destination: Path, max_size: int) -> None:
    total_size = 0
    with destination.open("wb") as output:
        while chunk := await upload.read(UPLOAD_CHUNK_SIZE):
            total_size += len(chunk)
            if total_size > max_size:
                raise HTTPException(
                    status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                    detail="O arquivo excede o limite de upload permitido.",
                )
            output.write(chunk)
