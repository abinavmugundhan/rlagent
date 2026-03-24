# ============================================================================
# GCP — Google Cloud Storage (training data from S3 transfer)
# ============================================================================

resource "google_storage_bucket" "training_data" {
  name          = "${var.gcs_bucket_name}-${var.environment}"
  location      = var.gcp_region
  force_destroy = var.environment != "prod"

  uniform_bucket_level_access = true

  versioning {
    enabled = true
  }

  lifecycle_rule {
    action {
      type          = "SetStorageClass"
      storage_class = "NEARLINE"
    }
    condition {
      age = 30
    }
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 365
    }
  }

  labels = {
    project     = "rl-autoscaler"
    environment = var.environment
  }
}

# Upload directory for Cloud Function source
resource "google_storage_bucket" "cloud_functions" {
  name          = "rl-autoscaler-functions-${var.environment}"
  location      = var.gcp_region
  force_destroy = true

  uniform_bucket_level_access = true

  labels = {
    project     = "rl-autoscaler"
    environment = var.environment
  }
}
