param(
  [string]$Project = $env:GOOGLE_CLOUD_PROJECT,
  [string]$Region = "us-central1",
  [string]$Service = "greenchain-agent",
  [string]$WebOrigin = $env:WEB_ORIGIN,
  [string]$McpUrl = $env:MCP_URL
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

if (-not $Project) { throw "Set GOOGLE_CLOUD_PROJECT or pass -Project" }

$bundle = Join-Path $Root "agent\bundled_fixtures"
if (Test-Path $bundle) { Remove-Item $bundle -Recurse -Force }
Copy-Item (Join-Path $Root "fixtures") $bundle -Recurse

$envArgs = @(
  "GOOGLE_GENAI_USE_VERTEXAI=TRUE",
  "GOOGLE_CLOUD_LOCATION=$Region",
  "GOOGLE_CLOUD_PROJECT=$Project",
  "GEMINI_MODEL=gemini-3.7-flash",
  "GREENCHAIN_STORE=firestore",
  "GREENCHAIN_FIXTURES=/app/bundled_fixtures"
)
if ($WebOrigin) { $envArgs += "WEB_ORIGIN=$WebOrigin" }
if ($McpUrl) { $envArgs += "MCP_URL=$McpUrl" }

gcloud run deploy $Service `
  --source (Join-Path $Root "agent") `
  --region $Region `
  --project $Project `
  --allow-unauthenticated `
  --memory 1Gi `
  --cpu 1 `
  --set-env-vars ($envArgs -join ",")

Write-Host "Agent deploy requested. Bind Vertex credentials via Secret Manager / Cloud Run SA — do not commit keys."
