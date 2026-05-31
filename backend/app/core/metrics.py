"""
Prometheus metrics for ElectroHub.

Auto-instrumentation (via prometheus-fastapi-instrumentator) covers:
  - http_requests_total          (method, handler, status)
  - http_request_duration_seconds (histogram, method, handler)

Custom business counters below track domain events that HTTP metrics miss.

Scrape endpoint: GET /metrics  (exposed by setup_metrics())
Local Prometheus: add to docker-compose and point at backend:8000/metrics
"""

from prometheus_client import Counter, Gauge
from prometheus_fastapi_instrumentator import Instrumentator

# ── Business-level counters ───────────────────────────────────────────────── #

items_listed = Counter(
    "electrohub_items_listed_total",
    "Marketplace items created",
)

messages_sent = Counter(
    "electrohub_messages_sent_total",
    "Messages sent between buyer and seller",
)

items_saved = Counter(
    "electrohub_items_saved_total",
    "Items added to user wishlists",
)

login_attempts = Counter(
    "electrohub_login_attempts_total",
    "Login attempts",
    ["result"],           # label values: "success" | "failure"
)

rate_limit_hits = Counter(
    "electrohub_rate_limit_hits_total",
    "Requests rejected by the token bucket rate limiter",
    ["layer"],            # label values: "global" | "login" | "contact"
)

event_published = Counter(
    "electrohub_pubsub_events_published_total",
    "Events published onto Redis pub/sub channels",
    ["channel"],
)

event_consumed = Counter(
    "electrohub_pubsub_events_consumed_total",
    "Events consumed from Redis pub/sub channels",
    ["channel"],
)

# ── Gauges ────────────────────────────────────────────────────────────────── #

db_pool_checked_out = Gauge(
    "electrohub_db_pool_checked_out",
    "SQLAlchemy connections currently checked out from the pool",
    ["shard"],
)


# ── Wiring ────────────────────────────────────────────────────────────────── #

def setup_metrics(app) -> None:
    """Call once in main.py after the app is created."""
    Instrumentator(
        should_group_status_codes=True,
        should_ignore_untemplated=True,
        excluded_handlers=["/health", "/metrics", "/docs", "/openapi.json", "/redoc"],
    ).instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)
