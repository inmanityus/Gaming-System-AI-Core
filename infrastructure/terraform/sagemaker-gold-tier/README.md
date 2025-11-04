# SageMaker Gold Tier Training Infrastructure

Terraform module for deploying SageMaker training infrastructure for Gold tier models (3B-8B).

## Features

- **Instance Type**: g6.12xlarge (L4) or g5.12xlarge (A10G)
- **Managed Spot Training**: 100% (maximum cost savings)
- **Checkpointing**: Every 30 minutes to S3
- **Automatic Resume**: Training jobs can resume from checkpoints on Spot interruption

## Usage

```hcl
module "sagemaker_gold_tier" {
  source = "./infrastructure/terraform/sagemaker-gold-tier"
  
  aws_region          = "us-east-1"
  environment         = "prod"
  project_name        = "gaming-ai-core"
  instance_type       = "ml.g6.12xlarge"
  training_image      = "your-ecr-repo/training:latest"
  training_data_s3_uri = "s3://your-bucket/training-data/"
  
  hyperparameters = {
    learning_rate = "1e-5"
    batch_size    = "32"
    epochs        = "5"
  }
}
```

## Resources Created

- S3 buckets for training data, checkpoints, and output
- IAM role and policies for SageMaker
- CloudWatch log group
- Training job configuration template

## Outputs

- `training_role_arn`: IAM role ARN for training jobs
- `checkpoint_s3_uri`: S3 URI for checkpoints
- `training_output_s3_uri`: S3 URI for training output
- `training_job_config_file`: Path to configuration file for Python scripts

## Notes

- Training jobs are created via Python scripts using the configuration file
- Checkpointing is configured for 30-minute intervals
- Spot instances provide up to 90% cost savings
- All resources are tagged for cost tracking

