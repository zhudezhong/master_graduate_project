from fastapi import FastAPI
import uvicorn

from app.api.router import api_router
from app.core.config import settings
from app.infra.container import AppContainer


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, debug=settings.debug)
    app.state.container = AppContainer(settings)
    app.include_router(api_router, prefix=settings.api_prefix)

    @app.on_event("startup")
    async def _startup() -> None:
        app.state.container.start_background_jobs()

    @app.on_event("shutdown")
    async def _shutdown() -> None:
        app.state.container.stop_background_jobs()

    return app


app = create_app()


def main() -> None:
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )


if __name__ == "__main__":
    main()
