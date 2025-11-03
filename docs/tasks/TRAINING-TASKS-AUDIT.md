# Training Tasks Audit - SRL→RLVR Replacement Plan
**Date**: 2025-01-29  
**Status**: Audit Complete - Replacement Plan Defined  
**Purpose**: Identify all existing training/fine-tuning tasks that must be REPLACED with SRL→RLVR approach

---

## 🚨 CRITICAL FINDINGS

**ALL existing training/fine-tuning tasks must be REPLACED or DEPRECATED.**

**NO exceptions. NO partial replacements. Complete replacement required.**

---

## TASKS TO DEPRECATE & REPLACE

### 1. MODEL-MANAGEMENT-TASKS.md

#### Task 7.4: Historical Log Processing & Training Data Preparation
**Status**: ❌ **DEPRECATED - REPLACE WITH SRL→RLVR**  
**Reason**: Old approach uses static historical logs. SRL→RLVR uses dynamic example generation with three-model collaboration.

**Replacement**: 
- See: `SRL-RLVR-TRAINING-TASKS.md` → Tasks COLLAB-001..003, DYN-001
- New approach: Three-model collaboration generates expert trajectories dynamically
- Never static: Dynamic example generation continuously improves

**Action**: 
- Mark task as DEPRECATED
- Add note: "REPLACED BY SRL→RLVR - See SRL-RLVR-TRAINING-TASKS.md"

---

#### Task 7.5: Fine-Tuning Pipeline with Historical Data
**Status**: ❌ **DEPRECATED - REPLACE WITH SRL→RLVR**  
**Reason**: Old approach uses basic fine-tuning. SRL→RLVR uses SRL pretraining → RLVR fine-tuning with step-wise rewards.

**Replacement**:
- See: `SRL-RLVR-TRAINING-TASKS.md` → Tasks SRL-001, RLVR-001, MODEL-*-001
- New approach: SRL (step-wise supervised rewards) → RLVR (outcome-based rewards)
- Covers all 7 model types with specific training strategies

**Action**:
- Mark task as DEPRECATED
- Add note: "REPLACED BY SRL→RLVR - See SRL-RLVR-TRAINING-TASKS.md"

---

#### Task 7.6: Testing & Validation Framework
**Status**: ⚠️ **ENHANCE - INTEGRATE WITH SRL→RLVR**  
**Reason**: Testing framework is still needed but must integrate SRL→RLVR requirements.

**Enhancements Required**:
- Add SRL→RLVR-specific tests
- Add dynamic example generation validation
- Add three-model collaboration tests
- Add model type-specific evaluation metrics
- Integrate with RLVR evaluation suite

**Action**:
- Keep task but enhance with SRL→RLVR requirements
- See: `SRL-RLVR-TRAINING-TASKS.md` → Tasks RLVR-002, TEST-001

---

### 2. AI-INFERENCE-TASKS.md

#### AI-003: LoRA Adapter System
**Status**: ✅ **KEEP - BUT UPDATE TO USE SRL→RLVR TRAINED LORAs**  
**Reason**: LoRA system is still needed for serving, but adapters must be trained via SRL→RLVR.

**Updates Required**:
- LoRA adapters must come from SRL→RLVR training pipeline
- Integration with Model Management System for adapter registration
- Hot-swap functionality for SRL→RLVR trained adapters

**Action**:
- Keep task but update description to reference SRL→RLVR training
- Add dependency on SRL→RLVR training pipeline

---

#### AI-004: Multi-Tier Model Serving
**Status**: ✅ **KEEP - BUT UPDATE FOR DYNAMIC MODEL SELECTION**  
**Reason**: Multi-tier serving still needed, but selection must use dynamic model selection system.

**Updates Required**:
- Model selection must use Dynamic Model Selection System (DYN-003)
- Cost-benefit analysis integrated
- Not arbitrary - responsibility-based selection

**Action**:
- Keep task but update to integrate with Dynamic Model Selection
- See: `SRL-RLVR-TRAINING-TASKS.md` → Task DYN-003

---

### 3. OTHER TASK FILES

**Review Required**: Check all task files for any mention of:
- "fine-tune" / "fine-tuning"
- "training" / "train"
- "LoRA" / "adapter" (if referring to training)
- "historical logs" / "historical data"

**Action**: 
- Audit each file individually
- Mark deprecated tasks
- Update tasks that reference training

---

## REPLACEMENT MAPPING

### Old Approach → New SRL→RLVR Approach

| Old Task | New SRL→RLVR Tasks | Notes |
|----------|-------------------|-------|
| MODEL-MGMT 7.4: Historical Log Processing | COLLAB-001..003, DYN-001 | Dynamic example generation replaces static logs |
| MODEL-MGMT 7.5: Fine-Tuning Pipeline | SRL-001, RLVR-001, MODEL-*-001 | SRL→RLVR replaces basic fine-tuning |
| MODEL-MGMT 7.6: Testing Framework | RLVR-002, TEST-001 | Enhanced with SRL→RLVR requirements |
| Any "fine-tune model X" | MODEL-X-001 (SRL→RLVR) | Each model type has specific SRL→RLVR task |

---

## MIGRATION PLAN

### Step 1: Deprecate Old Tasks (Immediate)
- Add DEPRECATED markers to tasks 7.4, 7.5
- Add cross-references to new SRL→RLVR tasks
- Document why replaced

### Step 2: Update Related Tasks (Week 1)
- Update AI-003 to reference SRL→RLVR trained LoRAs
- Update AI-004 to reference Dynamic Model Selection
- Review all other tasks for training references

### Step 3: Implement SRL→RLVR (Weeks 25-32)
- Follow Phase 5 build order in GLOBAL-MANAGER-SRL-RLVR.md
- All training uses SRL→RLVR approach
- Old training tasks completely replaced

### Step 4: Remove Old Tasks (After SRL→RLVR Proven)
- After 2 evaluation cycles with no regressions
- Archive old tasks (don't delete - keep for history)
- Update all documentation

---

## VALIDATION CHECKLIST

Before considering SRL→RLVR complete:
- [ ] All old training tasks marked DEPRECATED
- [ ] All new SRL→RLVR tasks implemented
- [ ] All 7 model types successfully trained via SRL→RLVR
- [ ] Dynamic example generation functional (never static)
- [ ] Dynamic model selection functional (not arbitrary)
- [ ] Paid fine-tuning functional (Gemini, ChatGPT, Anthropic)
- [ ] Performance tracking functional (weakness detection)
- [ ] Integration with existing systems validated
- [ ] All tests passing
- [ ] Documentation updated

---

## NOTES

**Important**: 
- Old tasks remain in files for historical reference
- New implementation must completely replace old approach
- No hybrid approach - full SRL→RLVR only
- All model training must go through SRL→RLVR pipeline

**Exception**:
- If models were already "trained" using old approach, they must be scrapped and re-trained with SRL→RLVR
- No exceptions - quality requires proper training

---

**STATUS**: ✅ Audit Complete - Replacement Plan Defined

**Next Action**: Begin Phase 0 (Foundation) implementation per GLOBAL-MANAGER-SRL-RLVR.md

