
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """Registra los manejadores globales de excepciones."""

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request,
        exc: StarletteHTTPException,
    ):
        logger.warning(
            "Error HTTP %s | método=%s | ruta=%s | detalle=%s",
            exc.status_code,
            request.method,
            request.url.path,
            exc.detail,
        )

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "http_error",
                "message": str(exc.detail),
                "path": request.url.path,
            },
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ):
        errores = exc.errors()

        # Registrar los errores sin exponer datos innecesarios
        logger.warning(
            "Error de validación | método=%s | ruta=%s | errores=%s",
            request.method,
            request.url.path,
            [
                {
                    "campo": error.get("loc"),
                    "tipo": error.get("type"),
                    "mensaje": error.get("msg"),
                }
                for error in errores
            ],
        )

        # Excluir ctx evita serializar objetos como ValueError.
        detalles = jsonable_encoder(
            errores,
            exclude={"ctx"},
        )

        return JSONResponse(
            status_code=422,
            content={
                "error": "validation_error",
                "message": "Los datos enviados no son válidos.",
                "details": detalles,
                "path": request.url.path,
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request,
        exc: Exception,
    ):
        logger.error(
            "Error interno | método=%s | ruta=%s | tipo=%s | detalle=%s",
            request.method,
            request.url.path,
            type(exc).__name__,
            str(exc),
            exc_info=(type(exc), exc, exc.__traceback__),
        )

        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_server_error",
                "message": "Ocurrió un error interno en el servidor.",
                "path": request.url.path,
            },
        )
