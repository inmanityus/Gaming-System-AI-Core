# 🧪 Load Testing Suite

**Purpose**: Validate system scales from 100 → 10,000 NPCs gracefully

**Status**: Infrastructure complete, ready to execute when production endpoint available

---

## 📋 Test Scenarios

### Scenario 1: Baseline (100 NPCs)
- **NPCs**: 100 concurrent
- **Duration**: 10 minutes
- **Ramp-up**: 1 minute
- **Target Latency**: P95 <150ms
- **Purpose**: Establish baseline performance

### Scenario 2: Medium Scale (1,000 NPCs)
- **NPCs**: 1,000 concurrent
- **Duration**: 15 minutes
- **Ramp-up**: 3 minutes
- **Target Latency**: P95 <200ms
- **Purpose**: Validate 10x scaling

### Scenario 3: High Scale (10,000 NPCs)
- **NPCs**: 10,000 concurrent
- **Duration**: 20 minutes
- **Ramp-up**: 10 minutes
- **Target Latency**: P95 <500ms
- **Purpose**: Validate maximum capacity

### Scenario 4: Spike Test
- **Pattern**: 100 → 5,000 NPCs in 5 minutes
- **Duration**: 10 minutes total
- **Target**: Auto-scaling responds <5 minutes
- **Purpose**: Validate rapid scale-up

### Scenario 5: Sustained Load
- **NPCs**: 1,000 concurrent
- **Duration**: 4 hours
- **Target**: No degradation, no memory leaks
- **Purpose**: Validate stability

### Scenario 6: Failure Recovery (Manual)
- **Pattern**: Kill GPU instances during Scenario 2
- **Target**: Recovery <5 minutes
- **Purpose**: Validate graceful degradation

---

## 🚀 Usage

### Prerequisites:
```bash
pip install -r requirements.txt
```

### Run Single Scenario:
```bash
python npc_load_generator.py baseline
python npc_load_generator.py medium
python npc_load_generator.py high
python npc_load_generator.py spike
python npc_load_generator.py sustained
```

### Run All Scenarios:
```powershell
pwsh -File run_all_scenarios.ps1
```

---

## 📊 Success Criteria

### Performance:
- **Scenario 1 (100 NPCs)**: P95 <150ms, errors <1%
- **Scenario 2 (1K NPCs)**: P95 <200ms, errors <1%
- **Scenario 3 (10K NPCs)**: P95 <500ms, errors <2%
- **Scenario 4 (Spike)**: Scale-up <5 minutes, P95 <250ms after stabilization
- **Scenario 5 (Sustained)**: No degradation, memory stable, errors <0.5%

### Auto-Scaling:
- Gold ASG scales 1 → 50 instances smoothly
- Silver ASG scales 1 → 30 instances smoothly
- No thrashing (scale up/down cycles)
- Spot instances launch successfully

### Stability:
- No service crashes
- No database connection exhaustion
- No memory leaks (4-hour test)
- Graceful recovery from instance failures

---

## 📁 Files

- `npc_load_generator.py` - Core load generator
- `metrics_collector.py` - Collects CloudWatch metrics during test
- `analyze_results.py` - Post-test analysis and graphing
- `run_all_scenarios.ps1` - Runs all scenarios sequentially
- `requirements.txt` - Python dependencies

---

## ⚠️ Important Notes

### Endpoint Configuration:
**UPDATE BEFORE RUNNING**: Load generator currently points to `http://localhost:8080`

Update endpoint in:
- `npc_load_generator.py` line 111 (LoadTestOrchestrator endpoint)
- Or pass as environment variable: `LOAD_TEST_ENDPOINT`

### Cost Warning:
High-scale scenarios (10,000 NPCs) will trigger maximum auto-scaling:
- Gold ASG: Up to 50 instances = $60/hour
- Silver ASG: Up to 30 instances = $45/hour
- **Total**: ~$105/hour at peak

Scenarios 1-2 are safe (<$10/hour)

### Prerequisites:
1. ✅ Auto-scaling configured and operational
2. ✅ GPU instances available
3. ✅ Monitoring dashboards deployed
4. ❓ Production NPC endpoint available

---

**Status**: ✅ Infrastructure Complete  
**Next**: Execute when production endpoint ready  
**Created**: 2025-11-09

