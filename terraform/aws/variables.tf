# ============================================================================
# AWS Module Variables & Outputs
# ============================================================================

variable "environment" { type = string }
variable "aws_region" { type = string }
variable "ec2_instance_type" { type = string }
variable "ec2_key_name" { type = string }
variable "s3_bucket_name" { type = string }

output "ec2_public_ip" {
  value = aws_instance.k3s_server.public_ip
}

output "s3_bucket_arn" {
  value = aws_s3_bucket.training_data.arn
}
