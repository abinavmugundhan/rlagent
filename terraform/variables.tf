# ============================================================================
# Terraform Variables
# ============================================================================

# ─── General ─────────────────────────────────────────────────────────────────

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

# ─── AWS ─────────────────────────────────────────────────────────────────────

variable "aws_region" {
  description = "AWS region for infrastructure"
  type        = string
  default     = "us-east-1"
}

variable "ec2_instance_type" {
  description = "EC2 instance type for k3s node"
  type        = string
  default     = "t2.micro"
}

variable "ec2_key_name" {
  description = "SSH key pair name for EC2"
  type        = string
  default     = "rl-autoscaler-key"
}

variable "s3_bucket_name" {
  description = "S3 bucket for training data"
  type        = string
  default     = "rl-autoscaler-training-data"
}

# ─── GCP ─────────────────────────────────────────────────────────────────────

variable "gcp_project_id" {
  description = "GCP project ID"
  type        = string
}

variable "gcp_region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

variable "gcs_bucket_name" {
  description = "GCS bucket for training data (from S3 transfer)"
  type        = string
  default     = "rl-autoscaler-training-gcs"
}
