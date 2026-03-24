# ============================================================================
# GCP IAM — Least-Privilege Service Accounts
# ============================================================================

# Service account for Cloud Function (retraining trigger)
resource "google_service_account" "cloud_function_sa" {
  account_id   = "rl-retrain-trigger-${var.environment}"
  display_name = "RL Autoscaler Retrain Trigger"
  description  = "Service account for the Cloud Function that triggers Vertex AI retraining"
}

# Allow Cloud Function SA to launch Vertex AI training jobs
resource "google_project_iam_member" "function_vertex_ai" {
  project = var.gcp_project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.cloud_function_sa.email}"
}

# Allow Cloud Function SA to read from GCS training bucket
resource "google_project_iam_member" "function_gcs_reader" {
  project = var.gcp_project_id
  role    = "roles/storage.objectViewer"
  member  = "serviceAccount:${google_service_account.cloud_function_sa.email}"
}

# Service account for Vertex AI training jobs
resource "google_service_account" "vertex_ai_sa" {
  account_id   = "rl-vertex-trainer-${var.environment}"
  display_name = "RL Autoscaler Vertex AI Trainer"
  description  = "Service account for Vertex AI custom training jobs"
}

# Allow Vertex AI SA to read/write GCS (model artifacts)
resource "google_project_iam_member" "vertex_gcs_writer" {
  project = var.gcp_project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.vertex_ai_sa.email}"
}

# Allow Vertex AI SA to use AI Platform
resource "google_project_iam_member" "vertex_ai_user" {
  project = var.gcp_project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.vertex_ai_sa.email}"
}
