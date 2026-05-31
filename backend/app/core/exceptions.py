"""
Hierarchical exception system for ElectroHub.

Hierarchy:
    ElectroHubException          ← base; all app errors derive from this
    ├── AuthException            ← 401 family
    │   ├── InvalidCredentialsException
    │   └── TokenExpiredException
    ├── ForbiddenException       ← 403 (authenticated but not allowed)
    ├── NotFoundException        ← 404
    ├── ConflictException        ← 409 (duplicate resource)
    ├── ValidationException      ← 422 (bad input beyond Pydantic)
    ├── RateLimitException       ← 429
    └── ServiceException         ← 503 (DB down, Redis down, email failed)
        ├── DatabaseException
        └── CacheException

FastAPI exception handlers are registered at the bottom and wired in main.py.
"""

import structlog
from fastapi import Request
from fastapi.responses import JSONResponse

log = structlog.get_logger()


# ── Base ─────────────────────────────────────────────────────────────────── #

class ElectroHubException(Exception):
    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


# ── Auth (401) ────────────────────────────────────────────────────────────── #

class AuthException(ElectroHubException):
    status_code = 401
    error_code = "AUTH_ERROR"


class InvalidCredentialsException(AuthException):
    error_code = "INVALID_CREDENTIALS"


class TokenExpiredException(AuthException):
    error_code = "TOKEN_EXPIRED"


class TokenMissingException(AuthException):
    error_code = "TOKEN_MISSING"


# ── Forbidden (403) ───────────────────────────────────────────────────────── #

class ForbiddenException(ElectroHubException):
    status_code = 403
    error_code = "FORBIDDEN"


# ── Not Found (404) ───────────────────────────────────────────────────────── #

class NotFoundException(ElectroHubException):
    status_code = 404
    error_code = "NOT_FOUND"


class ItemNotFoundException(NotFoundException):
    error_code = "ITEM_NOT_FOUND"


class UserNotFoundException(NotFoundException):
    error_code = "USER_NOT_FOUND"


# ── Conflict (409) ────────────────────────────────────────────────────────── #

class ConflictException(ElectroHubException):
    status_code = 409
    error_code = "CONFLICT"


class DuplicateEmailException(ConflictException):
    error_code = "EMAIL_ALREADY_EXISTS"


# ── Validation (422) ─────────────────────────────────────────────────────── #

class ValidationException(ElectroHubException):
    status_code = 422
    error_code = "VALIDATION_ERROR"


# ── Rate Limit (429) ─────────────────────────────────────────────────────── #

class RateLimitException(ElectroHubException):
    status_code = 429
    error_code = "RATE_LIMITED"

    def __init__(self, message: str, retry_after: int = 60):
        self.retry_after = retry_after
        super().__init__(message)


# ── Service / Dependency errors (503) ────────────────────────────────────── #

class ServiceException(ElectroHubException):
    status_code = 503
    error_code = "SERVICE_UNAVAILABLE"


class DatabaseException(ServiceException):
    error_code = "DATABASE_ERROR"


class CacheException(ServiceException):
    error_code = "CACHE_ERROR"


class EmailServiceException(ServiceException):
    error_code = "EMAIL_SERVICE_ERROR"


# ── FastAPI exception handlers ─────────────────────────────────────────────── #

async def electrohub_exception_handler(request: Request, exc: ElectroHubException):
    extra = {"retry_after": exc.retry_after} if isinstance(exc, RateLimitException) else {}
    log.warning(
        "app_exception",
        error_code=exc.error_code,
        message=exc.message,
        path=request.url.path,
        method=request.method,
        **extra,
    )
    headers = {}
    if isinstance(exc, RateLimitException):
        headers["Retry-After"] = str(exc.retry_after)

    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.error_code, "message": exc.message},
        headers=headers,
    )


async def unhandled_exception_handler(request: Request, exc: Exception):
    log.error(
        "unhandled_exception",
        exc_type=type(exc).__name__,
        message=str(exc),
        path=request.url.path,
        method=request.method,
        exc_info=True,
    )
    return JSONResponse(
        status_code=500,
        content={"error": "INTERNAL_ERROR", "message": "An unexpected error occurred"},
    )
