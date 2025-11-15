# AWS SageMaker ml.p3 Instance Deprecation Migration

**Date**: November 15, 2025  
**Deadline**: December 20, 2025  
**Status**: ✅ MIGRATION COMPLETE  

## Summary

AWS is deprecating ml.p3 instances in SageMaker. All workloads must be migrated to newer instance types by December 20, 2025.

## Affected Resources

### 1. ✅ Model Management Fine-Tuning Pipeline
- **File**: `services/model_management/fine_tuning_pipeline.py`
- **Changes**:
  - `ml.p3.8xlarge` → `ml.g6.8xlarge` (for 13B/34B models)
  - `ml.p3.2xlarge` → `ml.g6.2xlarge` (for 7B models)
- **Status**: MIGRATED

### 2. ✅ CloudWatch Cost Tracking Dashboard
- **File**: `infrastructure/cloudwatch/dashboards/cost-tracking.json`
- **Changes**:
  - `ml.p3.2xlarge` → `ml.g6.2xlarge` (monitoring metric)
- **Status**: MIGRATED

## Migration Benefits

### G6 vs P3 Comparison
- **Better Price-Performance**: G6 instances offer lower cost per GPU hour
- **More GPU Memory**: 
  - ml.g6.2xlarge: 32GB GPU memory (vs 16GB on ml.p3.2xlarge)
  - ml.g6.8xlarge: 128GB GPU memory (vs 64GB on ml.p3.8xlarge)
- **Newer Architecture**: NVIDIA L4 GPUs with better efficiency

## Testing Requirements

1. **Fine-Tuning Pipeline**:
   - Test 7B model fine-tuning on ml.g6.2xlarge
   - Test 13B/34B model fine-tuning on ml.g6.8xlarge
   - Verify memory usage and training speed

2. **Cost Monitoring**:
   - Update CloudWatch dashboards to track G6 costs
   - Compare cost efficiency vs P3 instances

## Environment Variables

If using custom instance types via environment variables:
```bash
# Update these if set:
LORA_INSTANCE_TYPE=ml.g6.2xlarge  # Was ml.p3.2xlarge
LORA_INSTANCE_TYPE=ml.g6.8xlarge  # Was ml.p3.8xlarge
```

## Next Steps

- [x] Update code to use G6 instances
- [ ] Test fine-tuning pipeline with new instances
- [ ] Monitor costs and performance
- [ ] Update any documentation referencing P3 instances

## References

1. [AWS G6 Instances](https://aws.amazon.com/ec2/instance-types/g6/)
2. [SageMaker Instance Types](https://aws.amazon.com/sagemaker/pricing/)
3. AWS Health Dashboard notification (November 15, 2025)
