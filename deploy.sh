#!/usr/bin/env bash

# Google Cloud deployment helper for Runway Ops Demo
# - Builds Docker images for backend & frontend
# - Pushes images to Artifact Registry
# - Deploys to Cloud Run (fully managed)

set -euo pipefail

### Configuration #############################################################
PROJECT_ID=runwayops-478106
REGION=${REGION:-us-central1}
REPO_NAME=${REPO_NAME:-runwayops_demo}
BACKEND_SERVICE_NAME=${BACKEND_SERVICE_NAME:-runwayops-backend}
FRONTEND_SERVICE_NAME=${FRONTEND_SERVICE_NAME:-runwayops-frontend}
BACKEND_PORT=${BACKEND_PORT:-8000}

# Environment files (KEY=value per line, no quotes). Required for backend.
BACKEND_ENV_FILE=${BACKEND_ENV_FILE:-backend/.env.deploy}

# Optional override for frontend API base. Defaults to backend service URL once deployed.
FRONTEND_VITE_MONITOR_API=${FRONTEND_VITE_MONITOR_API:-}

###############################################################################

if [[ -z "$PROJECT_ID" ]]; then
  echo "❌ PROJECT_ID is not set and gcloud has no default project configured." >&2
  exit 1
fi

command -v gcloud >/dev/null 2>&1 || { echo "❌ gcloud CLI is required." >&2; exit 1; }
command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required." >&2; exit 1; }

echo "🚀 Deploying Runway Ops Demo to Google Cloud"
echo "Project : $PROJECT_ID"
echo "Region  : $REGION"
echo "Repo    : $REPO_NAME"

##########################################################################
# Helper functions

read_env_file() {
  local file=$1
  if [[ ! -f "$file" ]]; then
    echo "❌ Env file '$file' not found." >&2
    exit 1
  fi
  # Remove comments/blank lines, join with comma
  grep -v '^#' "$file" | grep -v '^\s*$' | paste -sd ',' -
}

ensure_artifact_repo() {
  if ! gcloud artifacts repositories describe "$REPO_NAME" --location="$REGION" >/dev/null 2>&1; then
    echo "📦 Creating Artifact Registry repo '$REPO_NAME' in $REGION"
    gcloud artifacts repositories create "$REPO_NAME" \
      --repository-format=docker \
      --location="$REGION" \
      --description="Runway Ops Demo images"
  fi
}

###############################################################################

ensure_artifact_repo

REGISTRY="$REGION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME"
GIT_SHA=$(git rev-parse --short HEAD 2>/dev/null || echo "latest")

BACKEND_IMAGE="$REGISTRY/backend:$GIT_SHA"
FRONTEND_IMAGE="$REGISTRY/frontend:$GIT_SHA"

echo "🔐 Configuring Docker auth for Artifact Registry"
gcloud auth configure-docker "$REGION-docker.pkg.dev" --quiet

echo "🏗️ Building backend image: $BACKEND_IMAGE"
docker build -t "$BACKEND_IMAGE" ./backend
docker push "$BACKEND_IMAGE"

BACKEND_ENV_VARS=$(read_env_file "$BACKEND_ENV_FILE")

echo "🚢 Deploying backend to Cloud Run: $BACKEND_SERVICE_NAME"
gcloud run deploy "$BACKEND_SERVICE_NAME" \
  --image "$BACKEND_IMAGE" \
  --project "$PROJECT_ID" \
  --region "$REGION" \
  --port "$BACKEND_PORT" \
  --set-env-vars "$BACKEND_ENV_VARS" \
  --allow-unauthenticated

BACKEND_URL=$(gcloud run services describe "$BACKEND_SERVICE_NAME" \
  --project "$PROJECT_ID" --region "$REGION" \
  --format='value(status.url)')

if [[ -z "$FRONTEND_VITE_MONITOR_API" ]]; then
  FRONTEND_VITE_MONITOR_API="$BACKEND_URL"
fi

echo "🏗️ Building frontend image: $FRONTEND_IMAGE"
docker build \
  --build-arg VITE_MONITOR_API="$FRONTEND_VITE_MONITOR_API" \
  -t "$FRONTEND_IMAGE" ./frontend/dashboard
docker push "$FRONTEND_IMAGE"

echo "🚢 Deploying frontend to Cloud Run: $FRONTEND_SERVICE_NAME"
gcloud run deploy "$FRONTEND_SERVICE_NAME" \
  --image "$FRONTEND_IMAGE" \
  --project "$PROJECT_ID" \
  --region "$REGION" \
  --port 80 \
  --allow-unauthenticated

FRONTEND_URL=$(gcloud run services describe "$FRONTEND_SERVICE_NAME" \
  --project "$PROJECT_ID" --region "$REGION" \
  --format='value(status.url)')

cat <<EOF

✅ Deployment complete!
Backend : $BACKEND_URL
Frontend: $FRONTEND_URL

Remember to:
- Provision MongoDB (Atlas or Atlas on GCP) and update MONGO_URI in $BACKEND_ENV_FILE
- Set production API keys (OpenAI, Aviationstack, Amadeus) in the env file
- Configure HTTPS/custom domains in Cloud Run if desired
EOF