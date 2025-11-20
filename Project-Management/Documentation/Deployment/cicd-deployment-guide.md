# CI/CD Pipeline Deployment Guide

## Pre-Deployment Checklist

### 1. AWS Resources
- [ ] ECR repository exists: `695353648052.dkr.ecr.us-east-1.amazonaws.com/bodybroker-services`
- [ ] ECS clusters exist: `gaming-system-cluster` (production), `gaming-system-cluster-staging`
- [ ] IAM roles created:
  - [ ] `github-actions-ecr-push` - For pushing images to ECR
  - [ ] `github-actions-deploy-staging` - For staging deployments
  - [ ] `github-actions-deploy-production` - For production deployments

### 2. GitHub Configuration
- [ ] Repository secrets configured:
  - [ ] `AWS_ACCOUNT_ID`: 695353648052
  - [ ] `AWS_REGION`: us-east-1
- [ ] Environments configured:
  - [ ] `staging` environment with protection rules
  - [ ] `production` environment with:
    - Required reviewers
    - Deployment branch restrictions (main only)

### 3. Required IAM Permissions

#### github-actions-ecr-push
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecr:GetAuthorizationToken",
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage",
        "ecr:PutImage",
        "ecr:InitiateLayerUpload",
        "ecr:UploadLayerPart",
        "ecr:CompleteLayerUpload"
      ],
      "Resource": "*"
    }
  ]
}
```

#### github-actions-deploy-staging/production
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecs:UpdateService",
        "ecs:DescribeServices",
        "ecs:RegisterTaskDefinition",
        "ecs:DescribeTaskDefinition",
        "ecs:ListTasks",
        "ecs:DescribeTasks",
        "cloudwatch:PutMetricAlarm",
        "cloudwatch:DescribeAlarms",
        "codedeploy:CreateDeployment",
        "codedeploy:GetDeployment",
        "iam:PassRole"
      ],
      "Resource": "*"
    }
  ]
}
```

## Deployment Steps

### Step 1: Create GitHub Environments

1. Go to Settings → Environments in your GitHub repository
2. Create `staging` environment:
   ```
   - Name: staging
   - Protection rules: None (or add as needed)
   - Environment secrets: None (uses repository secrets)
   ```
3. Create `production` environment:
   ```
   - Name: production
   - Protection rules:
     - Required reviewers: 1-2 team members
     - Deployment branches: main only
     - Wait timer: 5 minutes (optional)
   ```

### Step 2: Configure OIDC for AWS

1. Create OIDC provider in AWS IAM:
   ```bash
   aws iam create-open-id-connect-provider \
     --url https://token.actions.githubusercontent.com \
     --client-id-list sts.amazonaws.com \
     --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1
   ```

2. Create trust policy for GitHub Actions:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Principal": {
           "Federated": "arn:aws:iam::695353648052:oidc-provider/token.actions.githubusercontent.com"
         },
         "Action": "sts:AssumeRoleWithWebIdentity",
         "Condition": {
           "StringEquals": {
             "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
             "token.actions.githubusercontent.com:sub": "repo:<OWNER>/<REPO>:ref:refs/heads/main"
           }
         }
       }
     ]
   }
   ```

### Step 3: Commit Workflow Files

1. Ensure all workflow files are in `.github/workflows/`:
   - `comprehensive-ci-v2.yml` - Main CI pipeline with path filtering
   - `deploy-with-promotion.yml` - Deployment workflow
   - `security-scan.yml` - Security scanning workflow

2. Ensure supporting files exist:
   - `.github/services.json` - Service configuration
   - `scripts/validate-python-imports.py`
   - `scripts/smoke-test-service-v2.sh`
   - `scripts/monitor-production-deployment.sh`

3. Commit and push to main branch:
   ```bash
   git add .github/workflows/ .github/services.json scripts/
   git commit -m "feat: Add production-ready CI/CD pipeline with security scanning"
   git push origin main
   ```

### Step 4: Test the Pipeline

1. **Test CI Pipeline**:
   - Create a test PR with a small change to one service
   - Verify only that service is built and tested
   - Check that security scans run successfully

2. **Test Deployment**:
   - Go to Actions → Deploy with Promotion
   - Run workflow with:
     - Service: knowledge-base (or any service)
     - Image tag: latest commit SHA
     - Environment: staging
     - Strategy: rolling
   - Verify deployment completes successfully

3. **Test Security Scanning**:
   - Go to Actions → Security Scanning
   - Run workflow manually
   - Review security findings in GitHub Security tab

## Post-Deployment Verification

### 1. Verify Workflows Active
```bash
# Check workflow runs
gh run list --workflow comprehensive-ci-v2.yml
gh run list --workflow deploy-with-promotion.yml
gh run list --workflow security-scan.yml
```

### 2. Verify Path Filtering
- Make a change to a single service
- Create a PR
- Verify only that service is tested/built

### 3. Verify Caching
- Re-run a workflow
- Check build times are significantly reduced
- Verify cache hit rates in workflow logs

### 4. Test Rollback
- Deploy a service to staging
- Manually fail the deployment (e.g., wrong image tag)
- Verify automatic rollback occurs

## Monitoring and Maintenance

### Daily Checks
- Review failed workflow runs
- Check security scan results
- Monitor build times and costs

### Weekly Tasks
- Review and merge Dependabot PRs
- Check for workflow updates
- Review AWS costs for CI/CD

### Monthly Tasks
- Audit IAM permissions
- Review and optimize caching strategies
- Update workflow dependencies

## Troubleshooting

### Common Issues

1. **OIDC Authentication Failures**
   - Verify trust policy matches repository
   - Check IAM role ARN in workflow
   - Ensure workflow has id-token: write permission

2. **Path Filtering Not Working**
   - Verify git history is fetched (fetch-depth: 0)
   - Check services.json paths match actual directories
   - Test with git diff locally

3. **Cache Misses**
   - Check cache key includes file hashes
   - Verify restore keys are properly ordered
   - Monitor cache size limits

4. **Deployment Failures**
   - Check ECS service quotas
   - Verify task definition is valid
   - Review CloudWatch logs

## Rollback Procedure

If the CI/CD pipeline causes issues:

1. **Immediate Rollback**:
   ```bash
   # Revert to previous workflow versions
   git revert <commit-with-workflows>
   git push origin main
   ```

2. **Disable Workflows**:
   - Go to Actions → Select workflow → ⋮ → Disable workflow

3. **Manual Deployment**:
   - Use existing scripts in `scripts/` directory
   - Follow previous manual deployment procedures

## Success Metrics

Track these metrics to measure CI/CD effectiveness:

- **Build Success Rate**: Target > 95%
- **Average Build Time**: Target < 10 minutes
- **Deployment Success Rate**: Target > 99%
- **Time to Deploy**: Target < 5 minutes
- **Security Findings Fixed**: Target < 48 hours

## Next Steps

1. **Immediate**:
   - Deploy workflows to repository
   - Test with a non-critical service
   - Monitor for 24 hours

2. **This Week**:
   - Enable for all services
   - Set up alerting for failures
   - Document team processes

3. **This Month**:
   - Optimize build times
   - Implement cost controls
   - Add performance testing

## Support

For CI/CD pipeline issues:
1. Check workflow logs in GitHub Actions
2. Review this documentation
3. Check AWS CloudWatch for deployment logs
4. Create issue with `ci-cd` label
