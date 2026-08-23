import logging
import time
import uuid
from collections import defaultdict, deque
from collections.abc import Callable
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import actions, auth, chats, sources, system
from app.config import get_settings
from app.observability import configure_logging


settings = get_settings()
configure_logging(settings)
logger = logging.getLogger("parcelpilot")

app = FastAPI(
    title="ParcelPilot Support API",
    version="0.1.0",
    docs_url="/api/docs" if settings.app_env != "production" else None,
    redoc_url=None,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-Request-ID"],
)


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self.events: dict[str, deque[float]] = defaultdict(deque)

    @staticmethod
    def parse(spec: str) -> tuple[int, int]:
        count_raw, period = spec.split("/", 1)
        seconds = {"second": 1, "minute": 60, "hour": 3600}.get(period.rstrip("s"), 60)
        return int(count_raw), seconds

    def allow(self, key: str, spec: str) -> bool:
        limit, window = self.parse(spec)
        now = time.monotonic()
        queue = self.events[key]
        while queue and queue[0] <= now - window:
            queue.popleft()
        if len(queue) >= limit:
            return False
        queue.append(now)
        return True


rate_limiter = InMemoryRateLimiter()


@app.middleware("http")
async def request_context(request: Request, call_next: Callable[..., Any]):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    origin = request.headers.get("origin")
    if request.method in {"POST", "PUT", "PATCH", "DELETE"} and origin:
        if origin not in settings.allowed_origins:
            return JSONResponse(
                status_code=403,
                content={
                    "code": "INVALID_ORIGIN",
                    "message": "Request origin is not allowed",
                    "requestId": request_id,
                    "retryable": False,
                },
            )
    client_ip = request.client.host if request.client else "unknown"
    rate_spec = None
    if request.url.path.endswith("/auth/login"):
        rate_spec = settings.rate_limit_login
    elif request.url.path.endswith("/messages"):
        rate_spec = settings.rate_limit_chat
    if rate_spec and not rate_limiter.allow(f"{client_ip}:{request.url.path}", rate_spec):
        return JSONResponse(
            status_code=429,
            content={
                "code": "RATE_LIMITED",
                "message": "Too many requests. Please try again shortly.",
                "requestId": request_id,
                "retryable": True,
            },
        )
    started = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "request.completed",
        extra={
            "request_id": request_id,
            "duration_ms": int((time.perf_counter() - started) * 1000),
            "outcome": response.status_code,
        },
    )
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    code = {
        401: "UNAUTHENTICATED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        429: "RATE_LIMITED",
        503: "DEPENDENCY_UNAVAILABLE",
    }.get(exc.status_code, "REQUEST_ERROR")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "code": code,
            "message": str(exc.detail),
            "requestId": request.state.request_id,
            "retryable": exc.status_code in {429, 503},
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "code": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "requestId": request.state.request_id,
            "retryable": False,
            "fieldErrors": [
                {"location": list(error["loc"]), "message": error["msg"]} for error in exc.errors()
            ],
        },
    )


@app.exception_handler(Exception)
async def unexpected_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("request.failed", extra={"request_id": request.state.request_id})
    return JSONResponse(
        status_code=500,
        content={
            "code": "INTERNAL_ERROR",
            "message": "An unexpected error occurred",
            "requestId": request.state.request_id,
            "retryable": True,
        },
    )


app.include_router(auth.router, prefix="/api/v1")
app.include_router(chats.router, prefix="/api/v1")
app.include_router(actions.router, prefix="/api/v1")
app.include_router(sources.router, prefix="/api/v1")
app.include_router(system.router, prefix="/api/v1")

