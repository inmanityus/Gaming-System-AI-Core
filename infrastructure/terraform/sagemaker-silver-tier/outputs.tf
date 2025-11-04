# Outputs for SageMaker Silver Tier Training Infrastructure

output "training_role_arn" {
  description = "ARN of the IAM role for SageMaker training"
  value       = aws_iam_role.sagemaker_training_role.arn
}

output "checkpoint_s3_uri" {
  description = "S3 URI for training checkpoints"
  value       = "s3://${aws_s3_bucket.checkpoints.bucket}/checkpoints/"
}

output "training_output_s3_uri" {
  description = "S3 URI for training output"
  value       = "s3://${aws_s3_bucket.training_output.bucket}/output/"
}

output "training_data_bucket" {
  description = "S3 bucket for training data"
  value       = aws_s3_bucket.training_data.bucket
}

output "checkpoint_bucket" {
  description = "S3 bucket for checkpoints"
  value       = aws_s3_bucket.checkpoints.bucket
}

output "training_output_bucket" {
  description = "S3 bucket for training output"
  value       = aws_s3_bucket.training_output.bucket
}

output "cloudwatch_log_group" {
  description = "CloudWatch log group for training logs"
  value       = aws_cloudwatch_log_group.training_logs.name
}

output "training_job_config_file" {
  description = "Path to training job configuration file"
  value       = local_file.training_job_config.filename
}

