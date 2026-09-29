from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(
        title="Serviço de filtragem de fotos de vistoria",
        version="0.1.0",
    )

    @app.get("/health", tags=["infraestrutura"])
    async def health_check() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()

