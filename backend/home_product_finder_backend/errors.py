"""Uniform error responses for the public API."""
from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException


def install_error_handlers(app: FastAPI) -> None:
    """Install the family-standard error envelope without dropping ``detail``.

    ``detail`` is deliberately retained because existing HomeProductFinder
    clients already use FastAPI's original error payload.
    """

    @app.exception_handler(HTTPException)
    async def http_exception_handler(
        request: Request, exc: HTTPException,
    ) -> JSONResponse:
        del request
        if exc.status_code == 404:
            code = "not_found"
            message = "Risorsa non trovata."
        else:
            code = f"http_{exc.status_code}"
            message = _http_message(exc.detail)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {"code": code, "message": message, "field": None},
                "detail": exc.detail,
            },
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError,
    ) -> JSONResponse:
        del request
        errors = exc.errors()
        first = errors[0] if errors else {}
        loc = first.get("loc", ())
        field = str(loc[-1]) if loc else None
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "validation_error",
                    "message": "I dati inviati non sono validi.",
                    "field": field,
                },
                "detail": errors,
            },
        )


def _http_message(detail: Any) -> str:
    """Use an existing textual detail when available, otherwise a clear fallback."""
    if isinstance(detail, str):
        return detail
    return "La richiesta non può essere completata."
