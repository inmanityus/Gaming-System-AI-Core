# SRL→RLVR Training System - Deployment Guide
**Date**: 2025-11-04  
**Status**: Production-Ready

---

## Overview

Complete deployment guide for the SRL→RLVR Training System on AWS SageMaker.

---

## Prerequisites

- AWS Account with SageMaker access
- Terraform installed (>= 1.0)
- AWS CLI configured
- Python 3.9+ with dependencies installed
- boto3 and sagemaker SDKs

---

## Deployment Steps

### Step 1: Deploy Infrastructure

```powershell
# Deploy Gold Tier
cd infrastructure/terraform/sagemaker-gold-tier
terraform init
terraform plan
terraform apply

# Deploy Silver Tier
cd ../sagemaker-silver-tier
terraform init
terraform plan
terraform apply

# Deploy Bronze Tier
cd ../sagemaker-bronze-tier
terraform init
terraform plan
terraform apply

# Deploy Model Registry
cd ../sagemaker-registry
terraform init
terraform plan
terraform apply
```

### Step 2: Deploy Training Scripts

```powershell
# Upload training code to S3
python scripts/sagemaker/upload-training-code.py

# Deploy training orchestrator
python scripts/sagemaker/training-orchestrator.py --deploy
```

### Step 3: Launch Training Jobs

```powershell
# Launch Gold Tier training
python scripts/sagemaker/train-gold-tier.py

# Launch Silver Tier training
python scripts/sagemaker/train-silver-tier.py

# Launch Bronze Tier training
python scripts/sagemaker/train-bronze-tier.py
```

### Step 4: Deploy Monitoring

```powershell
# Deploy CloudWatch dashboards
aws cloudwatch put-dashboard --dashboard-name "SRL-RLVR-Training" --dashboard-body file://infrastructure/cloudwatch/dashboards/training-metrics.json

# Deploy CloudWatch alarms
cd infrastructure/cloudwatch/alarms
terraform init
terraform plan
terraform apply
```

---

## Verification

### Check Training Jobs

```powershell
aws sagemaker list-training-jobs --status-equals InProgress
```

### Check CloudWatch Metrics

```powershell
aws cloudwatch get-metric-statistics --namespace "Custom/SRL-RLVR" --metric-name "ModelPerformance"
```

### Verify Model Registry

```powershell
aws sagemaker list-model-packages --model-package-group-name "srl-rlvr-models"
```

---

## Troubleshooting

### Common Issues

1. **Training Job Fails**: Check CloudWatch logs for error details
2. **Checkpoint Not Found**: Verify S3 bucket permissions
3. **Cost Exceeds Budget**: Review CloudWatch alarms and adjust thresholds
4. **Model Not Loading**: Verify model artifacts in S3

---

## Recovery Procedures

### Resume from Checkpoint

```python
from services.srl_rlvr_training.recovery import FailureHandler, CheckpointManager

handler = FailureHandler()
checkpoint_manager = CheckpointManager()

# Get latest checkpoint
checkpoint = await checkpoint_manager.get_latest_checkpoint(
    training_job_name="srl-rlvr-gold-20251104",
    tier="gold"
)

# Resume training with checkpoint
await handler.handle_training_failure(
    training_job_name="srl-rlvr-gold-20251104",
    failure_reason="Spot interruption",
    tier="gold",
    checkpoint_s3_uri=checkpoint["s3_uri"]
)
```

---

## Cost Optimization

- Use Managed Spot Training for Gold and Silver tiers
- Monitor costs via CloudWatch dashboards
- Set up budget alarms
- Use distillation pipeline to reduce Bronze tier dependency

---

## Security

- All S3 buckets use encryption at rest
- IAM roles follow least privilege principle
- Model registry tracks all model versions
- Audit logging enabled for all operations

---

## Support

For issues or questions:
- Check CloudWatch logs
- Review troubleshooting guide
- Check deployment documentation
- Review recovery playbooks


