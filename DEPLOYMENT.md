# Deployment Guide

This guide covers running ElectroHub locally, what to check if something breaks, and notes on taking it further toward a production environment.

---

## Local Setup (Docker Compose)

### Requirements

- Docker Desktop 4.x with Compose v2 (`docker compose` not `docker-compose`)
- 8 GB RAM minimum — the SBERT recommendation model loads ~90 MB into memory on startup
- Ports 80, 3000, 5432, 6379, 9092 free on your machine

### First-time build

```bash
git clone https://github.com/your-username/electrohub-marketplace.git
cd electrohub-marketplace
docker compose up --build
```

The first build takes 4–7 minutes. Most of that is:
- Downloading CPU-only PyTorch (~700 MB)
- Downloading `all-MiniLM-L6-v2` model weights (~90 MB from HuggingFace)

Both are cached in Docker image layers. Subsequent `docker compose up` runs take ~30 seconds.

### Seed the database

Wait until all containers are healthy, then run:

```bash
docker exec -it electrohub-backend python seed_all.py
```

This wipes and re-populates:
- 100 demo users
- 500 electronics listings across 6 categories
- 995 product images (Unsplash URLs)
- 3,000 view/save/click interactions
- 200 sample messages

To check the seed finished cleanly:

```bash
docker exec -it electrohub-backend python seed_all.py 2>&1 | tail -10
```

### Verify everything is up

```bash
docker compose ps
```

All containers should show `healthy`. If any show `unhealthy`, see the troubleshooting section below.

```bash
curl http://localhost/health
# {"service":"user-service","status":"ok"}
```

---

## Service Health Endpoints

| Service | Health check URL |
|---|---|
| user-service | http://localhost:8001/health |
| listing-service | http://localhost:8002/health |
| messaging-service | http://localhost:8003/health |
| activity-service | http://localhost:8004/health |
| recommendation-service | http://localhost:8005/health |

All return `{"status": "ok"}` when ready.

---

## Container Reference

| Container name | Image | Purpose |
|---|---|---|
| `electrohub-nginx` | nginx:1.25-alpine | API gateway and rate limiting |
| `electrohub-user-service` | local build | Auth, JWT, user accounts |
| `electrohub-listing-service` | local build | Items, search, wishlist |
| `electrohub-messaging-service` | local build | Chat, WebSocket, inbox |
| `electrohub-activity-service` | local build | Event logging |
| `electrohub-recommendation-service` | local build | SBERT similarity |
| `electrohub-postgres-shard0` | postgres:15-alpine | Primary database |
| `electrohub-redis` | redis:7-alpine | Cache, pub/sub, wishlist sets |
| `electrohub-kafka` | apache/kafka:3.7.1 | Event streaming |
| `electrohub-rabbitmq` | rabbitmq:3-management | Notification queue |

---

## Rebuilding a Single Service

When you change backend code, you don't need to rebuild everything:

```bash
# Rebuild and restart just the listing-service
docker compose build listing-service
docker compose up -d listing-service

# Or in one command
docker compose up -d --build listing-service
```

Frontend changes hot-reload automatically — no rebuild needed while the `frontend` container is running.

---

## Logs

```bash
# All services
docker compose logs -f

# One service
docker compose logs -f listing-service

# Last 50 lines
docker compose logs --tail=50 recommendation-service
```

---

## Troubleshooting

### Container stuck in `unhealthy`

```bash
docker logs electrohub-<service-name>
```

Common causes:

| Symptom | Likely cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'user_pb2'` | gRPC stubs not on PYTHONPATH | Rebuild the image — `PYTHONPATH=/app/app/grpc/generated` is set in the Dockerfile |
| `curl: not found` in health check | Old image without curl | Rebuild: `docker compose build <service>` |
| `AttributeError: 'PrintLogger' object has no attribute 'name'` | Old structlog config | Pull latest code — `add_logger_name` was removed from processors |
| `502 Bad Gateway` after rebuild | Nginx cached old container IP | `docker restart electrohub-nginx` |
| `connection refused` on port 5432 | Postgres still initialising | Wait 30 seconds and retry |

### Recommendation service is slow to start

This is expected. It loads all 500 items and encodes them with SBERT on startup. Give it 60–90 seconds. The `start_period: 120s` in `docker-compose.yml` accounts for this.

### Redis wishlist returns empty after restart

Redis is configured with `appendonly yes` (AOF persistence), so data survives restarts. If you wiped the volume, the listing-service will automatically fall back to reading from Postgres and re-populate Redis on the next request.

### Kafka connection errors in activity-service

Kafka uses KRaft mode (no Zookeeper). It needs a few seconds after the container starts to elect a controller. Services that depend on Kafka will retry — this resolves itself within 30 seconds.

---

## Environment Variables

All environment variables are set in `docker-compose.yml`. For a real deployment, move secrets out of the compose file into a `.env` file or a secrets manager.

| Variable | Default | Used by |
|---|---|---|
| `DB_HOST` | `postgres_shard0` | all services |
| `DB_NAME` | `electrohub` | all services |
| `DB_USER` | `postgres` | all services |
| `DB_PASSWORD` | `password` | all services — **change this** |
| `JWT_SECRET_KEY` | `electrohub-dev-secret-change-in-production` | messaging-service — **change this** |
| `REDIS_HOST` | `redis` | listing, messaging |
| `KAFKA_BROKERS` | `kafka:9092` | messaging, activity |
| `RABBITMQ_HOST` | `rabbitmq` | messaging, notification |

---

## Stopping and Cleaning Up

```bash
# Stop all containers (keeps volumes — data is preserved)
docker compose down

# Stop and delete all data volumes (full reset)
docker compose down -v

# Remove built images as well
docker compose down -v --rmi local
```

---

## Notes on Production Readiness

This project is a development setup. Before running it in production, the main things to address are:

- **Secrets** — rotate `JWT_SECRET_KEY` and `DB_PASSWORD`; use environment injection or a vault, not hardcoded values in compose
- **HTTPS** — add TLS termination at the Nginx layer (Let's Encrypt or a load balancer)
- **Postgres** — the shard1 container exists in the schema but is not wired up; add a read replica or managed DB (RDS, Cloud SQL)
- **SBERT cold start** — on a fresh deployment the recommendation service takes 60–90 seconds to build the index; add a readiness probe before routing traffic to it
- **Frontend** — build the React app (`npm run build`) and serve the static files from Nginx rather than running the dev server
- **Rate limits** — the current Nginx limits (5–60 req/min) are tuned for development; adjust for real traffic
