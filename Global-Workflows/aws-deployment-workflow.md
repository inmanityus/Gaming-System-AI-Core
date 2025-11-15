# AWS Deployment Workflow Rule
**Date**: 2025-01-29  
**Status**: MANDATORY - Implement Immediately  
**Priority**: CRITICAL - Protects Dev Computer

---

## 🚨 CRITICAL RULE: AWS Model Deployment

**Problem**: Local development computer cannot handle running all AI models locally - performance degradation and resource exhaustion.

**Solution**: Build and test locally, then deploy to AWS for production model execution.

---

## 📋 DEPLOYMENT WORKFLOW - MANDATORY

### **Phase 1: Local Development & Testing**
1. **Build Everything Locally**
   - Compile all code (Python services, UE5 project, etc.)
   - Ensure all dependencies are installed locally
   - Verify all code compiles without errors
   - **Status**: ✅ All code builds successfully

2. **Test Everything Locally (Dev Mode)**
   - Run ALL unit tests locally
   - Run ALL integration tests locally
   - Run ALL system tests locally
   - Use test databases/local mocks for services
   - **Requirement**: 100% test pass rate before proceeding
   - **Status**: ✅ All tests pass locally

3. **Verify Dev System Integrity**
   - Run comprehensive system health checks
   - Verify all services start correctly
   - Verify inter-service communication works
   - Verify database connections
   - Verify configuration is correct
   - **Requirement**: Dev system fully functional
   - **Status**: ✅ Dev system verified

---

### **Phase 2: AWS Deployment Preparation**
1. **Prepare AWS Deployment Configuration**
   - Create/update AWS infrastructure definitions (CloudFormation/CDK/Terraform)
   - Configure ECS/EKS/Lambda/EC2 as needed for services
   - Set up RDS/DynamoDB/ElastiCache as needed
   - Configure VPC, security groups, IAM roles
   - **Status**: ⏳ AWS config prepared

2. **Package Services for Deployment**
   - Create Docker images for all Python services
   - Package UE5 build artifacts if needed
   - Create deployment packages/scripts
   - Tag versions for deployment tracking
   - **Status**: ⏳ Services packaged

3. **Prepare AWS Infrastructure**
   - Deploy/update AWS infrastructure
   - Verify all resources created correctly
   - Verify network connectivity
   - Verify security configurations
   - **Status**: ⏳ Infrastructure ready

---

### **Phase 3: AWS Deployment**
1. **Deploy Services to AWS**
   - Deploy AI model services to AWS (ECS/EKS/Lambda)
   - Deploy backend API services to AWS
   - Deploy database services (if applicable)
   - Deploy event bus/caching services
   - **Status**: ⏳ Services deploying

2. **Deploy Configuration**
   - Deploy environment variables/secrets to AWS
   - Configure service endpoints
   - Update API gateway routes
   - Configure service discovery
   - **Status**: ⏳ Configuration deployed

3. **Verify AWS Deployment**
   - Check all services are running in AWS
   - Verify service health endpoints
   - Verify service logs for errors
   - Verify service metrics
   - **Status**: ⏳ Deployment verified

---

### **Phase 4: AWS Testing**
1. **Test All Services in AWS**
   - Run integration tests against AWS services
   - Test API endpoints from AWS services
   - Test model inference in AWS
   - Test database operations in AWS
   - **Requirement**: 100% test pass rate
   - **Status**: ⏳ AWS tests running

2. **Test System Integration in AWS**
   - Test inter-service communication in AWS
   - Test end-to-end workflows in AWS
   - Test event bus in AWS
   - Test caching in AWS
   - **Requirement**: All integrations working
   - **Status**: ⏳ Integration tests running

3. **Load Testing in AWS** (Optional but Recommended)
   - Test system under load in AWS
   - Verify auto-scaling works correctly
   - Verify resource utilization is optimal
   - **Status**: ⏳ Load testing (if applicable)

---

### **Phase 5: Dev System Shutdown**
1. **Stop Local Model Services**
   - Stop all local AI model services (Ollama, etc.)
   - Stop local LLM inference services
   - Free up local resources
   - **Status**: ⏳ Local models stopped

2. **Switch Configuration to AWS Endpoints**
   - Update local dev config to point to AWS services
   - Update API endpoints to AWS URLs
   - Update service discovery to AWS
   - **Status**: ⏳ Config switched to AWS

3. **Verify Dev System Works with AWS Backend**
   - Test local dev tools connect to AWS services
   - Test local UI/frontend connects to AWS backend
   - Test local debugging tools work with AWS
   - **Requirement**: Dev workflow functional with AWS backend
   - **Status**: ⏳ Dev-AWS integration verified

---

### **Phase 6: Issue Resolution (Continuous)**
1. **Monitor for Issues**
   - Watch AWS CloudWatch logs for errors
   - Monitor AWS service metrics
   - Monitor local dev system logs
   - **Status**: ⏳ Monitoring active

2. **Fix Issues Immediately**
   - Use `/all-rules` for all fixes
   - Follow `/test-comprehensive` for all testing
   - Deploy fixes immediately
   - Re-test after fixes
   - **Requirement**: All issues resolved before continuing
   - **Status**: ⏳ Issue resolution process

3. **Iterate Until Stable**
   - Repeat testing and fixing until system is stable
   - Verify all services working correctly
   - Verify all integrations working correctly
   - **Status**: ⏳ Iterating to stability

---

## 🔧 IMPLEMENTATION REQUIREMENTS

### **Build Everything Locally**
- ✅ Python services compile/validate
- ✅ UE5 project compiles
- ✅ All dependencies resolved
- ✅ No build errors

### **Test Everything Locally**
- ✅ All unit tests pass (100%)
- ✅ All integration tests pass (100%)
- ✅ All system tests pass (100%)
- ✅ No test failures

### **Verify Dev System**
- ✅ All services start locally
- ✅ All services communicate correctly
- ✅ Database connections work
- ✅ Configuration is correct

### **Deploy to AWS**
- ✅ Infrastructure deployed
- ✅ Services deployed
- ✅ Configuration deployed
- ✅ Services verified running

### **Test in AWS**
- ✅ All AWS tests pass (100%)
- ✅ All integrations work in AWS
- ✅ System works end-to-end in AWS

### **Shutdown Local Models**
- ✅ Local model services stopped
- ✅ Local resources freed
- ✅ Config points to AWS
- ✅ Dev system works with AWS backend

---

## 📝 MANDATORY ENFORCEMENT

**This workflow MUST be followed for:**
- Initial AWS deployment
- Every service update
- Every model update
- Every infrastructure change
- Every configuration change

**NEVER skip phases** - each phase validates the previous and ensures system stability.

---

## 🚀 AUTOMATION

This workflow should be automated via scripts:
- `scripts/aws-deploy-full.ps1` - Full deployment workflow
- `scripts/aws-deploy-services.ps1` - Deploy services only
- `scripts/aws-deploy-infrastructure.ps1` - Deploy infrastructure only
- `scripts/aws-test-services.ps1` - Test AWS services
- `scripts/shutdown-local-models.ps1` - Stop local models

---

## ⚠️ CRITICAL RULES

1. **ALWAYS build and test locally first**
2. **ALWAYS verify dev system before deploying**
3. **ALWAYS test in AWS after deployment**
4. **ALWAYS fix issues immediately using `/all-rules`**
5. **ALWAYS use `/test-comprehensive` for testing**
6. **ALWAYS shut down local models after AWS deployment**
7. **NEVER deploy without local testing first**
8. **NEVER skip AWS testing**
9. **NEVER leave local models running after AWS is ready**

---

## 📊 STATUS TRACKING

Each phase must have clear status indicators:
- ✅ Completed
- ⏳ In Progress
- ❌ Failed (must be fixed before continuing)

---

**STATUS**: ✅ **RULE CREATED - IMPLEMENTING IMMEDIATELY**











