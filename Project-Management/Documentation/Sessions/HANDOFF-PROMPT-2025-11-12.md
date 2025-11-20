# 🔄 SESSION HANDOFF PROMPT

**Copy this entire prompt into the next session to continue work:**

---

Please continue the microservices refactoring project. Read the complete handoff document at `.cursor/HANDOFF-2025-11-12-03-00.md` first.

## Context Summary

I'm refactoring 22 Python/FastAPI microservices from monolithic structure (with direct `from services.X import Y` imports) to proper independent microservices with HTTP communication.

**Current Status**: 15 of 22 services running
**Goal**: 22 of 22 services operational with independent architecture
**Approach**: Path C - Proper architectural refactoring (2-4 weeks, no shortcuts)

## Critical Rules (MANDATORY - ALL OF THEM)

Execute these commands to load all rules into your memory:
```
/all-rules
/memory-construct
/collaborate
```

**Key Mandates**:
1. **PEER CODE EVERYTHING** - Use GPT-4o, Gemini 2.5 Pro, or Claude 4.5 Sonnet for ALL code reviews
2. **PAIRWISE TEST EVERYTHING** - Every test validated by reviewer model
3. **NO REPORTING** until 100% complete (then burst-accept → report → burst-accept)
4. **NEVER STOP** - Continue automatically, no questions, no waiting
5. **UNLIMITED RESOURCES** - Take all time needed, quality over speed
6. **DO IT RIGHT** - First time right, no shortcuts
7. **SCRIPT TIMERS** - Show elapsed time for long-running operations

## Active Work

**Phase 1** (60% complete): Refactoring core services
- ✅ Created BaseHTTPClient (peer reviewed by GPT-4o)
- ✅ Created HTTP clients for model-management, state-manager, ai-integration
- ⚠️ In progress: Removing all cross-service imports
- ⏳ Next: Build and deploy Phase 1 services independently

**Phase 2-5** (pending): 18 remaining services in dependency order

## Immediate Next Steps

1. Read `.cursor/HANDOFF-2025-11-12-03-00.md` completely
2. Check current ECS status: How many of 22 services running?
3. Continue removing cross-service imports from all services
4. Build each service with `Dockerfile.independent`
5. Deploy services in tier order (see refactoring plan)
6. Test each service after deployment
7. Peer review all changes
8. Continue until all 22 services operational

## Important Files

- `.cursor/HANDOFF-2025-11-12-03-00.md` - Complete handoff details
- `docs/architecture/microservices-refactoring-plan.md` - Full refactoring plan
- `services/shared/http_clients/base_client.py` - HTTP client base
- `Project-Management/MASTER-TEST-REGISTRY.md` - Test registry

## AWS Resources

- **RDS**: gaming-system-bodybroker-db.cal6eoegigyq.us-east-1.rds.amazonaws.com
- **Secrets**: gaming-system/bodybroker-db-credentials
- **ECS Cluster**: gaming-system-cluster
- **ECR**: 695353648052.dkr.ecr.us-east-1.amazonaws.com/bodybroker-services
- **Region**: us-east-1

## ⏰ TIMER SERVICE (CRITICAL CLARIFICATION)

**Timer Service runs AUTOMATICALLY - DO NOT CALL IT MANUALLY**

The Timer Service:
- Starts automatically in startup.ps1 as silent background job
- Logs to `.cursor/timer-service.log` (NOT console)
- Runs every 10 minutes
- You never interact with it
- **NEVER call Global-Scripts\global-command-timer.ps1 manually**

**WRONG (causes PowerShell window spam)**:
```powershell
& "Global-Scripts\global-command-timer.ps1"  # DON'T DO THIS
```

**RIGHT (just work normally)**:
```powershell
# Timer Service runs automatically - you do nothing
# Just execute your commands normally
docker build ...
aws ecs update-service ...
```

## Script Progress Display (USER REQUESTED)

For long operations (>60s), show progress manually:
```powershell
$start = Get-Date
Write-Host "[Operation] Started at $(Get-Date -Format 'HH:mm:ss')"

# During long operation, periodically show elapsed:
for ($i = 0; $i -lt 100; $i++) {
    # Do work...
    if ($i % 10 -eq 0) {
        $elapsed = ((Get-Date) - $start).TotalSeconds
        Write-Host "[Operation] Running for $([int]$elapsed)s..."
    }
}

$duration = ((Get-Date) - $start).TotalSeconds
Write-Host "[Operation] Completed in $([int]$duration)s"
```

**This is separate from Timer Service - this is just progress display.**

## Validation

After reading this prompt:
- Confirm you've loaded /all-rules, /memory-construct, /collaborate
- Confirm you understand peer coding and pairwise testing are MANDATORY
- Confirm you'll show script timers for long operations
- Confirm you'll work silently until 100% complete
- Then begin work immediately without asking questions

**Do not report, do not stop, continue until all 22 services are operational and tested.**

