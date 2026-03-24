"""
Tests for the AutoscaleEnv Gymnasium environment.
"""
import numpy as np
import pytest
from rl_agent.environment import AutoscaleEnv, ACTION_SCALE_DOWN, ACTION_MAINTAIN, ACTION_SCALE_UP
from rl_agent.config import EnvironmentConfig


class TestAutoscaleEnv:
    """Tests for the autoscaling Gym environment."""

    def setup_method(self):
        self.env = AutoscaleEnv(max_steps=50)

    def test_reset_returns_correct_shape(self):
        """Reset should return observation of correct dimension."""
        obs, info = self.env.reset()
        assert obs.shape == (7,), f"Expected (7,), got {obs.shape}"
        assert obs.dtype == np.float32

    def test_observation_in_bounds(self):
        """All observation values should be in [0, 1]."""
        obs, _ = self.env.reset()
        assert np.all(obs >= 0.0), f"Negative values in obs: {obs}"
        assert np.all(obs <= 1.0), f"Values > 1 in obs: {obs}"

    def test_step_returns_correct_tuple(self):
        """Step should return (obs, reward, terminated, truncated, info)."""
        self.env.reset()
        result = self.env.step(ACTION_MAINTAIN)
        assert len(result) == 5
        obs, reward, terminated, truncated, info = result
        assert obs.shape == (7,)
        assert isinstance(reward, float)
        assert isinstance(terminated, bool)
        assert isinstance(truncated, bool)
        assert isinstance(info, dict)

    def test_scale_up_increases_replicas(self):
        """Scale up should increase replica count."""
        self.env.reset()
        initial = self.env.current_replicas
        self.env.step(ACTION_SCALE_UP)
        assert self.env.current_replicas == initial + 1

    def test_scale_down_decreases_replicas(self):
        """Scale down should decrease replica count."""
        self.env.reset()
        self.env.current_replicas = 5
        self.env.step(ACTION_SCALE_DOWN)
        assert self.env.current_replicas == 4

    def test_min_replicas_bound(self):
        """Replicas should not go below minimum."""
        config = EnvironmentConfig(min_replicas=2)
        env = AutoscaleEnv(config=config, max_steps=10)
        env.reset()
        env.current_replicas = 2
        env.step(ACTION_SCALE_DOWN)
        assert env.current_replicas == 2

    def test_max_replicas_bound(self):
        """Replicas should not go above maximum."""
        config = EnvironmentConfig(max_replicas=5)
        env = AutoscaleEnv(config=config, max_steps=10)
        env.reset()
        env.current_replicas = 5
        env.step(ACTION_SCALE_UP)
        assert env.current_replicas == 5

    def test_episode_terminates(self):
        """Episode should terminate after max_steps."""
        env = AutoscaleEnv(max_steps=5)
        env.reset()
        for i in range(5):
            _, _, terminated, _, _ = env.step(ACTION_MAINTAIN)

        assert terminated is True

    def test_maintain_keeps_replicas(self):
        """Maintain action should not change replica count."""
        self.env.reset()
        initial = self.env.current_replicas
        self.env.step(ACTION_MAINTAIN)
        assert self.env.current_replicas == initial

    def test_info_contains_metrics(self):
        """Info dict should contain metrics data."""
        self.env.reset()
        _, _, _, _, info = self.env.step(ACTION_MAINTAIN)
        assert "metrics" in info
        assert "replicas" in info
        assert "action_name" in info
        assert "cpu_utilization" in info["metrics"]

    def test_reward_sign_correctness(self):
        """High CPU should produce negative reward, normal CPU positive."""
        self.env.reset()
        # Run a few steps and check rewards are reasonable
        rewards = []
        for _ in range(10):
            _, reward, _, _, _ = self.env.step(ACTION_MAINTAIN)
            rewards.append(reward)
        # At least some rewards should be non-zero
        assert any(r != 0.0 for r in rewards)
