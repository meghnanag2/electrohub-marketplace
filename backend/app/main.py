import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import routes
from app.core.database import Base, engine
from app.core.exceptions import (
    ElectroHubException,
    electrohub_exception_handler,
    unhandled_exception_handler,
)
from app.core.logging_config import configure_logging, request_logging_middleware
from app.core.metrics import setup_metrics
from app.core.pubsub import subscribe_events
from app.core.rate_limit import global_rate_limit_middleware

configure_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    task = asyncio.create_task(subscribe_events())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="ElectroHub API", lifespan=lifespan)

# ── Exception handlers (must be before middleware) ────────────────────────── #
app.add_exception_handler(ElectroHubException, electrohub_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

# ── Middleware (outermost registered = outermost executed) ────────────────── #
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.middleware("http")(request_logging_middleware)
app.middleware("http")(global_rate_limit_middleware)

# ── Prometheus /metrics endpoint ──────────────────────────────────────────── #
setup_metrics(app)

app.include_router(routes.router)


@app.get("/health", tags=["ops"])
def health_check():
    return {"status": "ok"}


@app.get("/debug/shard-distribution", tags=["ops"])
def shard_distribution():
    from app.core.shard_db import get_shard_manager
    manager = get_shard_manager()
    return {"virtual_nodes_per_shard": manager.distribution()}
