# Optional. Create in GCP; never commit values.
# gcloud secrets create greenchain-vertex-sa --data-file=service-account.json
# Then grant the Cloud Run runtime SA secretAccessor and set
# GOOGLE_APPLICATION_CREDENTIALS from a mounted secret, or use the default compute SA with Vertex User.
#
# Live factors (Climatiq):
#   gcloud secrets create climatiq-api-key --data-file=-
#   Bind to Cloud Run as CLIMATIQ_API_KEY.
#
# Live ERP:
#   GREENCHAIN_ERP_URL and GREENCHAIN_ERP_TOKEN via Secret Manager.
#
# Firestore rules (deny-all client; agent uses ADC):
#   npx -y firebase-tools@latest deploy --only firestore:rules,storage:rules --project $GOOGLE_CLOUD_PROJECT

