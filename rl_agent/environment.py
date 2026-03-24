"""
OpenAI Gymnasium-compatible environment for Kubernetes autoscaling.

State:  [cpu_util, mem_util, request_rate_norm, replicas_norm,
         hour_sin, hour_cos, day_of_week_norm]
Actions: 0 = scale_down, 1 = maintain, 2 = scale_up
Reward: penalizes over-provisioning (waste) and under-provisioning (SLA risk).
"""
import math
import logging
from typing import Optional, Tuple

import numpy as np
import gymnasium as gym
from gymnasium import spaces

from .config import EnvironmentConfig
from .metrics_collector import SyntheticCollector, MetricsSnapshot

logger = logging.getLogger(__name__)

ACTION_SCALE_DOWN = 0
ACTION_MAINTAIN = 1
ACTION_SCALE_UP = 2
ACTION_NAMES = {0: "SCALE_DOWN", 1: "MAINTAIN", 2: "SCALE_UP"}


class AutoscaleEnv(gym.Env):
    """
    RL environment that simulates Kubernetes autoscaling decisions.

    The agent observes cluster metrics and decides whether to scale
    up, scale down, or maintain the current replica count.
    """

    metadata = {"render_modes": ["human"]}

    def __init__(
        self,
        config: Optional[EnvironmentConfig] = None,
        collector=None,
        max_steps: int = 200,
    ):
        super().__init__()
        self.config = config or EnvironmentConfig()
        self.collector = collector or SyntheticCollector()
        self.max_steps = max_steps

        # Spaces
        self.observation_space = spaces.Box(
            low=0.0, high=1.0, shape=(7,), dtype=np.float32
        )
        self.action_space = spaces.Discrete(3)

        # State
        self.current_replicas = 3
        self.step_count = 0
        self.last_metrics: Optional[MetricsSnapshot] = None

    def _get_obs(self, metrics: MetricsSnapshot) -> np.ndarray:
        """Convert raw metrics into normalized observation vector."""
        hour = (self.step_count * 0.25) % 24
        day = (self.step_count // 96) % 7
        return np.array([
            metrics.cpu_utilization,
            metrics.memory_utilization,
            min(metrics.request_rate / 1200.0, 1.0),  # normalize RPS
            self.current_replicas / self.config.max_replicas,
            (math.sin(2 * math.pi * hour / 24) + 1) / 2,
            (math.cos(2 * math.pi * hour / 24) + 1) / 2,
            day / 6.0,
        ], dtype=np.float32)

    def _compute_reward(self, metrics: MetricsSnapshot, action: int) -> float:
        """
        Reward function:
        - Penalize CPU > target (under-provisioned, SLA risk)
        - Penalize CPU < target * 0.3 (over-provisioned, waste)
        - Small bonus for keeping CPU near target
        - Penalize unnecessary scaling actions
        """
        cpu = metrics.cpu_utilization
        target = self.config.target_cpu
        reward = 0.0

        # SLA violation penalty (exponential)
        if cpu > target + 0.1:
            reward -= 2.0 * ((cpu - target) ** 2)

        # Over-provisioning penalty
        elif cpu < target * 0.3:
            reward -= 0.5 * ((target * 0.3 - cpu) ** 2)

        # Sweet-spot bonus
        else:
            reward += 1.0 - abs(cpu - target)

        # Action cost: scaling has a small cost, maintaining is free
        if action != ACTION_MAINTAIN:
            reward -= 0.05

        # Boundary penalties
        if self.current_replicas <= self.config.min_replicas and action == ACTION_SCALE_DOWN:
            reward -= 1.0
        if self.current_replicas >= self.config.max_replicas and action == ACTION_SCALE_UP:
            reward -= 1.0

        return float(reward)

    def reset(self, seed=None, options=None) -> Tuple[np.ndarray, dict]:
        super().reset(seed=seed)
        self.current_replicas = 3
        self.step_count = 0
        self.collector = SyntheticCollector(
            seed=seed if seed is not None else 42
        )
        metrics = self.collector.collect()
        self.last_metrics = metrics
        return self._get_obs(metrics), {"metrics": metrics.to_dict()}

    def step(self, action: int) -> Tuple[np.ndarray, float, bool, bool, dict]:
        # Apply action
        if action == ACTION_SCALE_DOWN:
            self.current_replicas = max(
                self.config.min_replicas, self.current_replicas - 1
            )
        elif action == ACTION_SCALE_UP:
            self.current_replicas = min(
                self.config.max_replicas, self.current_replicas + 1
            )

        # Collect new metrics (simulated load adapts slightly to replica count)
        metrics = self.collector.collect()
        # More replicas → lower per-pod CPU
        load_factor = max(0.3, 1.0 - (self.current_replicas - 3) * 0.04)
        metrics = MetricsSnapshot(
            cpu_utilization=min(0.99, metrics.cpu_utilization * load_factor),
            memory_utilization=min(0.99, metrics.memory_utilization * load_factor),
            request_rate=metrics.request_rate,
            timestamp=metrics.timestamp,
        )
        self.last_metrics = metrics

        reward = self._compute_reward(metrics, action)
        self.step_count += 1
        terminated = self.step_count >= self.max_steps
        truncated = False

        info = {
            "metrics": metrics.to_dict(),
            "replicas": self.current_replicas,
            "action_name": ACTION_NAMES[action],
            "step": self.step_count,
        }

        logger.debug(
            "Step %d | Action: %s | Replicas: %d | CPU: %.2f | Reward: %.3f",
            self.step_count, ACTION_NAMES[action],
            self.current_replicas, metrics.cpu_utilization, reward,
        )

        return self._get_obs(metrics), reward, terminated, truncated, info
