"""
Structured JSON logging via structlog.

Every log line is a JSON object — easy to ship to Grafana Loki, Datadog, etc.

Each HTTP request gets a unique request_id bound into the context so all log
lines for a single request are correlated even across concurrent requests.

Output format (one line per event):
    {
      "timestamp": "2026-05-30T12:00:00.123Z",
      "level": "info",
      "event": "request_completed",
      "request_id": "a1b2c3d4",
      "method": "GET",
      "path": "/marketplace/items",
      "status_code": 200,
      "duration_ms": 42.7,
      "user_id": "user_000002"   ← only if authenticated
    }
"""

import sys
import time
import uuid
import logging

import structlog
from fastapi import Request
from fastapi.responses import Response


def configure_logging(level: str = "INFO") -> None:
    shared_processors = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    structlog.configure(
        processors=shared_processors + [structlog.processors.JSONRenderer()],
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, level.upper(), logging.INFO)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(file=sys.stdout),
        cache_logger_on_first_use=True,
    )

    # Silence noisy stdlib loggers
    for noisy in ("uvicorn.access", "sqlalchemy.engine"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


async def request_logging_middleware(request: Request, call_next) -> Response:
    """
    Middleware: binds a request_id + route metadata into structlog contextvars
    so every log call within the request automatically includes them.
    Also logs request_started / request_completed with timing.
    """
    request_id = uuid.uuid4().hex[:8]
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(
        request_id=request_id,
        method=request.method,
        path=request.url.path,
    )

    # Bind user_id if JWT present (best-effort, don't fail the request)
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        try:
            from app.core.security import decode_access_token
            user_id = decode_access_token(auth_header[7:])
            if user_id:
                structlog.contextvars.bind_contextvars(user_id=user_id)
        except Exception:
            pass

    log = structlog.get_logger()
    log.info("request_started")

    t0 = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - t0) * 1000, 2)

    log.info("request_completed", status_code=response.status_code, duration_ms=duration_ms)
    response.headers["X-Request-ID"] = request_id
    return response
