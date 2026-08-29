#!/usr/bin/env bash
set -euo pipefail
PROJECT="${GOOGLE_CLOUD_PROJECT:?set GOOGLE_CLOUD_PROJECT}"
REGION="${GOOGLE_CLOUD_LOCATION:-us-central1}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT}/cloud-run-source-deploy/greenchain-mcp"

gcloud builds submit "$ROOT" \
  --project "$PROJECT" \
  --config "$ROOT/deploy/mcp-cloudbuild.yaml" \
  --substitutions "_IMAGE=$IMAGE"

gcloud run deploy greenchain-mcp \
  --image "$IMAGE" \
  --region "$REGION" \
  --project "$PROJECT" \
  --allow-unauthenticated \
  --memory 512Mi \
  --port 8081

echo "MCP: $(gcloud run services describe greenchain-mcp --region "$REGION" --project "$PROJECT" --format='value(status.url)')"
