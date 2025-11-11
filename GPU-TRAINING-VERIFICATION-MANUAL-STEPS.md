# GPU Training Verification - Manual Steps Required

**Instance**: i-0da704b9c213c0839 @ 54.147.14.199  
**Status**: Running  
**Issue**: SSM commands not returning output  
**Resolution**: Manual SSH verification required

---

## Manual Verification Steps

### 1. SSH to Instance

```bash
# From local machine with SSH key
ssh -i "docs/inventory/auth/gaming-system-ai-core-admin.pem" ubuntu@54.147.14.199
```

### 2. Check Training Directory

```bash
cd /home/ubuntu/training

# Check if directory exists
ls -la

# Check adapter count
ls adapters/vampire/ 2>/dev/null | wc -l
ls adapters/zombie/ 2>/dev/null | wc -l

# Expected: 14 adapters total (7 vampire + 7 zombie)
```

### 3. Check Training Process

```bash
# Check if training is running
ps aux | grep train_lora | grep -v grep

# Check training log
tail -50 training.log
```

### 4. Check GPU Status

```bash
# NVIDIA status
nvidia-smi

# Expected: NVIDIA A10G, 24GB, driver 550.144.03
```

### 5. Check Training Queue

```bash
# View training queue status
cat training_queue.json | python3 -m json.tool | head -50
```

---

## Expected State

### If Training Complete:
- 14 adapter files in `adapters/` directory
- 7 files in `adapters/vampire/`
- 7 files in `adapters/zombie/`
- No `train_lora` processes running
- training.log shows "Training complete"
- Inspector validation reports exist

### If Training In Progress:
- `train_lora_adapter.py` process running
- GPU utilization > 80%
- training.log shows recent progress
- Some adapters completed, others pending

### If Training Failed:
- No process running
- training.log shows errors
- Incomplete adapters
- CUDA errors or OOM messages

---

## Actions Based on State

### If Complete:
1. Run Inspector AI validation:
   ```bash
   cd /home/ubuntu/training
   python3 test_inspector.py
   ```

2. Copy validation reports:
   ```bash
   # Reports should be in inspector_reports/
   ls -la inspector_reports/
   ```

3. Download adapters for deployment:
   ```bash
   # From local machine
   scp -i "docs/inventory/auth/gaming-system-ai-core-admin.pem" \
       -r ubuntu@54.147.14.199:/home/ubuntu/training/adapters/ \
       ./trained-adapters/
   ```

### If In Progress:
1. Monitor progress periodically
2. Check logs for errors
3. Wait for completion

### If Failed:
1. Check error logs:
   ```bash
   tail -200 training.log | grep -i error
   ```

2. Check CUDA/GPU errors:
   ```bash
   dmesg | grep -i cuda
   nvidia-smi --query-gpu=temperature.gpu,power.draw --format=csv
   ```

3. Restart training if needed:
   ```bash
   cd /home/ubuntu/training
   nohup python3 train_lora_adapter.py --mode queue > training.log 2>&1 &
   ```

---

## Alternative: Redeploy Training

If manual verification is not feasible, redeploy training with improved logging:

```powershell
# From local machine
.\scripts\deploy-and-monitor-training.ps1 -InstanceId i-0da704b9c213c0839
```

---

## Why SSM Not Working

SSM commands appear to execute but return no output. Possible causes:
1. SSM agent misconfiguration
2. Shell environment issues
3. AWS SSM service issues
4. Command timeout before output returned

SSH is more reliable for interactive verification.

---

## Next Steps After Verification

1. **If adapters trained**: Run Inspector AI validation
2. **If validation passes**: Deploy adapters to production
3. **If validation fails**: Review Inspector reports and fix issues
4. **If training failed**: Debug and restart

---

**Created**: 2025-11-10  
**Status**: Awaiting manual verification  
**Priority**: Medium (training is automated, verification is validation only)

