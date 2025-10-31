# Deployment Runbook - Model Management System
**Date**: 2025-01-29  
**Status**: Production Ready ✅

---

## 🚀 **PRE-DEPLOYMENT CHECKLIST**

### **Environment Setup**
- [ ] PostgreSQL database running (port 5443)
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] Model Registry initialized
- [ ] Services configured

### **Validation**
- [ ] All tests passing (34/34)
- [ ] Production readiness script passed
- [ ] Health checks configured
- [ ] Monitoring enabled

---

## 📋 **DEPLOYMENT PROCEDURE**

### **Step 1: Database Preparation** (5 min)

```bash
# Connect to database
psql -h localhost -p 5443 -U postgres -d gaming_system

# Verify tables exist
\dt model_registry
\dt model_historical_logs
\dt model_deployments
```

**Success Criteria**: All tables exist and accessible

### **Step 2: Environment Configuration** (5 min)

```bash
# Set environment variables
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5443
export POSTGRES_DB=gaming_system
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=your_password

# Verify configuration
python scripts/validate-production-readiness.py
```

**Success Criteria**: All checks pass

### **Step 3: Service Initialization** (10 min)

```python
# Initialize Model Registry
from services.model_management.model_registry import ModelRegistry

registry = ModelRegistry()

# Register initial models
foundation_id = await registry.register_model(
    model_name="foundation-model-v1",
    model_type="self_hosted",
    provider="ollama",
    use_case="foundation_layer",
    version="1.0",
    configuration={"endpoint": "http://localhost:8001/generate"}
)
await registry.update_model_status(foundation_id, "current")
```

**Success Criteria**: Models registered and set to "current"

### **Step 4: Integration Verification** (10 min)

```python
# Test AI Inference integration
from services.ai_integration.llm_client import LLMClient

client = LLMClient(model_registry=registry)
result = await client.generate_text(
    layer="foundation",
    prompt="Test prompt",
    context={}
)
assert result["success"] is True
```

**Success Criteria**: All integrations working

### **Step 5: Health Checks** (5 min)

```bash
# Run health checks
python -m pytest services/model_management/tests/test_model_registry.py -v
python scripts/validate-production-readiness.py
```

**Success Criteria**: All checks pass

---

## 🔄 **ROLLBACK PROCEDURE**

### **If Deployment Fails**

1. **Stop New Services** (2 min)
```bash
# Stop all services using new model
# Services will fallback to hardcoded endpoints
```

2. **Revert Model Status** (3 min)
```python
# Revert model status in registry
await registry.update_model_status(new_model_id, "archived")
await registry.update_model_status(old_model_id, "current")
```

3. **Verify Rollback** (5 min)
```python
# Verify old model is active
current_model = await registry.get_current_model("foundation_layer")
assert current_model["model_id"] == old_model_id
```

**Total Rollback Time**: < 10 minutes

---

## 🔍 **HEALTH CHECK PROCEDURES**

### **Daily Health Checks**

1. **Model Registry Health**
```python
model = await registry.get_current_model("foundation_layer")
assert model is not None
```

2. **Historical Logging Health**
```python
log_id = await processor.log_inference(
    model_id=uuid4(),
    use_case="health_check",
    prompt="Health check",
    context={},
    generated_output="OK"
)
assert log_id is not None
```

3. **Guardrails Health**
```python
result = await monitor.monitor_outputs(
    model_id="test",
    outputs=["Safe test content"]
)
assert result["compliant"] is True
```

### **Weekly Reviews**

- Review guardrails violations
- Analyze historical logs
- Check deployment success rates
- Review performance metrics

---

## 🚨 **TROUBLESHOOTING GUIDE**

### **Issue 1: Model Registry Unavailable**

**Symptoms**: Services fallback to hardcoded endpoints
**Diagnosis**: Check database connectivity
```bash
psql -h localhost -p 5443 -U postgres -d gaming_system
```

**Resolution**: Restore database connectivity
**Impact**: Low - services continue with fallback

### **Issue 2: Historical Logging Failures**

**Symptoms**: Operations succeed but no logs created
**Diagnosis**: Check database write permissions
**Resolution**: Fix database permissions or connection
**Impact**: Low - operations continue, logs lost

### **Issue 3: Guardrails Violations**

**Symptoms**: Fallback content returned frequently
**Diagnosis**: Check violation logs, review content
**Resolution**: Update model or adjust guardrails thresholds
**Impact**: Medium - content quality affected

### **Issue 4: Deployment Failures**

**Symptoms**: New model not deployed
**Diagnosis**: Check deployment logs
**Resolution**: Rollback, investigate, retry
**Impact**: High - system stays on old model

---

## 📊 **MONITORING CHECKLIST**

### **Metrics to Monitor**

- [ ] Model Registry lookup latency (< 100ms)
- [ ] Historical logging success rate (> 95%)
- [ ] Guardrails violation rate (< 1%)
- [ ] Deployment success rate (> 90%)
- [ ] System response times

### **Alerts to Configure**

- [ ] Registry unavailable > 30 seconds
- [ ] Logging failure rate > 5%
- [ ] Critical guardrails violations
- [ ] Deployment failures
- [ ] Performance degradation

---

## ✅ **POST-DEPLOYMENT VALIDATION**

### **Immediate Checks** (15 min)

- [ ] All services running
- [ ] All integrations working
- [ ] Health checks passing
- [ ] Monitoring active
- [ ] No errors in logs

### **24-Hour Review**

- [ ] Review all metrics
- [ ] Check for issues
- [ ] Validate performance
- [ ] Review guardrails violations

---

## 📝 **DEPLOYMENT NOTES**

- All integrations are backward compatible
- Services work standalone or integrated
- Failures gracefully degrade (no system outages)
- Logging is non-blocking (performance maintained)

---

**Status**: ✅ **DEPLOYMENT READY - FOLLOW PROCEDURES ABOVE**

