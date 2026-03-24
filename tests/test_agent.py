"""
Tests for the PPO Agent.
"""
import numpy as np
import pytest
from rl_agent.agent import PPOAgent, ActorCritic, RolloutBuffer
from rl_agent.config import AgentConfig


class TestActorCritic:
    """Tests for the ActorCritic neural network."""

    def test_forward_output_shapes(self):
        """Actor-critic should output correct shapes."""
        net = ActorCritic(state_dim=7, action_dim=3, hidden_dim=64)
        import torch
        state = torch.randn(1, 7)
        probs, value = net(state)
        assert probs.shape == (1, 3), f"Expected (1,3), got {probs.shape}"
        assert value.shape == (1, 1), f"Expected (1,1), got {value.shape}"

    def test_probs_sum_to_one(self):
        """Action probabilities should sum to 1."""
        net = ActorCritic(state_dim=7, action_dim=3)
        import torch
        state = torch.randn(1, 7)
        probs, _ = net(state)
        total = probs.sum().item()
        assert abs(total - 1.0) < 1e-5, f"Probs sum to {total}, expected 1.0"

    def test_act_returns_valid_action(self):
        """act() should return action in [0, 2]."""
        net = ActorCritic(state_dim=7, action_dim=3)
        import torch
        state = torch.randn(1, 7)
        action, log_prob, value = net.act(state)
        assert action in [0, 1, 2], f"Invalid action: {action}"
        assert isinstance(log_prob.item(), float)
        assert isinstance(value.item(), float)


class TestPPOAgent:
    """Tests for the PPO Agent."""

    def test_select_action(self):
        """Agent should select valid actions from random states."""
        agent = PPOAgent(AgentConfig(state_dim=7, action_dim=3, hidden_dim=32))
        state = np.random.randn(7).astype(np.float32)
        action, log_prob, value = agent.select_action(state)
        assert action in [0, 1, 2]
        assert isinstance(log_prob, float)
        assert isinstance(value, float)

    def test_get_action_probs(self):
        """Action probs should be valid probability distribution."""
        agent = PPOAgent(AgentConfig(state_dim=7, action_dim=3, hidden_dim=32))
        state = np.random.randn(7).astype(np.float32)
        probs = agent.get_action_probs(state)
        assert probs.shape == (3,)
        assert abs(probs.sum() - 1.0) < 1e-5
        assert all(p >= 0 for p in probs)

    def test_update_with_empty_buffer(self):
        """Update with empty buffer should return empty dict."""
        agent = PPOAgent(AgentConfig(state_dim=7, action_dim=3, hidden_dim=32))
        result = agent.update()
        assert result == {}

    def test_update_with_data(self):
        """Update should produce valid loss values."""
        agent = PPOAgent(AgentConfig(
            state_dim=7, action_dim=3, hidden_dim=32, update_epochs=2
        ))
        # Fill buffer with some data
        for _ in range(20):
            state = np.random.randn(7).astype(np.float32)
            action, log_prob, value = agent.select_action(state)
            agent.buffer.add(state, action, np.random.randn(), log_prob, value, False)

        result = agent.update()
        assert "policy_loss" in result
        assert "value_loss" in result
        assert "entropy" in result
        assert isinstance(result["policy_loss"], float)

    def test_save_load(self, tmp_path):
        """Save and load should preserve network weights."""
        agent = PPOAgent(AgentConfig(state_dim=7, action_dim=3, hidden_dim=32))
        state = np.random.randn(7).astype(np.float32)
        probs_before = agent.get_action_probs(state)

        path = str(tmp_path / "test_model.pt")
        agent.save(path)

        agent2 = PPOAgent(AgentConfig(state_dim=7, action_dim=3, hidden_dim=32))
        agent2.load(path)
        probs_after = agent2.get_action_probs(state)

        np.testing.assert_array_almost_equal(probs_before, probs_after, decimal=5)


class TestRolloutBuffer:
    """Tests for the RolloutBuffer."""

    def test_add_and_length(self):
        buf = RolloutBuffer()
        assert len(buf) == 0
        buf.add(np.zeros(7), 1, 0.5, -0.1, 0.3, False)
        assert len(buf) == 1

    def test_clear(self):
        buf = RolloutBuffer()
        buf.add(np.zeros(7), 0, 1.0, -0.5, 0.2, True)
        buf.clear()
        assert len(buf) == 0
