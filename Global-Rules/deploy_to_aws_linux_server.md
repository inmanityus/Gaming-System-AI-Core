# Deploy to AWS Linux Server

## Goal
Ship a web or API release to an existing AWS Linux host using a portable checklist.

## Use When
- Code is ready and the target Linux instance has already been provisioned.
- You need a repeatable deploy routine that does not rely on bespoke scripts.
- Environment variables are managed centrally and only need to be verified.

## Optional MCP Shortcuts
- `awslabs.ec2-mcp-server`: copy artifacts or run remote commands. Without it, use SSH and SCP directly.
- `filesystem`: package build outputs or release notes. Without it, use local tooling and commit results.
- `sequential-thinking`: stage deployment steps. Without it, work through the checklist manually.

## Steps
1. Prepare
   - Confirm branch, version tag, and changelog. Ensure tests just passed.
   - Review `REQUIRED_VARIABLES.txt` and match them with the target environment file or parameter store.
2. Package
   - Build artifacts (Docker image, zip, static assets). Store them in a repo-accessible location.
   - If MCP access exists, upload via `awslabs.ec2-mcp-server`. Otherwise use `scp`, `rsync`, or a registry push.
3. Deploy
   - Apply migrations or other irreversible steps first while monitoring logs.
   - Restart services gracefully (systemd, PM2, Docker) and keep a rollback command ready.
4. Validate
   - Run smoke tests, ping health endpoints, and confirm metrics/alerts remain green.
   - Capture output and store it beside the deployment record.
5. Close out
   - Document the release (what changed, who approved, rollback instructions).
   - Queue follow-up tasks for monitoring, feature flags, or subsequent deployments.

## Outputs
- Deployment log with the exact commands executed.
- Updated environment documentation proving the variables match `REQUIRED_VARIABLES.txt`.
- Verified application health and a direct rollback path.
