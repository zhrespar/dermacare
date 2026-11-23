from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.routes import account, analysis, explanations, health, recommendations, system
from app.core.config import get_settings


def create_app() -> FastAPI:
    s = get_settings()
    app = FastAPI(title=s.app_name, version=__version__)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=s.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(account.router, prefix=s.api_v1_prefix)
    app.include_router(analysis.router, prefix=s.api_v1_prefix)
    app.include_router(recommendations.router, prefix=s.api_v1_prefix)
    app.include_router(explanations.router, prefix=s.api_v1_prefix)
    app.include_router(system.router, prefix=s.api_v1_prefix)
    return app


app = create_app()
