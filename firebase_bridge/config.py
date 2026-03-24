"""
Firebase Bridge configuration.
"""
import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()


@dataclass
class FirebaseBridgeConfig:
    """Firebase connection settings."""
    service_account_path: str = os.getenv(
        "FIREBASE_SA_PATH", "firebase-service-account.json"
    )
    database_url: str = os.getenv("FIREBASE_DB_URL", "")
    project_id: str = os.getenv("FIREBASE_PROJECT_ID", "")
    decisions_path: str = "/autoscaler/decisions"
    health_path: str = "/autoscaler/health"
    metrics_path: str = "/autoscaler/metrics"
    max_decisions_stored: int = 500
