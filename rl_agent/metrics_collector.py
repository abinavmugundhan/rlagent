"""
Prometheus Metrics Collector with synthetic fallback.

Fetches CPU utilization, memory utilization, and request rate
from a Prometheus server. Falls back to realistic synthetic data
generation for development/testing.
"""
import math
import time
import random
import logging
from dataclasses import dataclass
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class MetricsSnapshot:
    """A single observation of cluster metrics."""
    cpu_utilization: float      # 0.0 – 1.0
    memory_utilization: float   # 0.0 – 1.0
    request_rate: float         # requests per second
    timestamp: float            # epoch seconds

    def to_dict(self) -> dict:
        return {
            "cpu_utilization": round(self.cpu_utilization, 4),
            "memory_utilization": round(self.memory_utilization, 4),
            "request_rate": round(self.request_rate, 2),
            "timestamp": self.timestamp,
        }


class PrometheusCollector:
    """Fetch real metrics from a Prometheus endpoint."""

    def __init__(self, prometheus_url: str):
        self.url = prometheus_url.rstrip("/")

    def query(self, promql: str) -> Optional[float]:
        try:
            import requests
            resp = requests.get(
                f"{self.url}/api/v1/query",
                params={"query": promql},
                timeout=5,
            )
            data = resp.json()
            if data["status"] == "success" and data["data"]["result"]:
                return float(data["data"]["result"][0]["value"][1])
        except Exception as e:
            logger.warning("Prometheus query failed: %s", e)
        return None

    def collect(self) -> Optional[MetricsSnapshot]:
        cpu = self.query(
            '1 - avg(rate(node_cpu_seconds_total{mode="idle"}[2m]))'
        )
        mem = self.query(
            '1 - (node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes)'
        )
        rps = self.query(
            'sum(rate(http_requests_total[1m]))'
        )
        if cpu is not None and mem is not None and rps is not None:
            return MetricsSnapshot(
                cpu_utilization=cpu,
                memory_utilization=mem,
                request_rate=rps,
                timestamp=time.time(),
            )
        return None


class SyntheticCollector:
    """
    Generate realistic synthetic metrics for development.

    Simulates a diurnal traffic pattern with random spikes,
    correlated CPU/memory usage, and noise.
    """

    def __init__(self, seed: int = 42):
        self._rng = np.random.default_rng(seed)
        self._step = 0
        self._spike_active = False
        self._spike_remaining = 0

    def collect(self) -> MetricsSnapshot:
        hour = (self._step * 0.25) % 24  # each step ≈ 15-min
        # Diurnal pattern: peak at 14:00, trough at 04:00
        base_load = 0.3 + 0.35 * math.sin(math.pi * (hour - 4) / 12)
        base_load = max(0.05, min(base_load, 0.95))

        # Random traffic spikes
        if not self._spike_active and self._rng.random() < 0.08:
            self._spike_active = True
            self._spike_remaining = self._rng.integers(2, 8)
        if self._spike_active:
            base_load = min(base_load + self._rng.uniform(0.15, 0.4), 0.98)
            self._spike_remaining -= 1
            if self._spike_remaining <= 0:
                self._spike_active = False

        noise = self._rng.normal(0, 0.03)
        cpu = np.clip(base_load + noise, 0.01, 0.99)
        mem = np.clip(cpu * self._rng.uniform(0.7, 1.1) + self._rng.normal(0, 0.02), 0.01, 0.99)
        rps = max(1.0, base_load * 1000 + self._rng.normal(0, 30))

        self._step += 1
        return MetricsSnapshot(
            cpu_utilization=float(cpu),
            memory_utilization=float(mem),
            request_rate=float(rps),
            timestamp=time.time(),
        )


def create_collector(prometheus_url: str = "", simulate: bool = True):
    """Factory: return the appropriate metrics collector."""
    if simulate:
        logger.info("Using SYNTHETIC metrics collector")
        return SyntheticCollector()
    logger.info("Using PROMETHEUS collector at %s", prometheus_url)
    return PrometheusCollector(prometheus_url)
