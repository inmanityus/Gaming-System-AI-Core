# Deploy to AWS Windows Server

## Goal
Deliver a Windows-based release (API, desktop service, or IIS site) using a repeatable, script-light process.

## Use When
- A Windows instance is prepared and you are ready to roll out an update.
- Deployment steps must travel cleanly between staging, production, or client accounts.
- Environment variables are managed centrally and only need confirmation.

## Optional MCP Shortcuts
- `awslabs.ec2-mcp-server`: execute remote PowerShell commands or transfer files. Without it, use WinRM, RDP, or Systems Manager.
- `filesystem`: archive release artifacts. Without it, rely on the repo or artifact storage you already maintain.
- `sequential-thinking`: plan deployment phases. Without it, check off each step manually.

## Steps
1. Confirm readiness
   - Verify branch, build number, and release notes. Ensure the latest tests and backups are complete.
   - Cross-check `REQUIRED_VARIABLES.txt` against the environment configuration (web.config, appsettings, or parameter store).
2. Package
   - Build the application or service (MSBuild, dotnet publish, npm run build) and bundle supporting files.
   - Upload artifacts via MCP or copy them with SMB/WinSCP/Systems Manager.
3. Deploy
   - For IIS: create or update the site, bindings, and app pool. For services: stop, replace binaries, and restart.
   - Run database migrations or configuration scripts before starting traffic.
4. Validate
   - Hit health endpoints, run synthetic checks, and inspect Event Viewer for errors.
   - Review monitoring dashboards or logs to confirm stable performance.
5. Record
   - Document the deployment window, approvers, commands used, and rollback procedure.
   - Flag any follow-up tasks, especially certificate renewals or scheduled maintenance.

## Outputs
- Deployment notes committed to the repo or stored with release records.
- Updated environment config confirming the required variables.
- Evidence of successful smoke tests and monitoring checks.
