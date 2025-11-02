# AWS Deployment Setup Guide
**Date**: 2025-01-29  
**Status**: Implementation Guide

---

## 🚨 CRITICAL: Protect Dev Computer

**Problem**: Local development computer cannot handle running all AI models locally - performance degradation and resource exhaustion.

**Solution**: Build and test locally, then deploy models to AWS for production execution.

---

## 📋 PREREQUISITES

### 1. AWS CLI Installation
```powershell
# Download and install AWS CLI
# https://aws.amazon.com/cli/

# Verify installation
aws --version

# Configure credentials
aws configure --profile default
```

### 2. AWS Account Setup
- AWS Account with appropriate permissions
- IAM user with ECR, ECS/EKS, CloudFormation permissions
- Region selected (default: us-east-1)

### 3. Docker Installation
```powershell
# Verify Docker is installed
docker --version

# Docker must be running
docker ps
```

---

## 🚀 QUICK START

### Immediate Relief: Shutdown Local Models
```powershell
# Stop all local AI model services NOW
.\scripts\shutdown-local-models.ps1
```

This will:
- ✅ Stop Ollama (local LLM service)
- ✅ Stop Python model inference services
- ✅ Stop Docker containers running models
- ✅ Free up resources immediately

---

## 📋 FULL DEPLOYMENT WORKFLOW

### Step 1: Build & Test Locally
```powershell
# Build everything
python -m py_compile services/**/*.py

# Build UE5 (if applicable)
.\scripts\build-ue5-project.ps1

# Run all tests
python -m pytest services/**/tests/ -v
```

**Requirement**: All tests must pass (100%) before proceeding.

### Step 2: Deploy to AWS
```powershell
# Full deployment workflow
.\scripts\aws-deploy-full.ps1

# Or step by step:
.\scripts\aws-deploy-services.ps1
.\scripts\aws-test-services.ps1
.\scripts\shutdown-local-models.ps1
```

### Step 3: Verify Deployment
```powershell
# Test AWS services
.\scripts\aws-test-services.ps1

# Check service health
# (Update endpoints in script based on your AWS setup)
```

---

## 🔧 CONFIGURATION

### Environment Variables
Create `.env.aws` with:
```env
AWS_PROFILE=default
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=your-account-id

# Service endpoints (set after deployment)
AWS_STORY_TELLER_URL=https://your-story-teller-url.execute-api.us-east-1.amazonaws.com
AWS_AI_INTEGRATION_URL=https://your-ai-integration-url.execute-api.us-east-1.amazonaws.com
AWS_EVENT_BUS_URL=https://your-event-bus-url.execute-api.us-east-1.amazonaws.com
AWS_TIME_MANAGER_URL=https://your-time-manager-url.execute-api.us-east-1.amazonaws.com
AWS_WEATHER_MANAGER_URL=https://your-weather-manager-url.execute-api.us-east-1.amazonaws.com
```

### AWS Infrastructure Setup
1. **Create ECR Repository**
   ```powershell
   aws ecr create-repository --repository-name bodybroker-services --region us-east-1
   ```

2. **Deploy Infrastructure** (Terraform/CDK)
   - Create VPC, security groups
   - Create ECS/EKS cluster (or Lambda functions)
   - Create RDS/DynamoDB databases
   - Create API Gateway endpoints
   - Create IAM roles and policies

3. **Configure Services**
   - Update service endpoints in `.env.aws`
   - Update service discovery configuration
   - Update inter-service communication URLs

---

## 📊 MONITORING

### AWS CloudWatch
- Monitor service logs
- Monitor service metrics
- Set up alarms for errors

### Local Monitoring
```powershell
# Check if local models are still running
Get-Process -Name "ollama" -ErrorAction SilentlyContinue
Get-Process python* | Where-Object { $_.CommandLine -like "*model*" }
```

---

## ⚠️ TROUBLESHOOTING

### Issue: AWS CLI not found
**Solution**: Install AWS CLI from https://aws.amazon.com/cli/

### Issue: Docker login fails
**Solution**: 
```powershell
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin your-account-id.dkr.ecr.us-east-1.amazonaws.com
```

### Issue: Services not accessible
**Solution**: 
- Check security groups allow traffic
- Check IAM roles have correct permissions
- Verify service endpoints are correct

### Issue: Local models still running
**Solution**: 
```powershell
# Force stop
.\scripts\shutdown-local-models.ps1

# Manual stop
Stop-Process -Name "ollama" -Force
```

---

## ✅ SUCCESS CRITERIA

Deployment is successful when:
- ✅ All services deployed to AWS
- ✅ All AWS tests passing (100%)
- ✅ Local models stopped
- ✅ Dev system connects to AWS backend
- ✅ No errors in CloudWatch logs

---

## 📝 NEXT STEPS

After successful deployment:
1. Update local development configuration to use AWS endpoints
2. Test local dev tools with AWS backend
3. Monitor AWS services for issues
4. Continue development with AWS backend

---

**Status**: ✅ **AWS Deployment Workflow Ready**



