# ============================================================================
# Intelligent Predictive Autoscaler — Terraform Root Module
# Multi-cloud IaC: AWS + GCP + Firebase
# ============================================================================

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 5.0"
    }
  }

  backend "local" {
    path = "terraform.tfstate"
  }
}

# ─── Providers ───────────────────────────────────────────────────────────────

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "rl-autoscaler"
      ManagedBy   = "terraform"
      Environment = var.environment
    }
  }
}

provider "google" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

provider "google-beta" {
  project = var.gcp_project_id
  region  = var.gcp_region
}

# ─── Modules ────────────────────────────────────────────────────────────────

module "aws" {
  source = "./aws"

  environment        = var.environment
  aws_region         = var.aws_region
  ec2_instance_type  = var.ec2_instance_type
  ec2_key_name       = var.ec2_key_name
  s3_bucket_name     = var.s3_bucket_name
}

module "gcp" {
  source = "./gcp"

  environment    = var.environment
  gcp_project_id = var.gcp_project_id
  gcp_region     = var.gcp_region
  gcs_bucket_name = var.gcs_bucket_name
}

module "firebase" {
  source = "./firebase"

  gcp_project_id = var.gcp_project_id
}
