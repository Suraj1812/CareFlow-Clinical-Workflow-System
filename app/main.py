from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import Settings, get_settings
from app.database.init_db import init_db
from app.database.session import configure_database
from app.routes import advisories, alerts, health, responses, schedules, ui
from app.utils.errors import register_exception_handlers
from app.utils.logging import configure_logging, request_logging_middleware


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)
    configure_database(settings.database_url)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        init_db()
        yield

    application = FastAPI(
        title="CareFlow Clinical Workflow System",
        description=(
            "A deterministic internal healthcare workflow backend for advisory "
            "publication, schedule generation, response ingestion, alerts, and audit traceability."
        ),
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    application.state.settings = settings
    application.mount("/static", StaticFiles(directory="app/static"), name="static")

    register_exception_handlers(application)
    application.middleware("http")(request_logging_middleware)

    application.include_router(health.router)
    application.include_router(advisories.router)
    application.include_router(schedules.router)
    application.include_router(responses.router)
    application.include_router(alerts.router)
    application.include_router(ui.router)

    return application


app = create_app()

