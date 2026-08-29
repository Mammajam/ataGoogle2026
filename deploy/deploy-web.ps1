param(
  [string]$Project = $env:GOOGLE_CLOUD_PROJECT,
  [string]$Region = "us-central1",
  [string]$Service = "greenchain-web",
  [Parameter(Mandatory = $true)][string]$AgentUrl
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
if (-not $Project) { throw "Set GOOGLE_CLOUD_PROJECT or pass -Project" }

gcloud run deploy $Service `
  --source (Join-Path $Root "web") `
  --region $Region `
  --project $Project `
  --allow-unauthenticated `
  --memory 512Mi `
  --set-env-vars "AGENT_URL=$AgentUrl"

Write-Host "After web has a URL, redeploy the agent with -WebOrigin <web-url> so CORS is tight."
