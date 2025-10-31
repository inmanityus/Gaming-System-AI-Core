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

### **5. session-rules-enforcement.ps1** ⭐ **NEW**
- Enforces /all-rules compliance (timer, milestones, visibility)
- Function: `Initialize-SessionRulesEnforcement`
- Created: 2025-01-29

### **6. timer-service.ps1**
- Starts timer service to prevent session traps
- Function: `Initialize-TimerService`

### **7. timer-verification.ps1** ⭐ **NEW**
- Verifies timer service is running and accessible
- Function: `Initialize-TimerVerification`
- Created: 2025-01-29

---

## 🔄 **LOAD ORDER**

Current alphabetical order:
1. documentation-placement
2. memory-structure
3. minimum-model-levels
4. resource-management
5. session-rules-enforcement ⭐
6. timer-service
7. timer-verification ⭐

**Critical Sequence**: 
- Timer Service starts first
- Timer Verification checks it next
- Session Rules enforce compliance

---

## 🎯 **NEW FEATURES** (2025-01-29)

### **timer-verification.ps1**
**Purpose**: Verify timer service is actually running

**Checks**:
- Background job `CursorTimerService` is running
- Marker file `.cursor/timer-service.running` exists and is recent
- Sets `$env:CURSOR_TIMER_VERIFIED = "true"` if verified

**Requires**: timer-service.ps1 to run first

### **session-rules-enforcement.ps1**
**Purpose**: Enforce /all-rules compliance

**Functions**:
- Creates rules compliance tracker
- Sets environment variables for enforcement
- Reminds AI to format responses with timer/milestone/visibility
- Tracks compliance across session

**Dependencies**: 
- Should run after timer-verification
- Sets enforcement flags for /all-rules compliance

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
