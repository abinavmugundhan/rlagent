"""
PPO (Proximal Policy Optimization) Agent for Kubernetes Autoscaling.

Actor-Critic architecture with separate policy (actor) and value (critic)
networks. Supports training, inference, and checkpoint save/load.
"""
import os
import logging
import argparse
from typing import List, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.distributions import Categorical

from .config import Config, AgentConfig
from .environment import AutoscaleEnv, ACTION_NAMES

logger = logging.getLogger(__name__)


class ActorCritic(nn.Module):
    """Shared-trunk actor-critic network."""

    def __init__(self, state_dim: int, action_dim: int, hidden_dim: int = 128):
        super().__init__()
        self.shared = nn.Sequential(
            nn.Linear(state_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.ReLU(),
        )
        self.actor = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, action_dim),
            nn.Softmax(dim=-1),
        )
        self.critic = nn.Sequential(
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Linear(hidden_dim // 2, 1),
        )

    def forward(self, state: torch.Tensor):
        features = self.shared(state)
        return self.actor(features), self.critic(features)

    def act(self, state: torch.Tensor) -> Tuple[int, torch.Tensor, torch.Tensor]:
        probs, value = self.forward(state)
        dist = Categorical(probs)
        action = dist.sample()
        return action.item(), dist.log_prob(action), value.squeeze(-1)

    def evaluate(
        self, states: torch.Tensor, actions: torch.Tensor
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        probs, values = self.forward(states)
        dist = Categorical(probs)
        log_probs = dist.log_prob(actions)
        entropy = dist.entropy()
        return log_probs, values.squeeze(-1), entropy


class RolloutBuffer:
    """Stores trajectory data for PPO updates."""

    def __init__(self):
        self.states: List[np.ndarray] = []
        self.actions: List[int] = []
        self.rewards: List[float] = []
        self.log_probs: List[float] = []
        self.values: List[float] = []
        self.dones: List[bool] = []

    def add(self, state, action, reward, log_prob, value, done):
        self.states.append(state)
        self.actions.append(action)
        self.rewards.append(reward)
        self.log_probs.append(log_prob)
        self.values.append(value)
        self.dones.append(done)

    def clear(self):
        self.__init__()

    def __len__(self):
        return len(self.states)


class PPOAgent:
    """
    Proximal Policy Optimization agent for autoscaling.

    Collects rollouts from the environment, computes GAE advantages,
    and updates the actor-critic network with clipped surrogate loss.
    """

    def __init__(self, config: AgentConfig = None):
        self.config = config or AgentConfig()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.network = ActorCritic(
            state_dim=self.config.state_dim,
            action_dim=self.config.action_dim,
            hidden_dim=self.config.hidden_dim,
        ).to(self.device)

        self.optimizer = optim.Adam(
            self.network.parameters(), lr=self.config.learning_rate
        )
        self.buffer = RolloutBuffer()

    def select_action(self, state: np.ndarray) -> Tuple[int, float, float]:
        """Select action using current policy."""
        state_t = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        with torch.no_grad():
            action, log_prob, value = self.network.act(state_t)
        return action, log_prob.item(), value.item()

    def get_action_probs(self, state: np.ndarray) -> np.ndarray:
        """Return action probability distribution for visualization."""
        state_t = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        with torch.no_grad():
            probs, _ = self.network(state_t)
        return probs.cpu().numpy().flatten()

    def compute_gae(
        self, rewards, values, dones, gamma, lam
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """Compute Generalized Advantage Estimation."""
        advantages = []
        gae = 0.0
        next_value = 0.0

        for t in reversed(range(len(rewards))):
            if dones[t]:
                next_value = 0.0
                gae = 0.0
            delta = rewards[t] + gamma * next_value - values[t]
            gae = delta + gamma * lam * gae
            advantages.insert(0, gae)
            next_value = values[t]

        advantages = torch.FloatTensor(advantages).to(self.device)
        returns = advantages + torch.FloatTensor(values).to(self.device)
        # Normalize advantages
        advantages = (advantages - advantages.mean()) / (advantages.std() + 1e-8)
        return advantages, returns

    def update(self) -> dict:
        """Perform PPO update using collected rollout data."""
        if len(self.buffer) == 0:
            return {}

        states = torch.FloatTensor(np.array(self.buffer.states)).to(self.device)
        actions = torch.LongTensor(self.buffer.actions).to(self.device)
        old_log_probs = torch.FloatTensor(self.buffer.log_probs).to(self.device)

        advantages, returns = self.compute_gae(
            self.buffer.rewards,
            self.buffer.values,
            self.buffer.dones,
            self.config.gamma,
            self.config.gae_lambda,
        )

        total_policy_loss = 0.0
        total_value_loss = 0.0
        total_entropy = 0.0

        for _ in range(self.config.update_epochs):
            log_probs, values, entropy = self.network.evaluate(states, actions)

            # PPO clipped surrogate loss
            ratio = torch.exp(log_probs - old_log_probs)
            surr1 = ratio * advantages
            surr2 = (
                torch.clamp(
                    ratio,
                    1.0 - self.config.clip_epsilon,
                    1.0 + self.config.clip_epsilon,
                )
                * advantages
            )
            policy_loss = -torch.min(surr1, surr2).mean()
            value_loss = nn.MSELoss()(values, returns)
            entropy_bonus = entropy.mean()

            loss = (
                policy_loss
                + self.config.value_loss_coeff * value_loss
                - self.config.entropy_coeff * entropy_bonus
            )

            self.optimizer.zero_grad()
            loss.backward()
            nn.utils.clip_grad_norm_(
                self.network.parameters(), self.config.max_grad_norm
            )
            self.optimizer.step()

            total_policy_loss += policy_loss.item()
            total_value_loss += value_loss.item()
            total_entropy += entropy_bonus.item()

        n = self.config.update_epochs
        self.buffer.clear()

        return {
            "policy_loss": total_policy_loss / n,
            "value_loss": total_value_loss / n,
            "entropy": total_entropy / n,
        }

    def save(self, path: str):
        """Save model checkpoint."""
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else ".", exist_ok=True)
        torch.save(
            {
                "network_state_dict": self.network.state_dict(),
                "optimizer_state_dict": self.optimizer.state_dict(),
                "config": self.config,
            },
            path,
        )
        logger.info("Checkpoint saved to %s", path)

    def load(self, path: str):
        """Load model checkpoint."""
        checkpoint = torch.load(path, map_location=self.device, weights_only=False)
        self.network.load_state_dict(checkpoint["network_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        logger.info("Checkpoint loaded from %s", path)


def train(config: Config, episodes: int = 50):
    """Training loop: run episodes, collect rollouts, update agent."""
    agent = PPOAgent(config.agent)
    env = AutoscaleEnv(config=config.env, max_steps=200)

    best_reward = -float("inf")

    for ep in range(1, episodes + 1):
        state, info = env.reset(seed=ep)
        episode_reward = 0.0
        decisions = []

        for step in range(env.max_steps):
            action, log_prob, value = agent.select_action(state)
            next_state, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated

            agent.buffer.add(state, action, reward, log_prob, value, done)
            episode_reward += reward
            state = next_state

            decisions.append({
                "step": step,
                "action": ACTION_NAMES[action],
                "replicas": info["replicas"],
                "cpu": info["metrics"]["cpu_utilization"],
                "reward": round(reward, 3),
            })

            if done:
                break

        # PPO update at end of each episode
        losses = agent.update()

        if episode_reward > best_reward:
            best_reward = episode_reward
            agent.save(os.path.join(config.checkpoint_dir, "best_model.pt"))

        logger.info(
            "Episode %d/%d | Reward: %.2f | Best: %.2f | "
            "Policy Loss: %.4f | Value Loss: %.4f",
            ep, episodes, episode_reward, best_reward,
            losses.get("policy_loss", 0), losses.get("value_loss", 0),
        )

        # Print a few sample decisions
        if ep % 10 == 0 or ep == 1:
            print(f"\n{'='*60}")
            print(f"Episode {ep} — Total Reward: {episode_reward:.2f}")
            print(f"{'='*60}")
            for d in decisions[:5]:
                print(
                    f"  Step {d['step']:3d} | {d['action']:11s} | "
                    f"Replicas: {d['replicas']:2d} | CPU: {d['cpu']:.2f} | "
                    f"R: {d['reward']:+.3f}"
                )
            if len(decisions) > 5:
                print(f"  ... ({len(decisions) - 5} more steps)")

    print(f"\nTraining complete. Best reward: {best_reward:.2f}")
    return agent


def main():
    parser = argparse.ArgumentParser(description="RL Autoscaler Agent")
    parser.add_argument("--simulate", action="store_true", default=True,
                        help="Use synthetic metrics (default: True)")
    parser.add_argument("--episodes", type=int, default=50,
                        help="Number of training episodes")
    parser.add_argument("--checkpoint", type=str, default=None,
                        help="Path to load checkpoint from")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    config = Config(simulate=args.simulate)
    agent = train(config, episodes=args.episodes)


if __name__ == "__main__":
    main()
