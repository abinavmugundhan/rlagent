# ============================================================================
# Terraform Outputs
# ============================================================================

output "ec2_public_ip" {
  description = "Public IP of the k3s EC2 instance"
  value       = module.aws.ec2_public_ip
}

output "s3_bucket_arn" {
  description = "ARN of the S3 training data bucket"
  value       = module.aws.s3_bucket_arn
}

output "gcs_bucket_url" {
  description = "URL of the GCS training data bucket"
  value       = module.gcp.gcs_bucket_url
}

output "vertex_ai_endpoint" {
  description = "Vertex AI endpoint (if deployed)"
  value       = module.gcp.vertex_ai_endpoint
}

output "cloud_function_url" {
  description = "URL of the retraining Cloud Function"
  value       = module.gcp.cloud_function_url
}
