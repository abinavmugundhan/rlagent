"""
Tests for the K3s Scaler.
"""
import pytest
from rl_agent.scaler import K3sScaler, ScalingDecision


class TestScalingDecision:
    """Tests for the ScalingDecision dataclass."""

    def test_to_dict(self):
        decision = ScalingDecision(
            previous_replicas=3,
            new_replicas=4,
            action="SCALE_UP",
            confidence_score=0.87654,
            cpu_utilization=0.72345,
            memory_utilization=0.55123,
            request_rate=456.789,
            reason="CPU above target",
        )
        d = decision.to_dict()
        assert d["previous_replicas"] == 3
        assert d["new_replicas"] == 4
        assert d["action"] == "SCALE_UP"
        assert d["confidence_score"] == 0.8765
        assert d["cpu_utilization"] == 0.7235
        assert d["request_rate"] == 456.79
        assert d["reason"] == "CPU above target"


class TestK3sScaler:
    """Tests for the K3sScaler in dry-run mode."""

    def setup_method(self):
        self.scaler = K3sScaler(
            deployment="web-app",
            namespace="default",
            dry_run=True,
        )

    def test_dry_run_scale_up(self):
        """Dry-run scale up should succeed without kubectl."""
        decision = ScalingDecision(
            previous_replicas=3, new_replicas=4, action="SCALE_UP",
            confidence_score=0.9, cpu_utilization=0.8,
            memory_utilization=0.6, request_rate=500.0,
        )
        assert self.scaler.scale(decision) is True

    def test_dry_run_scale_down(self):
        """Dry-run scale down should succeed."""
        decision = ScalingDecision(
            previous_replicas=5, new_replicas=4, action="SCALE_DOWN",
            confidence_score=0.75, cpu_utilization=0.3,
            memory_utilization=0.25, request_rate=100.0,
        )
        assert self.scaler.scale(decision) is True

    def test_maintain_always_succeeds(self):
        """Maintain action should always return True."""
        decision = ScalingDecision(
            previous_replicas=3, new_replicas=3, action="MAINTAIN",
            confidence_score=0.5, cpu_utilization=0.6,
            memory_utilization=0.5, request_rate=300.0,
        )
        assert self.scaler.scale(decision) is True

    def test_get_current_replicas_dry_run(self):
        """Dry-run should return None for current replicas."""
        assert self.scaler.get_current_replicas() is None

    def test_get_cluster_status_dry_run(self):
        """Dry-run cluster status should indicate dry-run mode."""
        status = self.scaler.get_cluster_status()
        assert status["mode"] == "dry-run"

    def test_kubectl_command_build(self):
        """Should build correct kubectl command."""
        cmd = self.scaler._build_kubectl_cmd(5)
        assert "kubectl" in cmd
        assert "scale" in cmd
        assert "--replicas=5" in cmd
        assert "--namespace=default" in cmd
