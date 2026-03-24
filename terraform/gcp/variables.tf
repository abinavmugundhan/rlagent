# ============================================================================
# GCP Module Variables & Outputs
# ============================================================================

variable "environment" { type = string }
variable "gcp_project_id" { type = string }
variable "gcp_region" { type = string }
variable "gcs_bucket_name" { type = string }

output "gcs_bucket_url" {
  value = google_storage_bucket.training_data.url
}

output "vertex_ai_endpoint" {
  value = "https://${var.gcp_region}-aiplatform.googleapis.com"
}

output "cloud_function_url" {
  value = google_cloudfunctions_function.retrain_trigger.https_trigger_url
}
