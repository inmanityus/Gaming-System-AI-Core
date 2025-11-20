# Disabled Workflows

The following workflows have been disabled (.yml → .yml.disabled) because they require external infrastructure or credentials that are not available in CI/CD:

## 1. AWS Deployment Workflows
- **deploy.yml.disabled**
- **deploy-with-promotion.yml.disabled**
- **deploy-with-rollback.yml.disabled**

**Reason**: These workflows require AWS credentials to deploy to ECR/ECS. Per project rules, NO credentials are added to GitHub Secrets.

## 2. Unreal Engine Workflows
- **autonomous-testing.yml.disabled**

**Reason**: Requires Unreal Engine 5.6.1 installed on the runner, which GitHub Actions doesn't provide.

## How to Enable

If you need these workflows in the future:

1. **For AWS workflows**: Set up OIDC authentication or provide AWS credentials via another secure method
2. **For UE5 workflows**: Use self-hosted runners with UE5 installed

To re-enable a workflow:
```bash
mv .github/workflows/<workflow>.yml.disabled .github/workflows/<workflow>.yml
```

## Alternative Solutions

- **Local deployment**: Use the PowerShell scripts in `scripts/` to deploy from your local machine where credentials are available
- **Local testing**: Run UE5 tests locally using the scripts in `scripts/`
