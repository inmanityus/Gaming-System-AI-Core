# EKS Kubernetes Upgrade Status

## AWS Notification Summary

**Date Received**: Current  
**Action Required**: Upgrade EKS cluster from Kubernetes 1.29 to 1.32+  
**Deadline**: March 23, 2026 (extended support ends)  
**Affected Resource**: `arn:aws:eks:us-east-1:695353648052:cluster/gaming-ai-gold-tier`

## Current Status

✅ **Configuration Updated**: Terraform variables updated to use Kubernetes 1.32  
✅ **Upgrade Script Created**: `scripts/aws-upgrade-eks-k8s.ps1`  
✅ **Documentation Created**: `infrastructure/terraform/eks-gold-tier/UPGRADE-K8S-1.32.md`  

⏳ **Upgrade Pending**: Manual upgrade required before March 23, 2026

## Upgrade Approach

### Option 1: Terraform (Recommended)

The Terraform configuration has been updated to use Kubernetes 1.32. To upgrade:

```bash
cd infrastructure/terraform/eks-gold-tier
terraform init
terraform plan
terraform apply
```

### Option 2: PowerShell Script

Use the automated upgrade script:

```powershell
# Dry run first
.\scripts\aws-upgrade-eks-k8s.ps1 -DryRun

# Actual upgrade
.\scripts\aws-upgrade-eks-k8s.ps1
```

### Option 3: AWS CLI Direct

```bash
aws eks update-cluster-version \
  --name gaming-ai-gold-tier \
  --version 1.32 \
  --region us-east-1
```

## Timeline

- **Pre-upgrade checks**: 30 minutes
- **Control plane upgrade**: 30-60 minutes
- **Node group upgrade**: 30-60 minutes (rolling)
- **Verification**: 30 minutes
- **Total**: 2-3 hours

## Next Steps

1. **Review the upgrade guide**: `infrastructure/terraform/eks-gold-tier/UPGRADE-K8S-1.32.md`
2. **Schedule maintenance window**: Plan for 2-3 hours of downtime for control plane
3. **Run pre-upgrade checks**: Verify all workloads are healthy
4. **Execute upgrade**: Use Terraform or PowerShell script
5. **Verify**: Confirm cluster and workloads are functioning correctly

## Notes

- **No downtime for running workloads**: Pods will continue running during upgrade
- **Control plane unavailable**: New deployments may be delayed during upgrade
- **Node groups**: Will automatically upgrade to match control plane version
- **Addons**: Will be updated automatically if compatible

## References

- Upgrade Guide: `infrastructure/terraform/eks-gold-tier/UPGRADE-K8S-1.32.md`
- Upgrade Script: `scripts/aws-upgrade-eks-k8s.ps1`
- AWS Documentation: https://docs.aws.amazon.com/eks/latest/userguide/update-cluster.html


