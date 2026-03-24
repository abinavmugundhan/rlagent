"""
Kubernetes Scaler — executes scaling commands against k3s.

Supports both real kubectl execution and dry-run mode for testing.
"""
import json
import logging
import subprocess
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class ScalingDecision:
    """Record of a scaling action."""
    previous_replicas: int
    new_replicas: int
    action: str  # "SCALE_UP", "SCALE_DOWN", "MAINTAIN"
    confidence_score: float
    cpu_utilization: float
    memory_utilization: float
    request_rate: float
    reason: str = ""

    def to_dict(self) -> dict:
        return {
            "previous_replicas": self.previous_replicas,
            "new_replicas": self.new_replicas,
            "action": self.action,
            "confidence_score": round(self.confidence_score, 4),
            "cpu_utilization": round(self.cpu_utilization, 4),
            "memory_utilization": round(self.memory_utilization, 4),
            "request_rate": round(self.request_rate, 2),
            "reason": self.reason,
        }


class K3sScaler:
    """
    Execute scaling operations against a k3s/Kubernetes cluster.

    In dry-run mode, only logs what would happen without touching the cluster.
    """

    def __init__(
        self,
        deployment: str = "web-app",
        namespace: str = "default",
        kubeconfig: str = "",
        dry_run: bool = True,
    ):
        self.deployment = deployment
        self.namespace = namespace
        self.kubeconfig = kubeconfig
        self.dry_run = dry_run

    def _build_kubectl_cmd(self, replicas: int) -> list:
        cmd = [
            "kubectl", "scale", "deployment",
            self.deployment,
            f"--replicas={replicas}",
            f"--namespace={self.namespace}",
        ]
        if self.kubeconfig:
            cmd.extend(["--kubeconfig", self.kubeconfig])
        return cmd

    def get_current_replicas(self) -> Optional[int]:
        """Query current replica count from the cluster."""
        if self.dry_run:
            return None

        try:
            cmd = [
                "kubectl", "get", "deployment",
                self.deployment,
                f"--namespace={self.namespace}",
                "-o", "jsonpath={.spec.replicas}",
            ]
            if self.kubeconfig:
                cmd.extend(["--kubeconfig", self.kubeconfig])

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return int(result.stdout.strip())
        except Exception as e:
            logger.error("Failed to get current replicas: %s", e)
        return None

    def scale(self, decision: ScalingDecision) -> bool:
        """
        Execute a scaling decision.

        Returns True if scaling was successful (or dry-run logged).
        """
        if decision.action == "MAINTAIN":
            logger.info(
                "MAINTAIN — keeping %d replicas (CPU: %.1f%%)",
                decision.previous_replicas,
                decision.cpu_utilization * 100,
            )
            return True

        if self.dry_run:
            logger.info(
                "[DRY-RUN] %s: %d → %d replicas | Confidence: %.2f | "
                "CPU: %.1f%% | RPS: %.0f",
                decision.action,
                decision.previous_replicas,
                decision.new_replicas,
                decision.confidence_score,
                decision.cpu_utilization * 100,
                decision.request_rate,
            )
            return True

        # Real scaling
        cmd = self._build_kubectl_cmd(decision.new_replicas)
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                logger.info(
                    "SCALED %s: %d → %d replicas | %s",
                    decision.action,
                    decision.previous_replicas,
                    decision.new_replicas,
                    result.stdout.strip(),
                )
                return True
            else:
                logger.error("kubectl scale failed: %s", result.stderr)
                return False
        except subprocess.TimeoutExpired:
            logger.error("kubectl scale timed out")
            return False
        except Exception as e:
            logger.error("Scaling failed: %s", e)
            return False

    def get_cluster_status(self) -> dict:
        """Get deployment status as a dict."""
        if self.dry_run:
            return {"mode": "dry-run", "deployment": self.deployment}

        try:
            cmd = [
                "kubectl", "get", "deployment",
                self.deployment,
                f"--namespace={self.namespace}",
                "-o", "json",
            ]
            if self.kubeconfig:
                cmd.extend(["--kubeconfig", self.kubeconfig])

            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return json.loads(result.stdout)
        except Exception as e:
            logger.error("Failed to get cluster status: %s", e)
        return {}
