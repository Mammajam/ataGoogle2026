param(
  [string]$Project = $env:GOOGLE_CLOUD_PROJECT,
  [string]$Region = "us-central1"
)

if (-not $Project) {
  Write-Error "Set GOOGLE_CLOUD_PROJECT or pass -Project"
  exit 1
}

gcloud config set project $Project
gcloud services enable `
  aiplatform.googleapis.com `
  run.googleapis.com `
  firestore.googleapis.com `
  secretmanager.googleapis.com `
  cloudbuild.googleapis.com `
  artifactregistry.googleapis.com `
  --project $Project

Write-Host "Enabled Vertex AI, Cloud Run, Firestore, Secret Manager in $Project ($Region)"
Write-Host "Create a Firestore DB if you do not have one:"
Write-Host "  gcloud firestore databases create --location=$Region --project $Project"
