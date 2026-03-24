# Intelligent Predictive Autoscaler
## Mini Project Report & Deliverables

This document is structured to fulfill the evaluation criteria for the Mini Project, breaking down the deliverables across the four review phases.

---

## Review-1: Product Ideation & Architecture Design (1B)
**Date:** 30-01-2026

### 1. Problem Definition & PRD
**Problem Relevance & Clarity:**
Modern cloud-native applications face unpredictable and dynamic workloads. Traditional autoscaling mechanisms (like Kubernetes HPA) rely on static, rule-based thresholds (e.g., CPU > 80%). These reactive systems suffer from lag, resulting in under-provisioning during sudden traffic spikes (causing SLA violations) and over-provisioning during sudden traffic drops (wasting structural costs).

**Product Requirements Document (PRD):**
*   **Objective:** Develop an Intelligent Predictive Autoscaler that uses Reinforcement Learning (RL) to proactively scale Kubernetes deployments based on historical and real-time metric streams.
*   **Key Features:**
    *   **Proactive Scaling:** Predicts load and scales infrastructure *before* the spike hits.
    *   **Real-time Visualization:** A live React dashboard fed by Firebase Realtime Database.
    *   **Off-Cluster Training:** Cost-efficient heavy model (PPO) retraining using Google Vertex AI, while lightweight inference runs in-cluster.
    *   **Multi-Cloud Setup:** Core Kubernetes (K3s) on AWS EC2, Machine Learning on GCP, and state sync on Firebase.

### 2. Agile Backlog & Planning
**Epics:**
1.  **Environment & Infrastructure Setup:** Provision AWS EC2 instances, K3s clusters, GCP projects, Firebase configurations, and configure Terraform for generic multi-cloud deployments.
2.  **Reinforcement Learning Model Integration:** Develop a custom OpenAI Gymnasium environment reflecting cluster dynamics and integrate a stable Proximal Policy Optimization (PPO) agent.
3.  **Real-Time Data Pipelines:** Integrate Prometheus for ingestion and a syncing bridge to push rapid state updates to Firebase.
4.  **UI/UX Dashboard:** Build an interactive React + Vite frontend for continuous monitoring of agent confidence and scaling probabilities.

### 3. Cloud-Native Architecture Design
The architecture is inherently cloud-native, distributing responsibilities across optimized providers:
*   **AWS:** Hosts the primary compute layer (K3s cluster on EC2) and Prometheus for scraping real-time raw utilization metrics.
*   **Agent Module:** Python-based PPO Actor-Critic architecture wrapped in an isolated environment that pushes scaling instructions via `kubectl`.
*   **Google Cloud / Vertex AI:** Cloud Functions trigger distributed model retraining pipeline inside Vertex AI periodically.
*   **Firebase / Frontend:** Firebase Realtime DB operates as the real-time bridge feeding the React dashboard.

### 4. Security & Reliability Design
*   **IAM Roles & RBAC:** strict Least Privilege access applied for Vertex AI triggering and AWS EC2 provisioning.
*   **Scalability:** Uses asynchronous data processing strategies (Firebase Sync is non-blocking) ensuring the scaling operations aren't bottlenecked by the UI updates.

---

## Review-2: Implementation & Engineering Deliverables (2B)
**Date:** 20-02-2026

### 1. Application & Pipeline Implementation
*   **Agent Engineering:** The core autoscaler is implemented via a Gym Environment (`AutoscaleEnv`) tracking a normalized state vector: CPU, Memory, Request Rate, current replica count, and cyclical time features (hour sine/cosine, day of week).
*   **Actions:** Discrete Action Space (Scale Down, Maintain, Scale Up).
*   **Reward Function:** Heavily penalizes SLA risk (under-provisioning CPU > target) exponentially, mildly penalizes waste (over-provisioning), and assigns a small penalty for constant action thrashing.

### 2. Data Ingestion & Processing
The Prometheus bridge pulls live metrics, aggregates them into a `MetricsSnapshot`, and mathematically transforms them into [0.0 - 1.0] normalized bounded state values required for neural network processing.

### 3. ML / AI Model Integration
The underlying intelligence is powered by PPO (Proximal Policy Optimization) using PyTorch. State dimensions (7 inputs) map to continuous hidden layers before splitting into Actor (Softmax Action probabilities) and Critic (Value estimation) heads. Checkpointing ensures the best models are saved dynamically.

### 4. CI/CD, Containers, & Orchestration
*   **Manifests & Terraform:** Full infrastructure-as-code deployment definitions using multi-provider Terraform.
*   **Kubernetes Orchestration:** Deployed targets are continuously monitored; scaling is orchestrating directly via the Kubernetes REST API/Kubeconfig authentication strategy.

### 5. Secure Coding Practices
Implemented robust environment parameter management (e.g., via `.env`), isolating secrets like the Kubernetes API token, AWS keys, and Firebase JSON payloads from the core codebase.

---

## Review-3: Testing, Optimization & Deployment Deliverables (3B)
**Date:** 16-03-2026

### 1. Testing & Validation
Comprehensive `pytest` suite tests state bounds, ensuring mathematical stability of the observation matrices before being passed to the RL engine. The custom Gymnasium environment runs locally under simulated stress testing to validate reward consistency.

### 2. Performance & Cost Optimization
The system inherently reduces AWS EC2 usage by aggressive yet safe downscaling during off-peak hours based on the learned Time-of-Day inputs. Local inference requires minimal overhead (<1vCPU), pushing heavy GPU-intensive computation exclusively to preemptible Vertex instances.

### 3. Monitoring Dashboards
A complete React/Vite Dashboard interfaces via Firebase, visualizing:
1.  **Agent Brain Visualizer:** Rendering PPO Probability Vectors in real time (e.g., Scale Down 20%, Maintain 60%, Scale Up 20%).
2.  **Reward & Loss Tracks:** Monitoring policy stability and value confidence.
3.  **Resource Heatmap & Replicas:** Overlaying traffic spikes on top of autonomous scaler operations.

### 4. Deployment Evidence
Codebase committed to GitHub, complete with CI/CD workflows under `.github/workflows/deploy.yml`. Terraform state files successfully provision simulated cross-cloud environments. The real-time synthetic test bed (`run_demo.py`) successfully handles over 200 high-frequency steps without drift.

### 5. Risk, Threat Analysis & Mitigation
*   **Model Drift:** Mitigated by the asynchronous Vertex AI pipeline re-aggregating S3/GCS state data nightly.
*   **Thrashing:** Addressed via the `scale_cooldown_seconds` setting and negative reward penalties for jumping between scaling up and down erratically.
*   **Availability:** Firebase offline cache mode acts as a safety stop if the network partition disconnects the metrics bridge.

---

## Final Review (4B)
**Date:** 17-04-2026

*The complete Technical Project Report synthesizes the above reviews along with the Live Demo infrastructure (handled by `run_demo.py` + Vite React frontend) providing a seamless, real-time explanation layer for viva voce defense.*
