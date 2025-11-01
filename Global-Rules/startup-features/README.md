# Startup Features - Modular Architecture
**Purpose**: Extensible startup system for all Cursor projects  
**Location**: `Global-Workflows/startup-features/` (shared across projects)

---

## 📋 **CURRENT FEATURES**

Features load in alphabetical order. To enforce specific order, prefix filenames (e.g., `01-feature.ps1`).

### **1. documentation-placement.ps1**
- Verifies documentation is properly organized
- Function: `Initialize-DocumentationPlacement`

### **2. memory-structure.ps1**
- Creates and manages AI session memory structure
- Function: `Initialize-MemoryStructure`

### **3. minimum-model-levels.ps1**
- Loads and enforces minimum AI model requirements
- Function: `Initialize-MinimumModelLevels`

### **4. resource-management.ps1**
- Initializes resource management tools and health monitoring
- Function: `Initialize-ResourceManagement`

### **5. session-monitor.ps1** ⭐ **NEW - UPDATED**
- Continuous background monitoring of /all-rules compliance
- Function: `Initialize-SessionMonitor`
- Designed via three-model collaboration (Claude 3.5, GPT-4o, GPT-4 Turbo)
- Created: 2025-01-29

### **6. timer-service.ps1**
- Starts timer service to prevent session traps
- Function: `Initialize-TimerService`

### **7. work-visibility-enforcement.ps1** ⭐ **NEW**
- Enforces real-time command display requirement
- Function: `Initialize-WorkVisibilityEnforcement`
- **Critical**: Ensures ALL commands and results shown in session window (not just file summaries)
- Reference: `Global-History/work-visibility-real-time.md`

---

## 🔄 **LOAD ORDER**

Current alphabetical order:
1. documentation-placement
2. memory-structure
3. minimum-model-levels
4. resource-management
5. **session-monitor** ⭐ (continuous monitoring)
6. timer-service

**Critical Sequence**: 
- Timer Service starts first
- Session Monitor verifies it and continues monitoring

---

## 🎯 **NEW FEATURE: session-monitor.ps1** ⭐ **RECENTLY UPDATED**

### **Purpose**: Continuous Oversight Throughout Entire Session

**What It Does**:
- Runs continuously as background job
- Checks /all-rules compliance every 60 seconds
- Monitors: timer, peer coding, pairwise testing, milestones, visibility, memory, testing, continuity
- Writes status file: `.cursor/monitor/status.json`
- Logs violations: `.cursor/logs/session-monitor.jsonl`

**Design**:
- Based on timer-service background job pattern
- Lightweight (60s intervals, minimal resource usage)
- Auto-remediation (restarts dead timer if detected)
- Non-intrusive (never interrupts workflow)

**Why Three-Model Collaboration**:
- **Claude 3.5**: Background job architecture (lightweight)
- **GPT-4o**: Robust monitoring with auto-remediation
- **GPT-4 Turbo**: Hybrid approach balancing efficiency

**Benefits**:
- ✅ Continuous monitoring (not just startup check)
- ✅ Early violation detection
- ✅ Auto-remediation of simple issues
- ✅ Session stability and quality
- ✅ Lightweight, no burden
- ✅ Reduces overhead on sessions

---

## 📝 **ADDING NEW FEATURES**

### **Quick Start**

1. Create `.ps1` file in `Global-Workflows/startup-features/`
2. Use kebab-case: `my-new-feature.ps1`
3. Define function: `function Initialize-MyNewFeature { ... }`
4. File auto-loads on next startup!

### **Example**

```powershell
# my-new-feature.ps1
function Initialize-MyNewFeature {
    Write-Host "[MYFEATURE] Initializing..." -ForegroundColor Cyan
    
    # Your code here
    if (Test-Path "some-file.txt") {
        Write-Host "[OK] MyNewFeature ready" -ForegroundColor Green
    }
}
```

**Naming Convention**:
- File: `my-new-feature.ps1` (kebab-case)
- Function: `Initialize-MyNewFeature` (PascalCase)

---

## 🎯 **BEST PRACTICES**

- ✅ **Error Handling**: Use try/catch blocks
- ✅ **Status Messages**: Provide clear feedback
- ✅ **Idempotency**: Safe to run multiple times
- ✅ **Dependencies**: Check requirements first
- ✅ **Documentation**: Comment complex logic
- ✅ **Lightweight**: Minimize resource usage
- ✅ **Background Jobs**: For continuous monitoring

---

## 🔗 **USAGE**

Features load automatically when `startup.ps1` runs.

**In startup.ps1**:
```powershell
# Loads all .ps1 files from Global-Workflows/startup-features/
# Calls Initialize-* functions automatically
```

**Manual Loading**:
```powershell
. "Global-Workflows/startup-features/my-feature.ps1"
Initialize-MyFeature
```

---

**Status**: ✅ All features documented and ready for use
