"""
Cloud Function: Vertex AI Retraining Trigger.

Triggered when new training data arrives in the GCS bucket.
Launches a Vertex AI Custom Training Job to retrain the RL model.
"""
import os
import json
import logging

from google.cloud import aiplatform
from google.cloud import storage

logger = logging.getLogger(__name__)

GCP_PROJECT = os.environ.get("GCP_PROJECT_ID", "")
GCP_REGION = os.environ.get("GCP_REGION", "us-central1")
TRAINING_BUCKET = os.environ.get("TRAINING_BUCKET", "")


def trigger_retraining(event, context):
    """
    Cloud Function entry point.

    Triggered by a GCS finalize event (new object created).
    Only triggers retraining for files matching 'training-data/*.jsonl'.

    Args:
        event: GCS event payload with bucket, name, etc.
        context: Cloud Function context (event_id, timestamp, etc.).
    """
    file_name = event.get("name", "")
    bucket_name = event.get("bucket", "")

    logger.info(
        "GCS event: gs://%s/%s (type: %s)",
        bucket_name, file_name, event.get("contentType", "unknown"),
    )

    # Only trigger on training data files
    if not file_name.startswith("training-data/") or not file_name.endswith(".jsonl"):
        logger.info("Skipping non-training file: %s", file_name)
        return {"status": "skipped", "reason": "not a training data file"}

    try:
        # Initialize Vertex AI
        aiplatform.init(project=GCP_PROJECT, location=GCP_REGION)

        # Define the custom training job
        job = aiplatform.CustomContainerTrainingJob(
            display_name=f"rl-autoscaler-retrain-{context.event_id[:8]}",
            container_uri=f"gcr.io/{GCP_PROJECT}/rl-trainer:latest",
            staging_bucket=f"gs://{TRAINING_BUCKET}",
        )

        # Run the training job
        model = job.run(
            args=[
                "--data-path", f"gs://{bucket_name}/{file_name}",
                "--epochs", "100",
                "--output-dir", f"gs://{TRAINING_BUCKET}/models/",
            ],
            replica_count=1,
            machine_type="n1-standard-4",
            sync=False,  # Don't wait for job completion
        )

        logger.info("Vertex AI training job launched successfully")
        return {
            "status": "triggered",
            "job_display_name": job.display_name,
            "source_file": f"gs://{bucket_name}/{file_name}",
        }

    except Exception as e:
        logger.error("Failed to trigger retraining: %s", e)
        return {"status": "error", "error": str(e)}


def health_check(request):
    """HTTP health check endpoint."""
    return json.dumps({
        "status": "healthy",
        "project": GCP_PROJECT,
        "region": GCP_REGION,
    }), 200, {"Content-Type": "application/json"}
