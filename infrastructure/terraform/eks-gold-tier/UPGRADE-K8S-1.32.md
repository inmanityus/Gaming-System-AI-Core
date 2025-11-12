# EKS Kubernetes Upgrade Guide: 1.29 → 1.32

## Overview

AWS has notified that Kubernetes version 1.29 support will end on **March 23, 2026**. This guide provides step-by-step instructions to upgrade the `gaming-ai-gold-tier` EKS cluster from Kubernetes 1.29 to 1.32.

## Why 1.32?

- AWS recommends upgrading to **1.32 or higher** to minimize the frequency of future upgrades
- Version 1.33 is the latest supported version, but 1.32 provides a good balance between stability and longevity
- Avoids the need for extended support fees

## Prerequisites

1. **AWS CLI** configured with appropriate permissions
2. **Terraform** >= 1.5.0
3. **kubectl** installed and configured
4. **Backup** of current cluster state
5. **Maintenance window** scheduled (upgrade can take 30-60 minutes)

## Pre-Upgrade Checklist

- [ ] Verify all workloads are healthy: `kubectl get pods --all-namespaces`
- [ ] Check for deprecated API versions in use
- [ ] Review addon compatibility
- [ ] Backup critical configurations
- [ ] Notify team of maintenance window

## Upgrade Steps

### Step 1: Update Terraform Configuration

The `variables.tf` file has been updated to use Kubernetes 1.32:

```hcl
variable "kubernetes_version" {
  description = "Kubernetes version for EKS cluster"
  type        = string
  default     = "1.32"  # Updated from 1.29
}
```

### Step 2: Plan the Upgrade

```bash
cd infrastructure/terraform/eks-gold-tier
terraform init
terraform plan -out=upgrade.tfplan
```

Review the plan carefully. It should show:
- Cluster version update from 1.29 → 1.32
- Addon updates (if needed)
- No node group changes (nodes will be upgraded separately)

### Step 3: Apply the Upgrade

```bash
terraform apply upgrade.tfplan
```

**Note**: The cluster upgrade will take approximately 30-60 minutes. During this time:
- The control plane will be temporarily unavailable
- Running workloads will continue to function
- New deployments may be delayed

### Step 4: Verify Cluster Upgrade

```bash
# Check cluster version
aws eks describe-cluster --name gaming-ai-gold-tier --query 'cluster.version'

# Verify cluster status
aws eks describe-cluster --name gaming-ai-gold-tier --query 'cluster.status'

# Update kubectl context
aws eks update-kubeconfig --name gaming-ai-gold-tier --region us-east-1

# Verify nodes are accessible
kubectl get nodes
```

### Step 5: Upgrade Node Groups

After the control plane upgrade, node groups need to be upgraded:

```bash
# Check current node versions
kubectl get nodes -o wide

# Nodes will automatically upgrade to match control plane version
# This happens during the next node replacement or when you trigger an update
```

To force node group upgrade:

```bash
# Update node group (this will perform a rolling update)
aws eks update-nodegroup-version \
  --cluster-name gaming-ai-gold-tier \
  --nodegroup-name gold-tier-gpu \
  --region us-east-1
```

### Step 6: Verify Addon Compatibility

Check that all addons are compatible with 1.32:

```bash
# List installed addons
aws eks list-addons --cluster-name gaming-ai-gold-tier

# Check addon versions
aws eks describe-addon-versions --addon-name vpc-cni --kubernetes-version 1.32
```

Update addons if needed:

```bash
# Update addon (example for vpc-cni)
aws eks update-addon \
  --cluster-name gaming-ai-gold-tier \
  --addon-name vpc-cni \
  --addon-version latest \
  --region us-east-1
```

### Step 7: Post-Upgrade Verification

1. **Verify all pods are running:**
   ```bash
   kubectl get pods --all-namespaces
   ```

2. **Check application health:**
   ```bash
   # Test your applications
   # Verify NPC inference services are working
   ```

3. **Monitor logs for errors:**
   ```bash
   kubectl logs -n <namespace> <pod-name>
   ```

## Rollback Plan

If issues occur, you can rollback by:

1. **Revert Terraform configuration:**
   ```bash
   # Edit variables.tf to set version back to 1.29
   # Then apply
   terraform apply
   ```

   **Note**: AWS does not support downgrading EKS clusters. You would need to:
   - Create a new cluster with 1.29
   - Migrate workloads
   - Delete the upgraded cluster

2. **Alternative**: Contact AWS Support for assistance

## Troubleshooting

### Issue: Cluster stuck in "UPDATING" state

**Solution**: 
- Wait up to 60 minutes for the upgrade to complete
- Check AWS CloudWatch logs
- Contact AWS Support if stuck beyond 60 minutes

### Issue: Pods not starting after upgrade

**Solution**:
- Check for deprecated API versions: `kubectl get --raw /api/v1`
- Update manifests to use current APIs
- Review pod logs: `kubectl describe pod <pod-name>`

### Issue: Addons not compatible

**Solution**:
- Update addons to latest versions compatible with 1.32
- Check addon documentation for migration guides

## Timeline

- **Pre-upgrade preparation**: 1-2 hours
- **Control plane upgrade**: 30-60 minutes
- **Node group upgrade**: 30-60 minutes (rolling)
- **Verification**: 1-2 hours
- **Total estimated time**: 3-5 hours

## References

- [AWS EKS Upgrade Documentation](https://docs.aws.amazon.com/eks/latest/userguide/update-cluster.html)
- [Kubernetes Version Support](https://docs.aws.amazon.com/eks/latest/userguide/kubernetes-versions.html)
- [API Deprecation Guide](https://kubernetes.io/docs/reference/using-api/deprecation-guide/)

## Support

For issues or questions:
- AWS Support: https://aws.amazon.com/support
- EKS Documentation: https://docs.aws.amazon.com/eks/






