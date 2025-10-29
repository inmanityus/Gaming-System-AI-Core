# Deploy Mobile App to AWS Linux Server

## Goal
Publish a mobile backend or Expo/React Native web build to an AWS Linux host with predictable steps.

## Use When
- Mobile clients rely on a Linux-hosted API, job runner, or web bundle.
- You want one deployment recipe that works for staging and production without custom scripts.
- Build artifacts already exist or can be generated locally.

## Optional MCP Shortcuts
- `awslabs.ec2-mcp-server`: transfer bundles or run remote commands. Without it, use SSH and SCP.
- `filesystem`: package artifacts alongside release notes. Without it, use your usual artifact storage.
- `sequential-thinking`: stage rollout tasks. Without it, work down the checklist manually.

## Steps
1. Build client assets
   - Generate the mobile build artifacts (Expo web build, OTA bundle, or static assets) and upload them to artifact storage.
   - Review `REQUIRED_VARIABLES.txt` to ensure API URLs, feature flags, and keys are present.
2. Prepare the backend
   - Confirm API migrations and background jobs are ready. Run tests relevant to mobile flows.
   - Package backend code (Docker image or tarball) for deployment.
3. Deploy to Linux
   - Copy backend package and mobile assets to the server using MCP or native tools.
   - Apply zero-downtime reloads (systemd reload, Docker rollout, process manager restart).
4. Validate
   - Smoke test critical mobile endpoints and push notification paths.
   - If possible, load the mobile web build or OTA update to confirm it references the new backend.
5. Communicate
   - Share release notes, rollback steps, and next actions (store submissions, feature flag flips).
   - Log deployment timestamp and environment details for future reference.

## Outputs
- Backend and mobile artifacts deployed and verified.
- Release summary stored with the repo or deployment journal.
- Clear checklist for follow-up steps (app store submission, monitoring review, analytics validation).
