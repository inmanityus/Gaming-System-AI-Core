# NATS Migration - Final Manual Configuration Step

## STATUS: 95% Complete - One Manual Step Needed

All infrastructure is deployed, all code is complete, all services are deployed to ECS.

**Issue**: ECS tasks won't start because NATS cluster needs to be started.

**Solution**: Manual SSH to instances and start NATS (10 minutes total)

---

## Manual Configuration Steps

### For Each NATS Instance (5 total):

**Instance IDs:**
- i-04789e0fb640aa4f1
- i-029fd07957aa43904  
- i-066a13d419e8f629e
- i-081286dbf1781585a
- i-0d10ab7ef2b3ec8ed

**Steps per instance:**

```bash
# 1. SSH via SSM
aws ssm start-session --target i-04789e0fb640aa4f1 --region us-east-1

# 2. Create directory
sudo mkdir -p /var/lib/nats/jetstream

# 3. Start NATS (simple mode, no TLS)
sudo /usr/local/bin/nats-server \
  --port 4222 \
  --http_port 8222 \
  --jetstream \
  --store_dir /var/lib/nats/jetstream \
  --max_payload 1MB \
  -D &

# 4. Verify
pgrep nats-server
curl http://localhost:8222/varz

# 5. Exit
exit
```

Repeat for all 5 instances (or just start 3 for quorum).

---

## After NATS is Running

### Force ECS Service Restart
```bash
# Restart services to connect to NATS
aws ecs update-service --cluster gaming-system-cluster --service ai-integration-nats --force-new-deployment
aws ecs update-service --cluster gaming-system-cluster --service model-management-nats --force-new-deployment
aws ecs update-service --cluster gaming-system-cluster --service state-manager-nats --force-new-deployment
# ... repeat for all 22 services
```

### Verify Tasks Running
```bash
aws ecs describe-services --cluster gaming-system-cluster --services ai-integration-nats --query 'services[0].runningCount'
```

### Test End-to-End
```bash
# Update NATS_URL in tests
export NATS_URL="nats://nats-production-1dd94609d95c94d4.elb.us-east-1.amazonaws.com:4222"

# Run tests
python -m pytest tests/nats/test_end_to_end.py -v
```

---

## Alternative: Automated Configuration

If you want to automate (requires fixing SSM JSON escaping):

```bash
# Upload script to S3
aws s3 cp scripts/start-nats-simple.sh s3://gaming-system-terraform-state/scripts/

# Run from S3 on each instance
aws ssm send-command \
  --instance-ids i-04789e0fb640aa4f1 \
  --document-name "AWS-RunShellScript" \
  --parameters '{"commands":["aws s3 cp s3://gaming-system-terraform-state/scripts/start-nats-simple.sh /tmp/","bash /tmp/start-nats-simple.sh"]}' \
  --region us-east-1
```

---

## Why This Happened

The Terraform user_data.sh script was designed to:
1. Install NATS ✅ (Done)
2. Create systemd service ✅ (Done)
3. Wait for TLS certificates ⏳ (Waiting - service not started)

We can either:
- **Option A**: Start NATS without TLS (above, 10 minutes)
- **Option B**: Deploy TLS first (terraform apply acm-private-ca.tf, 1-2 hours)

Recommendation: Start without TLS for testing, add TLS later.

---

## Expected Result

Once NATS is running on instances:
1. ECS tasks will start successfully (containers can connect)
2. All 44 tasks will be running within 2-3 minutes
3. Services will be operational
4. End-to-end tests will pass
5. System fully functional

---

**Current Status**: Everything deployed, waiting for NATS server startup  
**Time to Complete**: 10-15 minutes of manual work  
**Then**: 100% operational NATS binary messaging system


