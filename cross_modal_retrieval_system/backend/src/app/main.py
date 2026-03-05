from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import get_settings
from app.infra.container import AppContainer


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, debug=settings.debug)
    app.state.container = AppContainer(settings)
    app.include_router(api_router, prefix=settings.api_prefix)
    return app


app = create_app()
