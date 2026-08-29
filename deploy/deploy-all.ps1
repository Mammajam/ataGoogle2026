param(
  [string]$Project = $env:GOOGLE_CLOUD_PROJECT,
  [string]$Region = "us-central1"
)

$ErrorActionPreference = "Stop"
& (Join-Path $PSScriptRoot "enable-apis.ps1") -Project $Project -Region $Region
& (Join-Path $PSScriptRoot "deploy-mcp.ps1") -Project $Project -Region $Region
$mcpUrl = gcloud run services describe greenchain-mcp --region $Region --project $Project --format="value(status.url)"
& (Join-Path $PSScriptRoot "deploy-agent.ps1") -Project $Project -Region $Region -McpUrl $mcpUrl
$agentUrl = gcloud run services describe greenchain-agent --region $Region --project $Project --format="value(status.url)"
& (Join-Path $PSScriptRoot "deploy-web.ps1") -Project $Project -Region $Region -AgentUrl $agentUrl
$webUrl = gcloud run services describe greenchain-web --region $Region --project $Project --format="value(status.url)"
& (Join-Path $PSScriptRoot "deploy-agent.ps1") -Project $Project -Region $Region -WebOrigin $webUrl -McpUrl $mcpUrl
Write-Host "Web: $webUrl"
Write-Host "Agent: $agentUrl"
Write-Host "MCP: $mcpUrl"
