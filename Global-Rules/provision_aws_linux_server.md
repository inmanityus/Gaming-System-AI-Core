# Provision AWS Linux Server

## Goal
Create a repeatable process for launching and configuring an AWS Linux instance that fits any project without bespoke scripts.

## Use When
- You need a clean Linux host for APIs, web apps, or background workers.
- Infrastructure should be reproducible between teams or environments.
- Existing automation is tightly coupled to another repository and you want a lighter approach.

## Optional MCP Shortcuts
- `awslabs.ec2-mcp-server`: launch instances or adjust security groups. Without it, run the same AWS CLI commands manually.
- `filesystem`: store provisioning notes or cloud-init templates. Without it, keep the files in your repo.
- `memory`: track decisions and pending follow-ups. Without it, add them to a shared doc.

## Steps
1. Set prerequisites
   - Confirm AWS credentials, region, VPC, and subnet. Check `REQUIRED_VARIABLES.txt` for supported values.
   - Decide on instance family, storage size, and tagging scheme.
2. Launch the instance
   - With `awslabs.ec2-mcp-server`, request the AMI, instance type, key pair, and security groups.
   - Without MCP access, run `aws ec2 run-instances` with the same parameters and record the instance ID.
3. Harden the host
   - Apply updates, create a non-root user, configure SSH, and enable required services.
   - Store bootstrap scripts or Ansible playbooks inside the repo so they can be reused anywhere.
4. Configure application dependencies
   - Install runtimes, package managers, reverse proxies, or metrics agents as needed.
   - Document any ports opened or managed services attached (databases, caches, queues).
5. Verify and hand off
   - Test SSH access, basic health checks, and logging.
   - Capture the AMI ID or automation steps in a short README for future environments.

## Outputs
- Instance details (ID, region, security groups, tags) recorded alongside the project docs.
- Hardened configuration scripts checked into source control.
- Follow-up tasks for deployment, monitoring, or backups.
