Perfect, let’s lock this down nicely so you can just copy–paste into files + into `deployment.md`.

Below are **two final scripts**:

* `deploy_mac.sh` – for local Mac dev with Docker + docker-compose
* `deploy_gke.sh` – for GKE deployment after you `git pull` on your laptop

I’ll assume project root is `electrohub-marketplace-main` and you’ve already updated `database/03_seed_data.py` to use `DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD`.

---

## 1️⃣ Local deployment script – `deploy_mac.sh`

**Location:** project root, next to `docker-compose.yml`, `backend/`, `frontend/`, `database/`.

```bash
#!/bin/bash
set -euo pipefail

# ----------------------------------------------------
# ElectroHub local deployment script (Mac + Docker)
# ----------------------------------------------------
# What this does:
#  1) Check Docker is installed & running
#  2) Start Postgres container via docker-compose
#  3) Wait until DB is ready
#  4) Create Python .venv in project root
#  5) Install psycopg2-binary + Faker (for seeding)
#  6) Run database/03_seed_data.py (env-based DB config)
#  7) Build & start backend + frontend with docker-compose
# ----------------------------------------------------

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo "🚀 ElectroHub local deployment (Mac)"

# 0. Check Docker binary
if ! command -v docker >/dev/null 2>&1; then
  echo "❌ Docker is not installed. Install Docker Desktop for Mac first."
  exit 1
fi

# 0b. Check Docker daemon
if ! docker info >/dev/null 2>&1; then
  echo "❌ Docker daemon is not running. Start Docker Desktop and retry."
  exit 1
fi

# OPTIONAL: stop Homebrew Postgres if it fights for port 5432
# echo "🧹 Stopping any Homebrew Postgres (if running)..."
# brew services stop postgresql@17 || true

echo "🧹 Stopping any previous ElectroHub stack..."
docker compose down -v || true

echo "🐘 Starting Postgres container..."
docker compose up -d postgres

echo "⏳ Waiting for Postgres to be ready..."
# Uses container_name from docker-compose.yml: electrohub-postgres
until docker exec electrohub-postgres pg_isready -U postgres -d electrohub >/dev/null 2>&1; do
  printf "."
  sleep 2
done
echo ""
echo "✅ Postgres is ready."

echo "👟 Setting up Python virtualenv in project root..."
if [ ! -d ".venv" ]; then
  python3 -m venv .venv
fi

# shellcheck source=/dev/null
source .venv/bin/activate

echo "📦 Installing Python packages for seeding (psycopg2-binary, Faker)..."
pip install --upgrade pip >/dev/null
pip install psycopg2-binary faker >/dev/null

echo "🌱 Running database/03_seed_data.py with env-based DB config..."

export DB_HOST="127.0.0.1"
export DB_PORT="5432"
export DB_NAME="electrohub"
export DB_USER="postgres"
export DB_PASSWORD="password"

python database/03_seed_data.py

deactivate
echo "✅ Database seeded."

echo "🔍 Verifying demo user exists..."
docker exec electrohub-postgres psql -U postgres -d electrohub -c \
"SELECT user_id, email FROM user_accounts WHERE email = 'demo@electrohub.com';"

echo "🐍 Building and starting backend + 🧁 frontend..."
# (Assumes services named 'backend' and 'frontend' exist in docker-compose.yml)
docker compose up -d --build

echo ""
echo "✅ ElectroHub is running locally!"
echo "   Frontend: http://localhost:3000"
echo "   Backend : http://localhost:8000"
echo ""
echo "👉 Demo login: demo@electrohub.com / password123"
```

**How you use it:**

```bash
cd ~/Downloads/electrohub-marketplace-main
chmod +x deploy_mac.sh
./deploy_mac.sh
```

To stop everything later:

```bash
docker compose down -v
```

---

## 2️⃣ GKE deployment script – `deploy_gke.sh`

This is for your **laptop**, after you `git pull` the repo and have:

* a GKE cluster already created
* an Artifact Registry repo ready for your Docker images

You’ll set these env vars before running it:

* `GCP_PROJECT_ID` – your GCP project ID
* `GKE_CLUSTER_NAME` – your GKE cluster name
* `GKE_REGION` – region/zone, e.g. `us-central1-a`
* `AR_REPO` – Artifact Registry repo, e.g.
  `us-central1-docker.pkg.dev/$GCP_PROJECT_ID/electrohub`
* `APP_VERSION` – image tag, e.g. `v1` or `$(date +%Y%m%d-%H%M)`

**Location:** project root as `deploy_gke.sh`.

```bash
#!/bin/bash
set -euo pipefail

# -------------------------------------------------------
# ElectroHub GKE deployment script (run on your laptop)
# -------------------------------------------------------
# Required env vars:
#   GCP_PROJECT_ID
#   GKE_CLUSTER_NAME
#   GKE_REGION
#   AR_REPO        # e.g. us-central1-docker.pkg.dev/$GCP_PROJECT_ID/electrohub
#   APP_VERSION    # e.g. v1 or 20251129-0900
#
# Expects Kubernetes manifests in:
#   k8s/postgres.yaml   - Postgres Deployment/StatefulSet + Service
#   k8s/backend.yaml    - Backend Deployment + Service
#   k8s/frontend.yaml   - Frontend Deployment + Service / Ingress
#   k8s/seed-job.yaml   - One-off Job running database/03_seed_data.py
# -------------------------------------------------------

if [ -z "${GCP_PROJECT_ID:-}" ] || \
   [ -z "${GKE_CLUSTER_NAME:-}" ] || \
   [ -z "${GKE_REGION:-}" ] || \
   [ -z "${AR_REPO:-}" ] || \
   [ -z "${APP_VERSION:-}" ]; then
  echo "❌ Please set: GCP_PROJECT_ID, GKE_CLUSTER_NAME, GKE_REGION, AR_REPO, APP_VERSION"
  exit 1
fi

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_ROOT"

echo "🚀 Deploying ElectroHub to GKE..."
echo "   Project : $GCP_PROJECT_ID"
echo "   Cluster : $GKE_CLUSTER_NAME"
echo "   Region  : $GKE_REGION"
echo "   Repo    : $AR_REPO"
echo "   Version : $APP_VERSION"
echo ""

# 1. Configure gcloud and get cluster credentials
gcloud config set project "$GCP_PROJECT_ID"
gcloud container clusters get-credentials "$GKE_CLUSTER_NAME" --region "$GKE_REGION"

# 2. Build & push Docker images to Artifact Registry
echo "🐳 Building backend image..."
docker build -t "$AR_REPO/backend:$APP_VERSION" backend

echo "🐳 Building frontend image..."
docker build -f frontend/Dockerfile -t "$AR_REPO/frontend:$APP_VERSION" frontend

echo "🔐 Configuring Artifact Registry auth..."
# Extract host from AR_REPO (e.g. us-central1-docker.pkg.dev)
REGISTRY_HOST="$(echo "$AR_REPO" | cut -d'/' -f1)"
gcloud auth configure-docker "$REGISTRY_HOST" -q

echo "📤 Pushing images..."
docker push "$AR_REPO/backend:$APP_VERSION"
docker push "$AR_REPO/frontend:$APP_VERSION"

# 3. Apply Kubernetes manifests
echo "📄 Applying Kubernetes manifests..."
kubectl apply -f k8s/postgres.yaml
kubectl apply -f k8s/backend.yaml
kubectl apply -f k8s/frontend.yaml

# 4. Run seed job to populate DB (uses env vars inside YAML)
echo "🌱 Applying seed job..."
kubectl apply -f k8s/seed-job.yaml

echo "⏳ Waiting for seed job to complete..."
kubectl wait --for=condition=complete --timeout=600s job/electrohub-seed-job || {
  echo "⚠️ Seed job did not complete in time. Logs:"
  kubectl logs job/electrohub-seed-job || true
  exit 1
}

echo "🧹 Cleaning up seed job (optional)..."
kubectl delete job/electrohub-seed-job || true

echo ""
echo "✅ GKE deployment complete!"
echo "   Check services with: kubectl get svc"
echo "   Check pods      with: kubectl get pods"
echo ""
```

**Example usage:**

```bash
export GCP_PROJECT_ID="your-project-id"
export GKE_CLUSTER_NAME="electrohub-cluster"
export GKE_REGION="us-central1-a"
export AR_REPO="us-central1-docker.pkg.dev/$GCP_PROJECT_ID/electrohub"
export APP_VERSION="v1"

chmod +x deploy_gke.sh
./deploy_gke.sh
```

---

## 3️⃣ Small snippet for `deployment.md`

You can paste something like this into your `deployment.md`:

````markdown
## Local deployment (Mac + Docker)

```bash
./deploy_mac.sh
````

This will:

* start Postgres in Docker
* set up `.venv` and run `database/03_seed_data.py` (env-based DB config)
* seed demo user `demo@electrohub.com / password123`
* build and start backend + frontend at `http://localhost:3000` and `http://localhost:8000`.

---

## GKE deployment

Set environment variables and run:

```bash
export GCP_PROJECT_ID="your-project-id"
export GKE_CLUSTER_NAME="electrohub-cluster"
export GKE_REGION="us-central1-a"
export AR_REPO="us-central1-docker.pkg.dev/$GCP_PROJECT_ID/electrohub"
export APP_VERSION="v1"

./deploy_gke.sh
```

This will:

* build & push backend + frontend images to Artifact Registry
* apply `k8s/*.yaml` manifests
* run a `seed-job` which executes `database/03_seed_data.py` inside the cluster
* clean up the job after completion.

```

---

If you want, I can also draft the **`k8s/seed-job.yaml`** and sample `postgres.yaml/backend.yaml/frontend.yaml` so they match your env-variable-based seeding and JWT login flow.
```
