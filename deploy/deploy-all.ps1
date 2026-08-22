param(
  [string]$Project = $env:GOOGLE_CLOUD_PROJECT,
  [string]$Region = "us-central1"
)

$ErrorActionPreference = "Stop"
& (Join-Path $PSScriptRoot "enable-apis.ps1") -Project $Project -Region $Region
& (Join-Path $PSScriptRoot "deploy-agent.ps1") -Project $Project -Region $Region
$agentUrl = gcloud run services describe greenchain-agent --region $Region --project $Project --format="value(status.url)"
& (Join-Path $PSScriptRoot "deploy-web.ps1") -Project $Project -Region $Region -AgentUrl $agentUrl
$webUrl = gcloud run services describe greenchain-web --region $Region --project $Project --format="value(status.url)"
& (Join-Path $PSScriptRoot "deploy-agent.ps1") -Project $Project -Region $Region -WebOrigin $webUrl
Write-Host "Web: $webUrl"
Write-Host "Agent: $agentUrl"
