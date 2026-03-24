"""
Configuration & Hyperparameters for the RL Autoscaler.
"""
import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class AgentConfig:
    """PPO Agent hyperparameters."""
    learning_rate: float = 3e-4
    gamma: float = 0.99
    gae_lambda: float = 0.95
    clip_epsilon: float = 0.2
    entropy_coeff: float = 0.01
    value_loss_coeff: float = 0.5
    max_grad_norm: float = 0.5
    update_epochs: int = 4
    batch_size: int = 64
    hidden_dim: int = 128
    state_dim: int = 7  # cpu, mem, rps, replicas, hour_sin, hour_cos, day_of_week
    action_dim: int = 3  # scale_down, maintain, scale_up


@dataclass
class EnvironmentConfig:
    """Autoscaling environment settings."""
    min_replicas: int = 1
    max_replicas: int = 20
    target_cpu: float = 0.65
    target_memory: float = 0.70
    scale_cooldown_seconds: int = 60
    observation_interval: int = 15  # seconds


@dataclass
class InfraConfig:
    """Infrastructure endpoints."""
    prometheus_url: str = os.getenv("PROMETHEUS_URL", "http://localhost:9090")
    k3s_api_url: str = os.getenv("K3S_API_URL", "https://localhost:6443")
    k3s_token: str = os.getenv("K3S_TOKEN", "")
    target_deployment: str = os.getenv("TARGET_DEPLOYMENT", "web-app")
    target_namespace: str = os.getenv("TARGET_NAMESPACE", "default")
    kubeconfig_path: str = os.getenv("KUBECONFIG", "")


@dataclass
class FirebaseConfig:
    """Firebase integration settings."""
    service_account_path: str = os.getenv(
        "FIREBASE_SA_PATH", "firebase-service-account.json"
    )
    database_url: str = os.getenv("FIREBASE_DB_URL", "")
    project_id: str = os.getenv("FIREBASE_PROJECT_ID", "")


@dataclass
class Config:
    """Master configuration."""
    agent: AgentConfig = field(default_factory=AgentConfig)
    env: EnvironmentConfig = field(default_factory=EnvironmentConfig)
    infra: InfraConfig = field(default_factory=InfraConfig)
    firebase: FirebaseConfig = field(default_factory=FirebaseConfig)
    simulate: bool = True
    checkpoint_dir: str = "checkpoints"
    log_dir: str = "logs"
