# ============================================================================
# GCP Cloud Functions — Retraining Trigger
# ============================================================================

resource "google_project_service" "cloudfunctions" {
  service            = "cloudfunctions.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "cloudbuild" {
  service            = "cloudbuild.googleapis.com"
  disable_on_destroy = false
}

# Cloud Function source archive (placeholder — real source in cloud_functions/)
data "archive_file" "function_source" {
  type        = "zip"
  source_dir  = "${path.root}/../cloud_functions"
  output_path = "${path.root}/tmp/cloud_function_source.zip"
}

resource "google_storage_bucket_object" "function_source" {
  name   = "cloud-functions/retrain-trigger-${data.archive_file.function_source.output_md5}.zip"
  bucket = google_storage_bucket.cloud_functions.name
  source = data.archive_file.function_source.output_path
}

resource "google_cloudfunctions_function" "retrain_trigger" {
  name        = "rl-autoscaler-retrain-trigger-${var.environment}"
  description = "Triggers Vertex AI retraining when new data arrives in GCS"
  runtime     = "python311"

  available_memory_mb   = 256
  source_archive_bucket = google_storage_bucket.cloud_functions.name
  source_archive_object = google_storage_bucket_object.function_source.name
  entry_point           = "trigger_retraining"

  event_trigger {
    event_type = "google.storage.object.finalize"
    resource   = google_storage_bucket.training_data.name
  }

  environment_variables = {
    GCP_PROJECT_ID = var.gcp_project_id
    GCP_REGION     = var.gcp_region
    TRAINING_BUCKET = google_storage_bucket.training_data.name
  }

  service_account_email = google_service_account.cloud_function_sa.email

  depends_on = [
    google_project_service.cloudfunctions,
    google_project_service.cloudbuild,
  ]
}
