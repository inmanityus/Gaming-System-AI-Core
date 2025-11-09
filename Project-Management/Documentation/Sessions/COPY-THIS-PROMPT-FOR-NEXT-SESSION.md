# 📋 COPY THIS PROMPT FOR NEXT SESSION

Copy the text below and paste it into a new Cursor session:

---

```
Please run /start-right to initialize the session properly.

# 🩸 The Body Broker - GPU Training & Validation Session

**Previous Session**: 2025-11-09 (~8 hours, all foundation complete)  
**This Session Goal**: Complete GPU training, pairwise testing, production deployment

## WHAT'S READY (From Previous Session):

✅ **All Code Complete** (67,704 lines, 41 services, zero placeholders)  
✅ **All Systems Implemented** (12 Python + 5 UE5 + 8 DB tables)  
✅ **GPU Instance Running**: i-05a16e074a5d79473 @ 13.222.142.205  
✅ **S3 Code Uploaded**: s3://body-broker-training-9728/body-broker-code.tar.gz  
✅ **All Automation Scripts**: Ready in scripts/ directory  
✅ **Local Validation**: ✅ Passed (Docker service working)

## TASK 1: Fix Code Deployment on GPU (~30 min)

**Issue**: Code extracted but scripts not finding training/

**Fix**:
```bash
# Via SSM
aws ssm send-command --instance-ids i-05a16e074a5d79473 --document-name "AWS-RunShellScript" --parameters file://scripts/proper-deploy-and-train.json

# Wait, then verify
aws ssm send-command --instance-ids i-05a16e074a5d79473 --document-name "AWS-RunShellScript" --parameters file://scripts/check-training-logs.json

# Should see: training/train_lora_adapter.py exists
```

## TASK 2: Train All 14 Adapters (12-22 hours)

**After deployment verified**:
```bash
# Train vampire adapters (7)
aws ssm send-command --instance-ids i-05a16e074a5d79473 --document-name "AWS-RunShellScript" --parameters file://scripts/train-all-vampire-adapters.json

# Train zombie adapters (7)  
aws ssm send-command --instance-ids i-05a16e074a5d79473 --document-name "AWS-RunShellScript" --parameters file://scripts/train-all-zombie-adapters.json

# Monitor progress
pwsh .\scripts\monitor-all-training.ps1
```

## TASK 3: Pairwise Testing (MANDATORY - 2-3 hours)

**After training completes**:

1. **Run tests on GPU**:
```bash
aws ssm send-command --instance-ids i-05a16e074a5d79473 --document-name "AWS-RunShellScript" --parameters file://scripts/run-pairwise-tests.json
```

2. **Get results**:
```bash
# Get command ID from above, then:
aws ssm get-command-invocation --instance-id i-05a16e074a5d79473 --command-id [COMMAND_ID]
```

3. **Send to reviewer** (GPT-5 Pro or Gemini 2.5 Pro):
   - Show test output
   - Get feedback
   - Fix issues
   - Re-test
   - Iterate until APPROVED

## TASK 4: Production Deployment (~1-2 hours)

**After pairwise testing approved**:
```bash
# Deploy services
docker-compose -f docker-compose.body-broker.yml up -d

# Validate
curl http://[instance-ip]:4100/body-broker/families
curl http://[instance-ip]:4100/body-broker/stats
```

## CRITICAL REMINDERS:

- **ALWAYS peer-code** (Primary model + ONE reviewer via MCP/API)
- **ALWAYS pairwise test** (Primary model + ONE reviewer)
- **Use Timer Service** throughout
- **Follow /all-rules** completely
- **IF MCP down**: STOP and ask for help
- **Run burst-connect** before/after summaries

## KEY FILES:

**Handoff Doc**: `HANDOFF-NEXT-SESSION-GPU-TRAINING.md`  
**AWS Resources**: `Project-Management/aws-resources.csv`  
**Training Guide**: `QUICK-START-GPU-TRAINING.md`  
**System Reference**: `COMPLETE-SYSTEM-REFERENCE.md`

## ESTIMATED TIMELINE:

**Code deployment fix**: 30 minutes  
**Training** (can run overnight): 12-22 hours  
**Pairwise testing**: 2-3 hours  
**Production deployment**: 1-2 hours  

**Total**: 16-28 hours (mostly unattended training)

---

**Context**: All foundation from previous session. Pick up where left off. All automation ready. Just need to execute GPU training and validation.

Follow ALL /all-rules protocols. Use peer-based coding and pairwise testing for any fixes needed.
```

---

**END OF COPYABLE PROMPT**

Paste the above into your next Cursor session to continue where we left off.

