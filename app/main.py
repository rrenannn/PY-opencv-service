from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import router
from app.config import Settings

STATIC_DIR = Path(__file__).parent / "static"


def create_app(settings: Settings | None = None) -> FastAPI:
    app = FastAPI(
        title="Serviço de filtragem de fotos de vistoria",
        version="0.1.0",
    )
    app.state.settings = settings or Settings.from_env()
    app.include_router(router)
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/", include_in_schema=False)
    async def home() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/health", tags=["infraestrutura"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
