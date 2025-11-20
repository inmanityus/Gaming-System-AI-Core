# GitHub Actions Workflows

This directory contains the CI/CD workflows for the Gaming System AI Core.

## Active Workflows

### Core CI/CD Pipeline
- **comprehensive-ci-v2.yml**: Main CI pipeline with path filtering, security scanning, and caching
- **deploy-with-promotion.yml**: Deployment workflow with staging → production promotion
- **security-scan.yml**: Dedicated security scanning (SAST, dependency scan, container scan)

### Supporting Workflows
- **ci.yml**: Basic CI checks
- **code-quality.yml**: Code quality and linting
- **database-migrations.yml**: Database migration management
- **deploy-with-rollback.yml**: Deployment with rollback capabilities
- **deploy.yml**: Basic deployment workflow
- **release.yml**: Release process automation
- **security.yml**: Additional security checks

### Legacy/Testing
- **autonomous-testing.yml**: Autonomous testing framework
- **comprehensive-ci.yml**: Original comprehensive CI (superseded by v2)

## Retired Workflows

### test-body-broker.yml (Deleted 2025-11-20)
- **Reason**: Attempted to install massive ML dependencies (torch 900MB, vllm 370MB) causing GitHub runners to run out of disk space
- **Problem**: Ran on every push/PR causing spam failure emails
- **Resolution**: Deleted as functionality is covered by comprehensive-ci-v2.yml
- **Alternative**: If full ML stack testing is needed in future, use:
  - Self-hosted runners with sufficient disk space
  - Manual trigger (`workflow_dispatch`) for occasional testing
  - Lightweight mock testing for CI

## Workflow Best Practices

1. **Disk Space**: GitHub runners have ~14GB available. Avoid installing large ML frameworks unless absolutely necessary.
2. **Caching**: Use setup-python-cache action for Python dependencies
3. **Path Filtering**: Only run workflows when relevant files change
4. **Matrix Strategy**: Use services.json for dynamic job generation
5. **Security**: Run security scans on all code changes

## Troubleshooting

### Workflow Failing with Disk Space Errors
- Check if workflow is installing large dependencies
- Consider using Docker images with pre-installed dependencies
- Use self-hosted runners for resource-intensive tasks

### Too Many Workflow Runs
- Implement path filtering to reduce unnecessary runs
- Use `workflow_dispatch` for manual-only workflows
- Consolidate similar workflows
