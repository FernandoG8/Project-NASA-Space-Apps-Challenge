"""Common response envelopes used across the API."""
from __future__ import annotations

from typing import Any, Generic, Optional, Sequence, TypeVar

from pydantic import BaseModel, Field


class ErrorItem(BaseModel):
    field: Optional[str] = Field(default=None, description="Campo relacionado al error")
    error: str = Field(..., description="Descripción del error")


DataT = TypeVar("DataT")


class BaseResponse(BaseModel, Generic[DataT]):
    success: bool = Field(..., description="Indica si la operación fue exitosa")
    message: str = Field(..., description="Mensaje descriptivo de la operación")
    data: Optional[DataT] = Field(default=None, description="Payload de la respuesta")
    errors: Optional[Sequence[ErrorItem]] = Field(
        default=None, description="Lista de errores asociados"
    )


class EmptyResponse(BaseResponse[None]):
    """Respuesta sin datos en el payload."""


def envelope(
    *, success: bool, message: str, data: Any | None = None, errors: Sequence[ErrorItem | str] | None = None
) -> dict[str, Any]:
    """Helper to generate response envelopes consistently."""
    normalized_errors: Sequence[ErrorItem] | None = None
    if errors:
        normalized_errors = [
            e if isinstance(e, ErrorItem) else ErrorItem(error=str(e))
            for e in errors
        ]
    return BaseResponse[Any](
        success=success,
        message=message,
        data=data,
        errors=normalized_errors,
    ).model_dump()
