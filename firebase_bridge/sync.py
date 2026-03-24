"""
Firebase Realtime Database sync for autoscaling decisions.

Pushes scaling decisions, health heartbeats, and metrics snapshots
to Firebase RTDB for the real-time dashboard to consume.
"""
import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Lazy imports to avoid hard dependency when Firebase is not configured
_firebase_admin = None
_db = None


def _init_firebase(service_account_path: str, database_url: str, project_id: str):
    """Initialize Firebase Admin SDK (idempotent)."""
    global _firebase_admin, _db
    if _firebase_admin is not None:
        return True

    try:
        import firebase_admin
        from firebase_admin import credentials, db

        _firebase_admin = firebase_admin
        _db = db

        # Check if already initialized
        try:
            firebase_admin.get_app()
        except ValueError:
            cred = credentials.Certificate(service_account_path)
            firebase_admin.initialize_app(cred, {
                "databaseURL": database_url,
                "projectId": project_id,
            })

        logger.info("Firebase Admin SDK initialized successfully")
        return True

    except FileNotFoundError:
        logger.warning(
            "Firebase service account file not found: %s. "
            "Running in offline mode.", service_account_path
        )
        return False
    except Exception as e:
        logger.warning("Firebase initialization failed: %s. Running in offline mode.", e)
        return False


class FirebaseSync:
    """
    Sync autoscaler state to Firebase Realtime Database.

    Falls back to local logging if Firebase is not configured.
    """

    def __init__(
        self,
        service_account_path: str = "",
        database_url: str = "",
        project_id: str = "",
        decisions_path: str = "/autoscaler/decisions",
        health_path: str = "/autoscaler/health",
        metrics_path: str = "/autoscaler/metrics",
    ):
        self.decisions_path = decisions_path
        self.health_path = health_path
        self.metrics_path = metrics_path
        self.online = False

        if database_url and service_account_path:
            self.online = _init_firebase(
                service_account_path, database_url, project_id
            )

        if not self.online:
            logger.info("FirebaseSync running in OFFLINE mode (local logging only)")

    def push_decision(self, decision: dict) -> Optional[str]:
        """
        Push a scaling decision to Firebase RTDB.

        Args:
            decision: Dict with keys like previous_replicas, new_replicas,
                      confidence_score, action, metrics_snapshot.

        Returns:
            Firebase push key if online, None otherwise.
        """
        decision["timestamp"] = time.time()
        decision["timestamp_iso"] = time.strftime(
            "%Y-%m-%dT%H:%M:%SZ", time.gmtime()
        )

        if self.online and _db:
            try:
                ref = _db.reference(self.decisions_path)
                result = ref.push(decision)
                logger.debug("Pushed decision to Firebase: %s", result.key)
                return result.key
            except Exception as e:
                logger.error("Failed to push decision to Firebase: %s", e)
                return None
        else:
            logger.info(
                "[OFFLINE] Decision: %s %d→%d (confidence: %.2f)",
                decision.get("action", "?"),
                decision.get("previous_replicas", 0),
                decision.get("new_replicas", 0),
                decision.get("confidence_score", 0),
            )
            return None

    def update_health(self, status: str = "healthy", extra: dict = None):
        """
        Update the agent health heartbeat in Firebase.

        This lets the dashboard know the agent is alive and operational.
        """
        health_data = {
            "status": status,
            "last_heartbeat": time.time(),
            "last_heartbeat_iso": time.strftime(
                "%Y-%m-%dT%H:%M:%SZ", time.gmtime()
            ),
        }
        if extra:
            health_data.update(extra)

        if self.online and _db:
            try:
                ref = _db.reference(self.health_path)
                ref.set(health_data)
                logger.debug("Health heartbeat updated")
            except Exception as e:
                logger.error("Failed to update health: %s", e)
        else:
            logger.info("[OFFLINE] Health: %s", status)

    def push_metrics(self, metrics: dict):
        """Push a metrics snapshot to Firebase for live display."""
        metrics["timestamp"] = time.time()

        if self.online and _db:
            try:
                ref = _db.reference(self.metrics_path)
                ref.push(metrics)
            except Exception as e:
                logger.error("Failed to push metrics: %s", e)
        else:
            logger.debug(
                "[OFFLINE] Metrics: CPU=%.2f MEM=%.2f RPS=%.0f",
                metrics.get("cpu_utilization", 0),
                metrics.get("memory_utilization", 0),
                metrics.get("request_rate", 0),
            )

    def cleanup_old_decisions(self, max_keep: int = 500):
        """Remove old decisions to prevent unbounded RTDB growth."""
        if not self.online or not _db:
            return

        try:
            ref = _db.reference(self.decisions_path)
            snapshot = ref.order_by_child("timestamp").get()
            if snapshot and len(snapshot) > max_keep:
                keys = list(snapshot.keys())
                to_delete = keys[: len(keys) - max_keep]
                for key in to_delete:
                    ref.child(key).delete()
                logger.info("Cleaned up %d old decisions", len(to_delete))
        except Exception as e:
            logger.error("Failed to cleanup old decisions: %s", e)
