"""SuperSlice API - application factory.

Wires together configuration, middleware, error handling, and routes. The
slicing logic lives in :mod:`app.services` / :mod:`app.slicer` and the HTTP
endpoints in :mod:`app.routes`.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router
from .config import API_DESCRIPTION, API_TITLE, API_VERSION, CORS_ORIGINS
from .core.errors import register_error_handlers
from .services import history
from .services.slicing import sweep_work_dirs


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown housekeeping."""
    sweep_work_dirs()  # clear orphaned files left by a previous crash
    history.init()      # no-op unless HISTORY_ENABLED
    yield


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    app = FastAPI(
        title=API_TITLE,
        description=API_DESCRIPTION,
        version=API_VERSION,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_error_handlers(app)
    app.include_router(router)
    return app


app = create_app()
