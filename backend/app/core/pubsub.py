"""
Redis Pub/Sub event bus for ElectroHub.

Why Redis Pub/Sub instead of gRPC right now?
  - This is a monolith: all handlers run in the same process, so gRPC
    inter-service transport would be transport overhead for no gain.
  - Redis is already in the stack (rate limiting, saved items cache).
  - When the app splits into microservices, swap publish_event() to
    push onto a gRPC streaming server or a proper broker (NATS, Kafka)
    with zero changes to the call sites.

Event channels:
    electrohub:events:message_sent   — buyer sent seller a message
    electrohub:events:item_saved     — user saved/wishlisted an item
    electrohub:events:item_listed    — seller published a new listing

Usage (publisher side):
    from app.core.pubsub import publish_event
    publish_event("message_sent", {"buyer_id": ..., "seller_id": ..., "item_id": ...})

The subscriber loop runs as a background asyncio Task started in main.py lifespan.
Each handler is the extension point: add push-notification, email, websocket, etc.
"""

import asyncio
import json

import structlog
from app.core.redis_client import get_redis_client

log = structlog.get_logger()

CHANNELS = {
    "message_sent": "electrohub:events:message_sent",
    "item_saved":   "electrohub:events:item_saved",
    "item_listed":  "electrohub:events:item_listed",
}


# ── Publisher ─────────────────────────────────────────────────────────────── #

def publish_event(channel: str, payload: dict) -> None:
    """
    Fire-and-forget publish. Logs on failure but never raises —
    the primary request must not fail because of an event.
    """
    from app.core.metrics import event_published
    try:
        key = CHANNELS.get(channel, f"electrohub:events:{channel}")
        get_redis_client().publish(key, json.dumps(payload))
        event_published.labels(channel=channel).inc()
        log.info("event_published", channel=channel, payload=payload)
    except Exception as exc:
        log.error("event_publish_failed", channel=channel, error=str(exc))


# ── Subscriber loop (background asyncio task) ─────────────────────────────── #

async def subscribe_events() -> None:
    """
    Long-running coroutine — subscribe to all channels and dispatch to handlers.
    Started by the FastAPI lifespan; cancelled on shutdown.
    """
    redis = get_redis_client()
    pubsub = redis.pubsub()
    pubsub.subscribe(*CHANNELS.values())
    log.info("pubsub_subscribed", channels=list(CHANNELS.values()))

    while True:
        try:
            msg = pubsub.get_message(ignore_subscribe_messages=True, timeout=0.05)
            if msg:
                await _dispatch(msg)
        except asyncio.CancelledError:
            pubsub.unsubscribe()
            log.info("pubsub_shutdown")
            return
        except Exception as exc:
            log.error("pubsub_loop_error", error=str(exc))
        await asyncio.sleep(0.01)


async def _dispatch(message: dict) -> None:
    from app.core.metrics import event_consumed
    try:
        raw_channel = message.get("channel", b"")
        channel = raw_channel.decode() if isinstance(raw_channel, bytes) else raw_channel
        data = json.loads(message["data"])
        short = channel.split(":")[-1]          # e.g. "message_sent"
        event_consumed.labels(channel=short).inc()
        log.info("event_received", channel=short, data=data)

        if short == "message_sent":
            await _on_message_sent(data)
        elif short == "item_saved":
            await _on_item_saved(data)
        elif short == "item_listed":
            await _on_item_listed(data)
    except Exception as exc:
        log.error("event_dispatch_failed", error=str(exc), message=str(message))


# ── Event handlers ────────────────────────────────────────────────────────── #
# Each handler is the seam where you'd add: WebSocket push, FCM push,
# email notification, Twilio SMS, audit log write, etc.

async def _on_message_sent(data: dict) -> None:
    log.info(
        "handler_message_sent",
        buyer_id=data.get("buyer_id"),
        seller_id=data.get("seller_id"),
        item_id=data.get("item_id"),
    )
    # TODO: push WebSocket notification to seller


async def _on_item_saved(data: dict) -> None:
    log.info(
        "handler_item_saved",
        user_id=data.get("user_id"),
        item_id=data.get("item_id"),
    )
    # TODO: increment seller's "saves" analytics counter


async def _on_item_listed(data: dict) -> None:
    log.info(
        "handler_item_listed",
        seller_id=data.get("seller_id"),
        item_id=data.get("item_id"),
        category=data.get("category"),
    )
    # TODO: trigger search index update / recommendation refresh
