# ============================================================================
# GCP Vertex AI — Custom Training Job Configuration
# ============================================================================

# Enable required APIs
resource "google_project_service" "aiplatform" {
  service            = "aiplatform.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "compute" {
  service            = "compute.googleapis.com"
  disable_on_destroy = false
}

# Vertex AI custom training job specification
# This is defined as a template — actual jobs are triggered by Cloud Function
resource "google_storage_bucket_object" "training_config" {
  name   = "vertex-ai/training-config.json"
  bucket = google_storage_bucket.training_data.name

  content = jsonencode({
    displayName = "rl-autoscaler-training-${var.environment}"
    jobSpec = {
      workerPoolSpecs = [{
        machineSpec = {
          machineType = "n1-standard-4"
        }
        replicaCount = 1
        containerSpec = {
          imageUri = "gcr.io/${var.gcp_project_id}/rl-trainer:latest"
          args = [
            "--data-bucket", google_storage_bucket.training_data.name,
            "--epochs", "100",
            "--output-dir", "gs://${google_storage_bucket.training_data.name}/models/"
          ]
        }
      }]
    }
  })
}
