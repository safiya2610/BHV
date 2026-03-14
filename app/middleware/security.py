from typing import Callable, Awaitable
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.requests import Request
from starlette.responses import Response, JSONResponse, PlainTextResponse
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
import os
import traceback


class SecurityHeadersMiddleware:
    """
    Adds common security headers to every response.
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - Referrer-Policy: no-referrer
    - Strict-Transport-Security: for HTTPS only (configurable)
    - Content-Security-Policy: strict default suitable for non-inline assets
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        enable_hsts: bool = True,
        csp: str | None = None,
    ) -> None:
        self.app = app
        self.enable_hsts = enable_hsts
        
        self.csp = csp or (
            "default-src 'self'; "
            "img-src 'self' data:; "
            "style-src 'self'; "
            "script-src 'self'"
        )

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_wrapper(message):
            if message.get("type") == "http.response.start":
                headers = message.setdefault("headers", [])

                def add_header(key: str, value: str):
                    headers.append((key.encode("latin-1"), value.encode("latin-1")))

                add_header("x-content-type-options", "nosniff")
                add_header("x-frame-options", "DENY")
                add_header("referrer-policy", "no-referrer")
                if self.csp:
                    add_header("content-security-policy", self.csp)

                # Only add HSTS if configured and likely HTTPS
                if self.enable_hsts:
                    # Trust environment hint to avoid forcing HSTS in dev
                    debug = os.getenv("DEBUG", "false").lower() in {"1", "true", "yes", "on"}
                    if not debug:
                        add_header("strict-transport-security", "max-age=31536000; includeSubDomains")

            await send(message)

        await self.app(scope, receive, send_wrapper)


def install_exception_handlers(app: FastAPI) -> None:
    """Register global exception handlers for consistent error responses and logging."""

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail or "HTTP error"},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=422,
            content={"detail": exc.errors()},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        # Do not leak internals; optionally log exc to server logs here
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )
