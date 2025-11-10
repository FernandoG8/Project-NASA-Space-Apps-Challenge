"""Custom exception handlers that enforce the response envelope."""
from __future__ import annotations

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.schemas.response import ErrorItem, envelope


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        detail = exc.detail
        message = "Error"
        errors = None
        if isinstance(detail, dict):
            message = detail.get("message", "Error")
            raw_errors = detail.get("errors")
            if raw_errors:
                errors = [
                    e if isinstance(e, ErrorItem) else ErrorItem(error=str(e))
                    for e in raw_errors
                ]
        elif isinstance(detail, str):
            message = detail
        return JSONResponse(
            status_code=exc.status_code,
            content=envelope(success=False, message=message, errors=errors),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        items = [
            ErrorItem(
                field=".".join(str(loc) for loc in err["loc"][1:]),
                error=err["msg"],
            )
            for err in exc.errors()
        ]
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=envelope(
                success=False,
                message="Solicitud inválida",
                errors=items,
            ),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=envelope(
                success=False,
                message="Error interno del servidor",
            ),
        )


__all__ = ["register_exception_handlers"]
