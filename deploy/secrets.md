# Optional. Create in GCP; never commit values.
# gcloud secrets create greenchain-vertex-sa --data-file=service-account.json
# Then grant the Cloud Run runtime SA secretAccessor and set
# GOOGLE_APPLICATION_CREDENTIALS from a mounted secret, or use the default compute SA with Vertex User.
