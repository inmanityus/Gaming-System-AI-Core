# Quick Start Guide
## AI-Driven Game Testing System - The Body Broker

**Get up and running in 15 minutes**

---

## Prerequisites

- ✅ Windows 10/11
- ✅ UE5 5.6.1 installed
- ✅ Python 3.11+
- ✅ Node.js 18+
- ✅ AWS CLI configured
- ✅ Docker Desktop (optional)

---

## Step 1: Configure API Keys (5 minutes)

### Required Keys:
1. **OpenAI API Key** - For GPT-4o vision analysis
2. **Google API Key** - For Gemini 2.5 Pro  
3. **Anthropic API Key** - For Claude Sonnet 4.5

### Update Secrets Manager:

```powershell
# Get current secret
$Secret = aws secretsmanager get-secret-value --secret-id bodybroker/api-keys --query 'SecretString' --output text | ConvertFrom-Json

# Add your real API keys
$Secret.OPENAI_API_KEY = "sk-proj-YOUR-KEY-HERE"
$Secret.GOOGLE_API_KEY = "AIzaSy-YOUR-KEY-HERE"
$Secret.ANTHROPIC_API_KEY = "sk-ant-YOUR-KEY-HERE"

# Update secret
$SecretJson = $Secret | ConvertTo-Json -Compress
aws secretsmanager update-secret --secret-id bodybroker/api-keys --secret-string $SecretJson

# Restart orchestrator to load new keys
aws ecs update-service --cluster gaming-system-cluster --service body-broker-qa-orchestrator --force-new-deployment
```

---

## Step 2: Start Local Test Runner Agent (2 minutes)

```powershell
# Navigate to agent directory
cd ai-testing-system/local-test-runner

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Run agent (runs continuously)
python agent.py

# Output: "Local Test Runner Agent running"
# Agent monitors: unreal/GameObserver/Captures/
```

**Keep this terminal open** - agent runs continuously

---

## Step 3: Start Triage Dashboard (2 minutes)

```powershell
# Open NEW terminal
cd ai-testing-system/dashboard

# Install dependencies (first time only)
npm install

# Start development server
npm run dev

# Dashboard at: http://localhost:3000
```

**Keep this terminal open** - dashboard runs continuously

---

## Step 4: Test the System (5 minutes)

### Option A: Manual Test (Quick)

```powershell
# Create test capture manually
cd unreal/GameObserver/Captures

# Create test screenshot
Copy-Item "path\to\any\image.png" "Baseline_0001_test.png"

# Create test telemetry JSON
@"
{
  "screenshot_filename": "Baseline_0001_test.png",
  "timestamp": "$(Get-Date -Format o)",
  "event_type": "Baseline",
  "player_data": {"health": 100},
  "world_data": {"zone_name": "Test"},
  "rendering_data": {"current_fps": 60}
}
"@ | Out-File "Baseline_0001_test.json" -Encoding UTF8

# Watch agent terminal - should detect files and upload to S3
# Watch dashboard - issue should appear after analysis (~30 seconds)
```

### Option B: Full Integration Test (Requires Game Running)

```powershell
# Build Body Broker with GameObserver plugin
& "C:\Program Files\Epic Games\UE_5.6\Engine\Build\BatchFiles\Build.bat" `
  BodyBrokerEditor Win64 Development `
  "E:\Vibe Code\Gaming System\AI Core\unreal\BodyBroker.uproject"

# Open in UE5 Editor
# Add GameObserverComponent to PlayerController blueprint
# Enable baseline capture (2 FPS)
# Play in Editor (PIE)
# Perform actions (take damage, change zones, etc.)
# Screenshots auto-captured and analyzed
```

---

## Step 5: Verify System is Working (1 minute)

### Check Orchestrator:
```powershell
Invoke-RestMethod -Uri "http://54.174.89.122:8000/stats"
```

**Expected Output:**
```json
{
  "total_captures": 1+,
  "analyzed": 1+,
  "issues_flagged": 0+
}
```

### Check Dashboard:
- Open http://localhost:3000
- Should see issues list (if any flagged)
- Click issue to see detailed analysis

### Check S3:
```powershell
aws s3 ls s3://body-broker-qa-captures/captures/ --recursive
```

**Expected Output:**
```
2025-11-11 ... captures/2025-11-11T.../Baseline_0001_test.png
2025-11-11 ... captures/2025-11-11T.../Baseline_0001_test.json
```

---

## 🎯 What Happens in the Workflow?

```
1. GameObserver captures screenshot + JSON
   └─> unreal/GameObserver/Captures/

2. Local Agent detects new files
   └─> Bundles and uploads to S3

3. Agent notifies Orchestrator
   └─> POST http://54.174.89.122:8000/captures/new

4. Orchestrator dispatches to Vision Models
   ├─> Gemini 2.5 Pro analyzes (horror atmosphere)
   ├─> GPT-4o analyzes (UX/clarity)
   └─> Claude analyzes (visual bugs)

5. Orchestrator evaluates consensus
   └─> If ≥2 models agree + >0.85 confidence → Issue flagged

6. Recommendation Generator creates structured fix
   └─> Stored in system (viewable in Dashboard)

7. Human reviews in Triage Dashboard
   ├─> Accept → Create Jira ticket (future)
   └─> Reject → Feedback improves models
```

---

## 🐛 Troubleshooting

### Agent not uploading:
```powershell
# Check agent logs
Get-Content ai-testing-system/local-test-runner/test-runner-agent.log -Tail 50

# Verify AWS credentials
aws sts get-caller-identity
```

### Dashboard shows no data:
```powershell
# Check orchestrator API directly
Invoke-RestMethod -Uri "http://54.174.89.122:8000/captures"

# Check S3 bucket
aws s3 ls s3://body-broker-qa-captures/captures/ --recursive
```

### Orchestrator not responding:
```powershell
# Check ECS service status
aws ecs describe-services --cluster gaming-system-cluster --services body-broker-qa-orchestrator --query 'services[0].[status,runningCount,events[0].message]'

# Check CloudWatch logs
aws logs tail /ecs/body-broker/qa-orchestrator --follow
```

---

## 📊 Monitoring Commands

### Check System Health:
```powershell
# Full health check
Invoke-RestMethod -Uri "http://54.174.89.122:8000/health"

# Statistics
Invoke-RestMethod -Uri "http://54.174.89.122:8000/stats"

# Redis cache status
aws elasticache describe-cache-clusters --cache-cluster-id body-broker-qa-cache --query 'CacheClusters[0].CacheClusterStatus'
```

### View Recent Activity:
```powershell
# Recent captures
aws s3 ls s3://body-broker-qa-captures/captures/ --recursive | Select-Object -Last 20

# SQS queue depth
aws sqs get-queue-attributes --queue-url "https://sqs.us-east-1.amazonaws.com/695353648052/body-broker-qa-analysis-jobs" --attribute-names ApproximateNumberOfMessages

# Service logs
aws logs tail /ecs/body-broker/qa-orchestrator --since 10m
```

---

## 🎉 Success Indicators

You'll know the system is working when:

1. ✅ Agent terminal shows "Uploaded: Baseline_0001_test"
2. ✅ Orchestrator stats show total_captures > 0
3. ✅ Dashboard displays issue cards (if any flagged)
4. ✅ S3 bucket contains PNG + JSON files
5. ✅ CloudWatch logs show "INFO: New capture registered"

---

## 🚀 Next Steps After Quick Start

1. Integrate GameObserver into Body Broker game events
2. Run comprehensive test suite
3. Build benchmark dataset
4. Validate model accuracy
5. Configure monitoring
6. Security hardening

---

**Quick Start Version:** 1.0.0  
**Last Updated:** 2025-11-11  
**Estimated Time:** 15 minutes  
**Difficulty:** Intermediate

**For detailed instructions, see [DEPLOYMENT.md](DEPLOYMENT.md)**

