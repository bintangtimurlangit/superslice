"""Opt-in API protection: key auth, rate limiting, and a concurrency cap.

All three are disabled by default, so the service runs with zero configuration.
They are enabled purely through environment variables (see config.py):

- ``API_KEYS``               -> require a matching ``X-API-Key`` / Bearer token
- ``RATE_LIMIT_PER_MINUTE``  -> per-client request ceiling
- ``MAX_CONCURRENT_SLICES``  -> bound simultaneous slices

The rate limiter and concurrency cap are in-process, i.e. per replica. For a
multi-replica deployment, enforce global limits at the gateway instead.
"""
import asyncio
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from typing import Optional

from starlette.requests import Request

from ..config import API_KEYS, MAX_CONCURRENT_SLICES, RATE_LIMIT_PER_MINUTE
from .errors import APIError


def _bearer_token(request: Request) -> Optional[str]:
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return None


def _provided_key(request: Request) -> Optional[str]:
    return request.headers.get("x-api-key") or _bearer_token(request)


def _client_id(request: Request) -> str:
    key = _provided_key(request)
    if key:
        return f"key:{key}"
    client = request.client
    return f"ip:{client.host if client else 'unknown'}"


async def require_api_key(request: Request) -> None:
    """FastAPI dependency: enforce an API key when ``API_KEYS`` is configured."""
    if not API_KEYS:
        return  # auth disabled
    if _provided_key(request) not in API_KEYS:
        raise APIError(401, "UNAUTHORIZED", "Missing or invalid API key")


# --- Rate limiting (sliding 60s window per client) ------------------------
_WINDOW = 60.0
_hits: dict[str, deque] = defaultdict(deque)
_rate_lock = asyncio.Lock()


async def enforce_rate_limit(request: Request) -> None:
    """FastAPI dependency: enforce ``RATE_LIMIT_PER_MINUTE`` per client."""
    if RATE_LIMIT_PER_MINUTE <= 0:
        return  # disabled
    client = _client_id(request)
    now = time.monotonic()
    async with _rate_lock:
        hits = _hits[client]
        while hits and hits[0] <= now - _WINDOW:
            hits.popleft()
        if len(hits) >= RATE_LIMIT_PER_MINUTE:
            retry_after = int(_WINDOW - (now - hits[0])) + 1
            raise APIError(
                429,
                "RATE_LIMITED",
                f"Rate limit exceeded ({RATE_LIMIT_PER_MINUTE}/min)",
                headers={"Retry-After": str(retry_after)},
            )
        hits.append(now)


# --- Concurrency cap ------------------------------------------------------
_semaphore: Optional[asyncio.Semaphore] = (
    asyncio.Semaphore(MAX_CONCURRENT_SLICES) if MAX_CONCURRENT_SLICES > 0 else None
)


@asynccontextmanager
async def slice_slot():
    """Bound the number of concurrent slices; callers queue when at capacity."""
    if _semaphore is None:
        yield
        return
    await _semaphore.acquire()
    try:
        yield
    finally:
        _semaphore.release()
