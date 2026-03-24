"""
Tests for the Firebase sync module.
"""
import time
import pytest
from unittest.mock import patch, MagicMock
from firebase_bridge.sync import FirebaseSync


class TestFirebaseSyncOffline:
    """Tests for FirebaseSync in offline/mock mode."""

    def test_offline_init(self):
        """Should initialize in offline mode when no config provided."""
        sync = FirebaseSync()
        assert sync.online is False

    def test_push_decision_offline(self):
        """push_decision should return None in offline mode."""
        sync = FirebaseSync()
        result = sync.push_decision({
            "action": "SCALE_UP",
            "previous_replicas": 3,
            "new_replicas": 4,
            "confidence_score": 0.85,
        })
        assert result is None

    def test_update_health_offline(self):
        """update_health should not raise in offline mode."""
        sync = FirebaseSync()
        sync.update_health("healthy", {"episode": 10})

    def test_push_metrics_offline(self):
        """push_metrics should not raise in offline mode."""
        sync = FirebaseSync()
        sync.push_metrics({
            "cpu_utilization": 0.65,
            "memory_utilization": 0.45,
            "request_rate": 350.0,
        })

    def test_decision_gets_timestamp(self):
        """Pushed decisions should get a timestamp added."""
        sync = FirebaseSync()
        decision = {"action": "MAINTAIN", "previous_replicas": 3, "new_replicas": 3}
        # Even offline, the method adds timestamps to the dict
        sync.push_decision(decision)
        assert "timestamp" in decision
        assert "timestamp_iso" in decision

    def test_cleanup_offline(self):
        """cleanup_old_decisions should not raise in offline mode."""
        sync = FirebaseSync()
        sync.cleanup_old_decisions(max_keep=100)
