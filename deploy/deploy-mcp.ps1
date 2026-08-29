param(
  [string]$Project = $env:GOOGLE_CLOUD_PROJECT,
  [string]$Region = "us-central1",
  [string]$Service = "greenchain-mcp"
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
if (-not $Project) { throw "Set GOOGLE_CLOUD_PROJECT or pass -Project" }

$image = "$Region-docker.pkg.dev/$Project/cloud-run-source-deploy/greenchain-mcp"
gcloud artifacts repositories describe cloud-run-source-deploy --location=$Region --project=$Project 2>$null
gcloud builds submit $Root `
  --project $Project `
  --config (Join-Path $PSScriptRoot "mcp-cloudbuild.yaml") `
  --substitutions "_IMAGE=$image"

gcloud run deploy $Service `
  --image $image `
  --region $Region `
  --project $Project `
  --allow-unauthenticated `
  --memory 512Mi `
  --cpu 1 `
  --port 8081

Write-Host "MCP deploy requested. Set MCP_URL on the agent to this service URL."
