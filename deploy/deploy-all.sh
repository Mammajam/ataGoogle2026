#!/usr/bin/env bash
set -euo pipefail
PROJECT="${GOOGLE_CLOUD_PROJECT:?set GOOGLE_CLOUD_PROJECT}"
REGION="${GOOGLE_CLOUD_LOCATION:-us-central1}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

gcloud services enable aiplatform.googleapis.com run.googleapis.com firestore.googleapis.com secretmanager.googleapis.com cloudbuild.googleapis.com --project "$PROJECT"

bash "$ROOT/deploy/deploy-mcp.sh"
MCP_URL="$(gcloud run services describe greenchain-mcp --region "$REGION" --project "$PROJECT" --format='value(status.url)')"

rm -rf "$ROOT/agent/bundled_fixtures"
cp -R "$ROOT/fixtures" "$ROOT/agent/bundled_fixtures"

gcloud run deploy greenchain-agent \
  --source "$ROOT/agent" \
  --region "$REGION" \
  --project "$PROJECT" \
  --allow-unauthenticated \
  --memory 1Gi \
  --set-env-vars "GOOGLE_GENAI_USE_VERTEXAI=TRUE,GOOGLE_CLOUD_LOCATION=$REGION,GOOGLE_CLOUD_PROJECT=$PROJECT,GEMINI_MODEL=gemini-3.7-flash,GREENCHAIN_STORE=firestore,GREENCHAIN_FIXTURES=/app/bundled_fixtures,MCP_URL=$MCP_URL"

AGENT_URL="$(gcloud run services describe greenchain-agent --region "$REGION" --project "$PROJECT" --format='value(status.url)')"

gcloud run deploy greenchain-web \
  --source "$ROOT/web" \
  --region "$REGION" \
  --project "$PROJECT" \
  --allow-unauthenticated \
  --set-env-vars "AGENT_URL=$AGENT_URL"

WEB_URL="$(gcloud run services describe greenchain-web --region "$REGION" --project "$PROJECT" --format='value(status.url)')"
gcloud run deploy greenchain-agent \
  --source "$ROOT/agent" \
  --region "$REGION" \
  --project "$PROJECT" \
  --allow-unauthenticated \
  --update-env-vars "WEB_ORIGIN=$WEB_URL,MCP_URL=$MCP_URL"

echo "Web: $WEB_URL"
echo "Agent: $AGENT_URL"
echo "MCP: $MCP_URL"
