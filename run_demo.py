"""
Demo Runner — Runs the RL Agent and writes decisions to a local JSON file
that the dashboard can read via a simple API server.

Usage:
    python run_demo.py
"""
import os
import sys
import json
import time
import logging
import threading
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

import numpy as np

from rl_agent.agent import PPOAgent
from rl_agent.environment import AutoscaleEnv, ACTION_NAMES
from rl_agent.config import Config, AgentConfig, EnvironmentConfig
from firebase_bridge.sync import FirebaseSync

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("demo")

# Output file for dashboard consumption
DEMO_DATA_DIR = Path(__file__).parent / "dashboard" / "public"
DEMO_DATA_FILE = DEMO_DATA_DIR / "demo-data.json"


class DemoState:
    """Shared state between RL agent and the API server."""

    def __init__(self):
        self.data = {
            "agent_status": "initializing",
            "current_episode": 0,
            "total_episodes": 0,
            "metrics": {
                "cpu_utilization": 0.0,
                "memory_utilization": 0.0,
                "request_rate": 0.0,
                "replicas": 3,
            },
            "action_probs": [0.33, 0.34, 0.33],
            "decisions": [],
            "training_stats": {
                "best_reward": 0.0,
                "current_reward": 0.0,
                "policy_loss": 0.0,
                "value_loss": 0.0,
            },
        }
        self.lock = threading.Lock()

    def update(self, **kwargs):
        with self.lock:
            for key, value in kwargs.items():
                if key in self.data:
                    self.data[key] = value
            self._save()

    def add_decision(self, decision: dict):
        with self.lock:
            self.data["decisions"].insert(0, decision)
            self.data["decisions"] = self.data["decisions"][:50]
            self._save()

    def _save(self):
        DEMO_DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(DEMO_DATA_FILE, "w") as f:
            json.dump(self.data, f, indent=2)

    def to_json(self):
        with self.lock:
            return json.dumps(self.data)


demo_state = DemoState()


class CORSRequestHandler(SimpleHTTPRequestHandler):
    """HTTP handler with CORS headers for the dashboard API."""

    def do_GET(self):
        if self.path == "/api/state":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(demo_state.to_json().encode())
        else:
            super().do_GET()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def log_message(self, fmt, *args):
        pass  # Suppress HTTP logs


def start_api_server(port=8888):
    """Start a simple API server for the dashboard to poll."""
    server = HTTPServer(("0.0.0.0", port), CORSRequestHandler)
    logger.info("Demo API server running at http://localhost:%d/api/state", port)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def run_demo(episodes: int = 20, max_steps: int = 200):
    """Run the full RL agent demo with live state updates."""
    config = Config(simulate=True)
    agent = PPOAgent(config.agent)
    env = AutoscaleEnv(config=config.env, max_steps=max_steps)

    # Initialize Firebase sync (offline mode — logs locally)
    firebase_sync = FirebaseSync()

    best_reward = -float("inf")

    demo_state.update(
        agent_status="training",
        total_episodes=episodes,
    )

    print("\n" + "=" * 70)
    print("  🧠 RL AUTOSCALER — LIVE DEMO")
    print("  " + "=" * 66)
    print(f"  Episodes: {episodes} | Max Steps: {max_steps}")
    print(f"  Dashboard: http://localhost:3000")
    print(f"  API:       http://localhost:8888/api/state")
    print("=" * 70 + "\n")

    for ep in range(1, episodes + 1):
        state, info = env.reset(seed=ep)
        episode_reward = 0.0

        demo_state.update(current_episode=ep)

        for step in range(max_steps):
            # Get action and probabilities
            action, log_prob, value = agent.select_action(state)
            action_probs = agent.get_action_probs(state).tolist()

            # Step environment
            next_state, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated

            # Store in buffer
            agent.buffer.add(state, action, reward, log_prob, value, done)
            episode_reward += reward

            # Create decision record
            decision = {
                "id": f"ep{ep}-step{step}",
                "action": ACTION_NAMES[action],
                "previous_replicas": info["replicas"] + (1 if action == 0 else -1 if action == 2 else 0),
                "new_replicas": info["replicas"],
                "confidence_score": float(max(action_probs)),
                "cpu_utilization": info["metrics"]["cpu_utilization"],
                "memory_utilization": info["metrics"]["memory_utilization"],
                "request_rate": info["metrics"]["request_rate"],
                "timestamp": time.time(),
                "episode": ep,
                "step": step,
            }

            # Update demo state for dashboard
            demo_state.update(
                metrics={
                    "cpu_utilization": info["metrics"]["cpu_utilization"],
                    "memory_utilization": info["metrics"]["memory_utilization"],
                    "request_rate": info["metrics"]["request_rate"],
                    "replicas": info["replicas"],
                },
                action_probs=action_probs,
            )
            demo_state.add_decision(decision)

            # Push to Firebase (offline mode logs it)
            firebase_sync.push_decision(decision)

            state = next_state

            if done:
                break

            # Small delay for visualization
            time.sleep(0.05)

        # PPO update
        losses = agent.update()

        if episode_reward > best_reward:
            best_reward = episode_reward
            os.makedirs(config.checkpoint_dir, exist_ok=True)
            agent.save(os.path.join(config.checkpoint_dir, "best_model.pt"))

        demo_state.update(
            training_stats={
                "best_reward": round(best_reward, 2),
                "current_reward": round(episode_reward, 2),
                "policy_loss": round(losses.get("policy_loss", 0), 4),
                "value_loss": round(losses.get("value_loss", 0), 4),
            }
        )

        # Print episode summary
        bar_len = int(min(episode_reward / 2, 30))
        bar = "█" * max(bar_len, 1) + "░" * (30 - max(bar_len, 1))
        print(
            f"  Episode {ep:3d}/{episodes} │ "
            f"Reward: {episode_reward:7.2f} │ "
            f"Best: {best_reward:7.2f} │ "
            f"{bar} │ "
            f"PL: {losses.get('policy_loss', 0):.4f}"
        )

        firebase_sync.update_health("training", {"episode": ep, "reward": episode_reward})

    demo_state.update(agent_status="trained")
    firebase_sync.update_health("trained")

    print("\n" + "=" * 70)
    print(f"  ✅ Training Complete! Best Reward: {best_reward:.2f}")
    print("=" * 70)

    return agent


if __name__ == "__main__":
    # Start API server
    start_api_server(port=8888)

    # Run the demo
    agent = run_demo(episodes=20, max_steps=200)

    # Keep running for dashboard access
    print("\n  Agent trained. Dashboard still accessible at http://localhost:3000")
    print("  API data at http://localhost:8888/api/state")
    print("  Press Ctrl+C to exit.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nDemo stopped.")
