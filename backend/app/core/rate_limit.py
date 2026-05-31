"""
Token bucket rate limiter backed by Redis.

Why token bucket?
- Allows controlled bursting: a user who has been idle accumulates tokens
  up to the bucket capacity, then can spend them quickly.
- Fairer than fixed-window: no "reset cliff" where 10 requests at 11:59
  and 10 more at 12:01 bypass a per-minute limit.
- O(1) per request — single atomic Redis Lua call.

Algorithm:
    Each user/IP has a bucket: { tokens: float, last_refill: timestamp }
    On every request:
        elapsed   = now - last_refill
        tokens   += elapsed * refill_rate          # passive refill
        tokens    = min(tokens, capacity)           # cap at max
        if tokens >= 1: tokens -= 1; allow
        else:           reject 429

The Lua script executes atomically on Redis so there are no race conditions
even with many concurrent requests hitting the same bucket.
"""

import time
from typing import Optional
from fastapi import Request, HTTPException, status
from app.core.redis_client import get_redis_client

# ---------------------------------------------------------------------- #
#  Lua script — runs atomically inside Redis                              #
# ---------------------------------------------------------------------- #

_TOKEN_BUCKET_LUA = """
local key          = KEYS[1]
local capacity     = tonumber(ARGV[1])
local refill_rate  = tonumber(ARGV[2])
local now          = tonumber(ARGV[3])
local cost         = tonumber(ARGV[4])

local data = redis.call('HMGET', key, 'tokens', 'last_refill')
local tokens      = tonumber(data[1]) or capacity
local last_refill = tonumber(data[2]) or now

-- Refill proportional to elapsed time
local elapsed    = math.max(0, now - last_refill)
local new_tokens = math.min(capacity, tokens + elapsed * refill_rate)

if new_tokens < cost then
    -- Not enough tokens — return remaining tokens (negative means wait time)
    return {0, math.ceil((cost - new_tokens) / refill_rate)}
end

new_tokens = new_tokens - cost
redis.call('HMSET', key, 'tokens', new_tokens, 'last_refill', now)
redis.call('EXPIRE', key, 3600)
return {1, math.floor(new_tokens)}
"""


class TokenBucket:
    """
    Reusable token bucket. Instantiate once per limit tier.

    Parameters
    ----------
    capacity     : max tokens in the bucket (burst size)
    refill_rate  : tokens added per second
    cost         : tokens consumed per request (default 1)

    Example tiers
    -------------
    browse_limit  = TokenBucket(capacity=60,  refill_rate=1)   # 60 req/min, burst 60
    auth_limit    = TokenBucket(capacity=5,   refill_rate=0.1) # 5 req/min, burst 5
    contact_limit = TokenBucket(capacity=3,   refill_rate=0.05)# 3 req/min, burst 3
    """

    def __init__(self, capacity: int, refill_rate: float, cost: int = 1):
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.cost = cost
        self._script = None

    def _get_script(self):
        if self._script is None:
            redis = get_redis_client()
            self._script = redis.register_script(_TOKEN_BUCKET_LUA)
        return self._script

    def consume(self, identifier: str) -> tuple[bool, int]:
        """
        Try to consume one token for `identifier`.

        Returns
        -------
        (allowed, info)
            allowed=True  → request is permitted; info = tokens remaining
            allowed=False → rate limited;          info = seconds to wait
        """
        redis = get_redis_client()
        script = self._get_script()
        key = f"tb:{identifier}:{self.capacity}:{self.refill_rate}"
        now = time.time()
        result = script(
            keys=[key],
            args=[self.capacity, self.refill_rate, now, self.cost],
        )
        allowed = bool(result[0])
        info = int(result[1])
        return allowed, info


# ---------------------------------------------------------------------- #
#  Pre-configured limit tiers                                             #
# ---------------------------------------------------------------------- #

# Public endpoints — generous, protects DB from scrapers
browse_bucket = TokenBucket(capacity=60, refill_rate=1.0)

# Login endpoint — tight, prevents brute force
login_bucket = TokenBucket(capacity=5, refill_rate=0.083)   # 5/min

# Contact-seller — separate daily limit already in route; this adds per-minute
contact_bucket = TokenBucket(capacity=3, refill_rate=0.05)


# ---------------------------------------------------------------------- #
#  FastAPI dependency helpers                                             #
# ---------------------------------------------------------------------- #

def _get_identifier(request: Request, use_user: bool = False) -> str:
    """Prefer authenticated user_id; fall back to IP."""
    if use_user:
        token = request.headers.get("Authorization", "")
        if token.startswith("Bearer "):
            from app.core.security import decode_access_token
            user_id = decode_access_token(token[7:])
            if user_id:
                return f"user:{user_id}"
    return f"ip:{request.client.host}"


def rate_limit(bucket: TokenBucket, use_user: bool = True):
    """
    Returns a FastAPI dependency that enforces the given bucket.

    Usage:
        @router.get("/items", dependencies=[Depends(rate_limit(browse_bucket))])
        def get_items(): ...
    """
    def _dependency(request: Request):
        identifier = _get_identifier(request, use_user=use_user)
        allowed, info = bucket.consume(identifier)
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Retry after {info} seconds.",
                headers={"Retry-After": str(info)},
            )
    return _dependency


# ---------------------------------------------------------------------- #
#  Global middleware — coarse IP shield (applied to all routes)           #
# ---------------------------------------------------------------------- #

_global_bucket = TokenBucket(capacity=200, refill_rate=3.0)  # 200 burst, 3/sec steady

EXEMPT_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}


async def global_rate_limit_middleware(request: Request, call_next):
    """
    Middleware-level token bucket: 200-burst / 3 req-per-second per IP.
    Nginx handles the outer DDoS shield; this is the last line of defence.
    """
    if request.url.path in EXEMPT_PATHS:
        return await call_next(request)

    identifier = f"ip:{request.client.host}"
    allowed, wait = _global_bucket.consume(identifier)
    if not allowed:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=429,
            content={"detail": f"Too many requests. Retry after {wait}s."},
            headers={"Retry-After": str(wait)},
        )
    return await call_next(request)
