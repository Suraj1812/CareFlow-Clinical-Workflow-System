import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger("careflow.errors")


class DomainError(Exception):
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class IdempotencyConflict(DomainError):
    def __init__(self) -> None:
        super().__init__(
            "Idempotency-Key was already used with a different request body.",
            status.HTTP_409_CONFLICT,
        )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        errors = jsonable_encoder(exc.errors())
        logger.warning(
            "validation_error",
            extra={"path": request.url.path, "errors": errors},
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": errors, "error": "validation_error"},
        )

    @app.exception_handler(DomainError)
    async def domain_exception_handler(request: Request, exc: DomainError):
        logger.warning(
            "domain_error",
            extra={"path": request.url.path, "message": exc.message},
        )
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    @app.exception_handler(SQLAlchemyError)
    async def database_exception_handler(request: Request, exc: SQLAlchemyError):
        logger.exception("database_error", extra={"path": request.url.path})
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "A database error occurred."},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("unhandled_error", extra={"path": request.url.path})
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "An unexpected server error occurred."},
        )
