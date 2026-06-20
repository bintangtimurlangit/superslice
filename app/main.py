"""SuperSlice API - application factory.

Wires together configuration, middleware, and routes. The slicing logic lives
in :mod:`app.slicer` and the HTTP endpoints in :mod:`app.routes`.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import API_TITLE, API_DESCRIPTION, API_VERSION, CORS_ORIGINS
from .routes import router


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    app = FastAPI(
        title=API_TITLE,
        description=API_DESCRIPTION,
        version=API_VERSION,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)
    return app


app = create_app()
