# EKS Kubernetes Upgrade - Quick Reference

## Quick Commands

### Check Current Versions
```powershell
.\scripts\aws-check-eks-version.ps1
```

### Dry Run Upgrade
```powershell
.\scripts\aws-upgrade-eks-k8s.ps1 -DryRun
```

### Execute Upgrade
```powershell
.\scripts\aws-upgrade-eks-k8s.ps1
```

### Using Terraform
```bash
cd infrastructure/terraform/eks-gold-tier
terraform init
terraform plan
terraform apply
```

## Upgrade Timeline

| Phase | Duration | Impact |
|-------|----------|--------|
| Pre-upgrade checks | 30 min | None |
| Control plane upgrade | 30-60 min | Control plane unavailable |
| Node group upgrade | 30-60 min | Rolling update (no downtime) |
| Verification | 30 min | None |
| **Total** | **2-3 hours** | Minimal workload impact |

## Version Compatibility

| Version | Status | Action Required |
|---------|--------|-----------------|
| 1.29 | ⚠️ Deprecated | **Upgrade before March 23, 2026** |
| 1.30-1.31 | ⚠️ Supported | Consider upgrade to 1.32+ |
| 1.32-1.33 | ✅ Recommended | No action needed |

## Files Updated

- ✅ `infrastructure/terraform/eks-gold-tier/variables.tf` → 1.32
- ✅ `infrastructure/terraform/eks-silver-tier/variables.tf` → 1.32
- ✅ `infrastructure/aws-cli/create-eks-gold-tier.ps1` → 1.32

## Documentation

- **Full Guide**: `infrastructure/terraform/eks-gold-tier/UPGRADE-K8S-1.32.md`
- **Status**: `docs/EKS-K8S-UPGRADE-STATUS.md`
- **Quick Ref**: This file

## Support

- AWS Support: https://aws.amazon.com/support
- EKS Docs: https://docs.aws.amazon.com/eks/latest/userguide/update-cluster.html


