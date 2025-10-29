# Deploy Mobile App to AWS Windows Server

## Goal
Deliver mobile backend services or Windows-hosted tooling that supports mobile clients without relying on bespoke scripts.

## Use When
- Mobile apps depend on Windows-hosted APIs, push notification services, or build agents.
- Builds must be deployable across environments with the same directions.
- Environment variables are centrally managed and only need validation.

## Optional MCP Shortcuts
- `awslabs.ec2-mcp-server`: copy files or run PowerShell remotely. Without it, use WinRM, RDP, or Systems Manager.
- `filesystem`: store release assets and documentation. Without it, archive them wherever you normally keep artifacts.
- `sequential-thinking`: outline the deployment order. Without it, use a manual checklist.

## Steps
1. Build deliverables
   - Produce mobile artifacts (OTA bundle, static assets) and backend packages (zip, MSI, service binaries).
   - Ensure variables in `REQUIRED_VARIABLES.txt` are mapped to appsettings or web.config values.
2. Stage the Windows host
   - Confirm prerequisites (IIS features, background service accounts, certificates) are ready.
   - Back up current binaries or take a snapshot if required.
3. Deploy
   - Transfer packages using MCP or your usual remote tooling.
   - Update IIS sites, Windows services, or scheduled tasks with the new binaries.
   - Run any database migrations before bringing the app online.
4. Validate
   - Hit key API endpoints, notification queues, and background jobs used by the mobile clients.
   - Confirm telemetry and logging show expected traffic.
5. Wrap up
   - Record release details, rollback actions, and required follow-up (store submissions, QA sign-off).
   - Notify stakeholders of completion and any client updates required.

## Outputs
- Updated binaries and mobile assets deployed to the Windows host.
- Documented release notes and validation checks.
- Follow-up task list for client updates or monitoring adjustments.
