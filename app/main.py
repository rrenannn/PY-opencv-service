from fastapi import FastAPI

from app.api import router
from app.config import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    app = FastAPI(
        title="Serviço de filtragem de fotos de vistoria",
        version="0.1.0",
    )
    app.state.settings = settings or Settings.from_env()
    app.include_router(router)

    @app.get("/health", tags=["infraestrutura"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
