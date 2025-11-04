# Outputs for SageMaker Model Registry

output "model_package_group_arn" {
  description = "ARN of the main model package group"
  value       = aws_sagemaker_model_package_group.main.arn
}

output "gold_tier_package_group_arn" {
  description = "ARN of the Gold tier model package group"
  value       = aws_sagemaker_model_package_group.gold_tier.arn
}

output "silver_tier_package_group_arn" {
  description = "ARN of the Silver tier model package group"
  value       = aws_sagemaker_model_package_group.silver_tier.arn
}

output "bronze_tier_package_group_arn" {
  description = "ARN of the Bronze tier model package group"
  value       = aws_sagemaker_model_package_group.bronze_tier.arn
}

output "model_packages_bucket" {
  description = "S3 bucket for model package artifacts"
  value       = aws_s3_bucket.model_packages.bucket
}

output "registry_role_arn" {
  description = "ARN of the IAM role for model registry operations"
  value       = aws_iam_role.model_registry_role.arn
}

