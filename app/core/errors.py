"""Structured error responses.

Every error is returned as a consistent envelope:

    {"detail": "<message>", "error": {"code": "<CODE>", "message": "<message>"}}

`detail` is kept for backward compatibility; `error.code` is the stable,
machine-readable identifier consumers should branch on.
"""
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.requests import Request

# Default code per status, used when an HTTPException carries no explicit code.
_DEFAULT_CODES = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    408: "SLICE_TIMEOUT",
    413: "FILE_TOO_LARGE",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMITED",
    500: "INTERNAL_ERROR",
    503: "SERVICE_UNAVAILABLE",
}


class APIError(HTTPException):
    """An HTTPException that carries a machine-readable error code."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        headers: Optional[dict] = None,
    ):
        super().__init__(status_code=status_code, detail=message, headers=headers)
        self.code = code


def _envelope(detail, code: str) -> dict:
    return {"detail": detail, "error": {"code": code, "message": detail if isinstance(detail, str) else None}}


async def _http_exception_handler(request: Request, exc: HTTPException):
    code = getattr(exc, "code", None) or _DEFAULT_CODES.get(exc.status_code, "ERROR")
    return JSONResponse(
        status_code=exc.status_code,
        content=_envelope(exc.detail, code),
        headers=getattr(exc, "headers", None),
    )


async def _validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "error": {"code": "VALIDATION_ERROR", "message": "Request validation failed"},
        },
    )


def register_error_handlers(app: FastAPI) -> None:
    """Wire the structured handlers onto the app."""
    app.add_exception_handler(HTTPException, _http_exception_handler)
    app.add_exception_handler(RequestValidationError, _validation_exception_handler)
