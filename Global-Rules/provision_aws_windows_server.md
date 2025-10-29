# Provision AWS Windows Server

## Goal
Stand up an AWS Windows host with predictable configuration while keeping every step portable.

## Use When
- A project needs IIS, .NET, or other Windows-only components.
- You want parity with the Linux provisioning workflow but for Windows images.
- Previous automation relied on path-specific scripts that no longer apply.

## Optional MCP Shortcuts
- `awslabs.ec2-mcp-server`: create and tag the instance. Without it, use AWS CLI or Console manually.
- `filesystem`: store PowerShell bootstrap scripts inside the repo. Without it, manage them locally and commit later.
- `memory`: capture credentials handoff and maintenance tasks. Without it, log them in a shared checklist.

## Steps
1. Gather requirements
   - Choose the Windows Server edition, instance type, storage, and region. Verify values against `REQUIRED_VARIABLES.txt`.
   - Ensure you have a key pair or Systems Manager access for remote administration.
2. Launch the instance
   - With MCP access, call `awslabs.ec2-mcp-server` to provision the AMI, subnet, and security groups.
   - Otherwise use `aws ec2 run-instances` (or the console) and document the instance ID.
3. Harden and configure
   - Set administrator credentials, enable Windows Update, configure firewall rules, and add required roles or features.
   - Store PowerShell scripts for user creation, package install, and logging in the repo.
4. Prepare application stack
   - Install IIS, .NET, Node, or runtime dependencies. Configure services to start automatically.
   - Record any DNS entries, load balancers, or certificates linked to the host.
5. Validate and share
   - Confirm RDP access, run smoke tests, and capture system state (installed software, open ports).
   - Summarize the build steps and next workflows (usually deployment or monitoring setup).

## Outputs
- Documented instance details, security settings, and bootstrap scripts.
- Checklist of maintenance tasks (patching, backups, credential rotation).
- Ready handoff to the deployment workflow.
