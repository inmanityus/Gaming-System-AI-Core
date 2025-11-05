# SRL→RLVR Training System - Recovery Playbooks
**Date**: 2025-11-04  
**Status**: Production-Ready

---

## Overview

Step-by-step recovery procedures for common failure scenarios in the SRL→RLVR training system.

---

## Failure Scenario 1: Spot Instance Interruption

### Symptoms
- Training job status: "Interrupted"
- CloudWatch alarm: "TrainingJobInterrupted"
- Partial checkpoint available

### Recovery Steps

1. **Identify Checkpoint**
```python
from services.srl_rlvr_training.recovery import CheckpointManager

checkpoint_manager = CheckpointManager()
checkpoint = await checkpoint_manager.get_latest_checkpoint(
    training_job_name="srl-rlvr-gold-20251104",
    tier="gold"
)
```

2. **Validate Checkpoint**
```python
validation = await checkpoint_manager.validate_checkpoint(
    checkpoint["s3_uri"]
)

if not validation["valid"]:
    # Handle invalid checkpoint
    pass
```

3. **Resume Training**
```python
from services.srl_rlvr_training.recovery import FailureHandler

handler = FailureHandler()
recovery = await handler.handle_training_failure(
    training_job_name="srl-rlvr-gold-20251104",
    failure_reason="Spot interruption",
    tier="gold",
    checkpoint_s3_uri=checkpoint["s3_uri"]
)

# Launch new training job with checkpoint
if recovery["recovery_result"]["strategy"] == "resume_from_checkpoint":
    # Use checkpoint in new training job
    pass
```

---

## Failure Scenario 2: Out of Memory (OOM)

### Symptoms
- Training job fails with OOM error
- CloudWatch metric: "TrainingJobMemoryUsage" > threshold
- No checkpoint available

### Recovery Steps

1. **Identify Failure**
```python
handler = FailureHandler()
recovery = await handler.handle_training_failure(
    training_job_name="srl-rlvr-silver-20251104",
    failure_reason="Out of memory",
    tier="silver"
)
```

2. **Reduce Batch Size**
```python
if recovery["recovery_result"]["strategy"] == "retry_with_reduced_batch":
    reduction = recovery["recovery_result"]["batch_size_reduction"]
    # Launch new job with reduced batch size
    new_batch_size = int(original_batch_size * reduction)
```

3. **Retry Training**
```python
# Launch new training job with reduced batch size
python scripts/sagemaker/train-silver-tier.py --batch-size $new_batch_size
```

---

## Failure Scenario 3: Data Validation Failure

### Symptoms
- Training job fails during data loading
- Error: "Invalid data format" or "Data validation failed"
- No checkpoint available

### Recovery Steps

1. **Validate Training Data**
```python
# Run data validation
python scripts/sagemaker/validate-training-data.py \
    --s3-uri s3://bucket/training-data/ \
    --tier gold
```

2. **Fix Data Issues**
```python
# Fix identified issues
python scripts/sagemaker/fix-training-data.py \
    --s3-uri s3://bucket/training-data/ \
    --fix-issues
```

3. **Retry Training**
```python
handler = FailureHandler()
recovery = await handler.handle_training_failure(
    training_job_name="srl-rlvr-gold-20251104",
    failure_reason="Data validation failed",
    tier="gold"
)

# Launch new job after data fix
if recovery["recovery_result"]["strategy"] == "retry_after_data_fix":
    # Launch new training job
    pass
```

---

## Failure Scenario 4: Model Performance Degradation

### Symptoms
- CloudWatch alarm: "ModelPerformance" < threshold
- Model drift detected
- User feedback indicates quality issues

### Recovery Steps

1. **Rollback to Previous Version**
```python
from services.srl_rlvr_training.recovery import FailureHandler

handler = FailureHandler()
fallback_model = await handler.get_fallback_model(
    tier="gold",
    use_case="srl_gold_tier"
)

if fallback_model:
    # Deploy fallback model
    await model_registry.promote_model_version(
        model_id=fallback_model["model_id"],
        status="production"
    )
```

2. **Investigate Root Cause**
```python
# Check training metrics
# Review training logs
# Analyze performance data
```

3. **Retrain with Fixes**
```python
# After identifying root cause, retrain with fixes
python scripts/sagemaker/train-gold-tier.py --fix-issues
```

---

## Failure Scenario 5: Complete System Failure

### Symptoms
- Multiple training jobs failed
- No valid checkpoints available
- System unable to recover automatically

### Recovery Steps

1. **Assess Situation**
```python
# Check all training jobs status
# Review CloudWatch alarms
# Check S3 bucket contents
```

2. **Manual Intervention**
```python
# Restore from backup
# Use previous model version
# Restart training from scratch if needed
```

3. **Document and Prevent**
```python
# Document failure cause
# Update recovery procedures
# Implement preventive measures
```

---

## Best Practices

1. **Always Enable Checkpointing**: Set checkpoint frequency to 30 minutes
2. **Monitor Continuously**: Use CloudWatch alarms for early detection
3. **Test Recovery Procedures**: Regularly test recovery scenarios
4. **Document Failures**: Keep detailed logs of all failures and recoveries
5. **Automate Where Possible**: Use Step Functions for automated recovery

---

## Emergency Contacts

- **AWS Support**: Use AWS Support for infrastructure issues
- **SageMaker Team**: Contact for training-specific issues
- **Internal Team**: For system-specific issues

---

## Recovery Time Objectives (RTO)

- **Gold Tier**: 1 hour (resume from checkpoint)
- **Silver Tier**: 2 hours (resume or retry)
- **Bronze Tier**: 4 hours (may require full retrain)

---

## Recovery Point Objectives (RPO)

- **Checkpoint Frequency**: 30 minutes
- **Data Loss Tolerance**: 30 minutes maximum
- **Model Version Loss**: 0 (all versions tracked in registry)


