# ============================================================================
# AWS IAM — Least-Privilege EC2 → S3
# ============================================================================

resource "aws_iam_role" "ec2_role" {
  name = "rl-autoscaler-ec2-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
      Action = "sts:AssumeRole"
    }]
  })
}

# Only allow access to the specific training data bucket
resource "aws_iam_policy" "s3_training_data" {
  name = "rl-autoscaler-s3-policy-${var.environment}"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:ListBucket",
        ]
        Resource = [
          aws_s3_bucket.training_data.arn,
          "${aws_s3_bucket.training_data.arn}/*",
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "s3_attach" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = aws_iam_policy.s3_training_data.arn
}

resource "aws_iam_instance_profile" "ec2_profile" {
  name = "rl-autoscaler-ec2-profile-${var.environment}"
  role = aws_iam_role.ec2_role.name
}
