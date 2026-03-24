# ============================================================================
# Firebase Module — Realtime Database & Hosting
# ============================================================================

variable "gcp_project_id" { type = string }

resource "google_project_service" "firebase" {
  provider = google-beta
  project  = var.gcp_project_id
  service  = "firebase.googleapis.com"

  disable_on_destroy = false
}

resource "google_firebase_project" "default" {
  provider = google-beta
  project  = var.gcp_project_id

  depends_on = [google_project_service.firebase]
}

resource "google_project_service" "firebasedatabase" {
  provider = google-beta
  project  = var.gcp_project_id
  service  = "firebasedatabase.googleapis.com"

  disable_on_destroy = false
}

resource "google_firebase_database_instance" "autoscaler_rtdb" {
  provider = google-beta
  project  = var.gcp_project_id
  region   = "us-central1"

  instance = "${var.gcp_project_id}-autoscaler"
  type     = "DEFAULT_DATABASE"

  depends_on = [
    google_firebase_project.default,
    google_project_service.firebasedatabase,
  ]
}

resource "google_project_service" "firebasehosting" {
  provider = google-beta
  project  = var.gcp_project_id
  service  = "firebasehosting.googleapis.com"

  disable_on_destroy = false
}
