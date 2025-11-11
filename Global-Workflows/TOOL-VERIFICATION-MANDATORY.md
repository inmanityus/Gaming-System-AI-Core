# 🚨 MANDATORY: TOOL PATH VERIFICATION RULE

## ENFORCEMENT LEVEL: MAXIMUM - Zero Tolerance

**CRITICAL**: This rule MUST be followed for EVERY executable, script, or tool usage.

**PURPOSE**: Prevents session crashes from missing or incorrectly pathed tools.

**VIOLATION CONSEQUENCES**: Session crashes, data loss, wasted time, user frustration.

---

## THE RULE

### ⚠️ NEVER Execute a Tool Without Verification

**BEFORE** executing any tool, script, or executable, you **MUST**:

1. ✅ **Verify the tool exists** using `Test-Path` or the tool-paths.ps1 script
2. ✅ **Use the full path** to the tool (not just the command name)
3. ✅ **Handle failure gracefully** if the tool is not found

### ❌ VIOLATIONS (These Will Crash Sessions)

```powershell
# ❌ WRONG - No verification
python --version

# ❌ WRONG - Assumes Python is in PATH
python script.py

# ❌ WRONG - Uses Windows App Alias (wrong Python)
& "C:\Users\kento\AppData\Local\Microsoft\WindowsApps\python.exe"
```

### ✅ CORRECT USAGE

```powershell
# ✅ CORRECT - Load verified paths
$tools = & "Global-Scripts\tool-paths.ps1"

# ✅ CORRECT - Check before use
if ($tools.Python) {
    & $tools.Python --version
} else {
    Write-Error "Python not found! Cannot proceed."
    exit 1
}

# ✅ CORRECT - Use full path with error handling
if (Test-Path "C:\Users\kento\AppData\Local\Programs\Python\Python313\python.exe") {
    & "C:\Users\kento\AppData\Local\Programs\Python\Python313\python.exe" script.py
} else {
    Write-Error "Python 3.13 not found at expected location!"
    Write-Host "Expected: C:\Users\kento\AppData\Local\Programs\Python\Python313\python.exe"
    exit 1
}
```

---

## VERIFIED TOOL LOCATIONS

These are the **verified** tool locations for this system:

### Core Development Tools

| Tool | Verified Path |
|------|---------------|
| **Python 3.13** | `C:\Users\kento\AppData\Local\Programs\Python\Python313\python.exe` |
| **Pip** | `C:\Users\kento\AppData\Local\Programs\Python\Python313\Scripts\pip.exe` |
| **Node.js** | `C:\Program Files\nodejs\node.exe` |
| **NPM** | `C:\Program Files\nodejs\npm.cmd` |
| **Git** | `C:\Program Files\Git\cmd\git.exe` |
| **Docker** | `C:\Program Files\Docker\Docker\resources\bin\docker.exe` |
| **PowerShell 7** | `C:\Program Files\PowerShell\7\pwsh.exe` |

### Cloud & Infrastructure Tools

| Tool | Verified Path |
|------|---------------|
| **AWS CLI** | `C:\Program Files\Amazon\AWSCLIV2\aws.exe` |
| **kubectl** | `C:\Program Files\Docker\Docker\resources\bin\kubectl.exe` |
| **Terraform** | ⚠️ NOT INSTALLED (manual installation required) |

### Unreal Engine 5.6.1 Tools

| Tool | Verified Path |
|------|---------------|
| **Unreal Editor** | `C:\Program Files\Epic Games\UE_5.6\Engine\Binaries\Win64\UnrealEditor.exe` |
| **UnrealBuildTool** | `C:\Program Files\Epic Games\UE_5.6\Engine\Build\BatchFiles\Build.bat` |
| **UAT (Automation)** | `C:\Program Files\Epic Games\UE_5.6\Engine\Build\BatchFiles\RunUAT.bat` |
| **Version Selector** | `C:\Program Files\Epic Games\UE_5.6\Engine\Binaries\DotNET\UnrealVersionSelector\UnrealVersionSelector.exe` |

### Database Tools

| Tool | Verified Path |
|------|---------------|
| **psql (PostgreSQL)** | `C:\Program Files\PostgreSQL\16\bin\psql.exe` (if installed) |

---

## USING THE TOOL VERIFICATION SYSTEM

### Method 1: Load All Tool Paths

```powershell
# Load verified tool paths
$tools = & "Global-Scripts\tool-paths.ps1"

# Use with error handling
if ($tools.Python) {
    Write-Host "Using Python: $($tools.Python)"
    & $tools.Python --version
} else {
    Write-Error "Python not found!"
}

if ($tools.Node) {
    & $tools.Node --version
}

if ($tools.Docker) {
    & $tools.Docker --version
}
```

### Method 2: Show All Available Tools

```powershell
# Display all verified tools with status
& "Global-Scripts\tool-paths.ps1" -ShowAll

# Output:
# === TOOL PATH VERIFICATION RESULTS ===
# 
# ✅ Python
#    Path: C:\Users\kento\AppData\Local\Programs\Python\Python313\python.exe
# 
# ✅ Node
#    Path: C:\Program Files\nodejs\node.exe
# 
# ❌ Terraform
#    Status: NOT FOUND
```

### Method 3: Verbose Mode (Debug)

```powershell
# Show verification process details
$tools = & "Global-Scripts\tool-paths.ps1" -Verbose

# Output:
# [OK] Python found at: C:\Users\kento\AppData\Local\Programs\Python\Python313\python.exe
# [OK] Node found at: C:\Program Files\nodejs\node.exe
# [NOT FOUND] Terraform
```

---

## SPECIAL CASE: PYTHON

⚠️ **CRITICAL**: Python has a special verification requirement due to Windows App Aliases.

### The Problem

Windows creates app execution aliases in `WindowsApps` that redirect Python commands. These are **NOT** the real Python installation and may not work correctly.

**WRONG PATH** (Windows App Alias):
```
C:\Users\kento\AppData\Local\Microsoft\WindowsApps\python.exe
```

**CORRECT PATH** (Real Python 3.13):
```
C:\Users\kento\AppData\Local\Programs\Python\Python313\python.exe
```

### The Solution

**ALWAYS** use the tool-paths.ps1 script for Python, which automatically avoids the Windows App Alias:

```powershell
$tools = & "Global-Scripts\tool-paths.ps1"

if ($tools.Python) {
    # This will be the REAL Python, not the alias
    & $tools.Python script.py
} else {
    Write-Error "Python 3.13 not found!"
}
```

---

## STARTUP INTEGRATION

The tool verification system is integrated into `startup.ps1`:

1. **Loads tool paths at startup**
2. **Verifies critical tools are available**
3. **Warns if required tools are missing**
4. **Exports `$global:ToolPaths` for session use**

After startup completes, you can use:

```powershell
# Already loaded by startup.ps1
& $global:ToolPaths.Python --version
& $global:ToolPaths.Node --version
& $global:ToolPaths.Docker version
```

---

## ENFORCEMENT CHECKLIST

Before executing ANY command, verify:

- [ ] Is this an executable/script/tool?
- [ ] Have I verified it exists using `Test-Path` or `tool-paths.ps1`?
- [ ] Am I using the full path (not just command name)?
- [ ] Do I have error handling if the tool is not found?
- [ ] If it's Python, am I avoiding the Windows App Alias?

**If ANY checkbox is unchecked, DO NOT execute the command!**

---

## COMMON TOOL VERIFICATION PATTERNS

### Pattern: Python Script Execution

```powershell
$tools = & "Global-Scripts\tool-paths.ps1"

if (-not $tools.Python) {
    Write-Error "Python 3.13 required but not found!"
    Write-Host "Expected: C:\Users\kento\AppData\Local\Programs\Python\Python313\python.exe"
    exit 1
}

Write-Host "Using Python: $($tools.Python)"
& $tools.Python "path\to\script.py"
```

### Pattern: Node/NPM Commands

```powershell
$tools = & "Global-Scripts\tool-paths.ps1"

if (-not $tools.NPM) {
    Write-Error "NPM not found! Node.js installation required."
    exit 1
}

& $tools.NPM install
& $tools.Node server.js
```

### Pattern: Docker Commands

```powershell
$tools = & "Global-Scripts\tool-paths.ps1"

if (-not $tools.Docker) {
    Write-Error "Docker not found! Docker Desktop installation required."
    exit 1
}

& $tools.Docker ps
& $tools.Docker compose up -d
```

### Pattern: Unreal Engine Build

```powershell
$tools = & "Global-Scripts\tool-paths.ps1"

if (-not $tools.UnrealBuildTool) {
    Write-Error "Unreal Engine 5.6.1 not found!"
    Write-Host "Expected: C:\Program Files\Epic Games\UE_5.6\"
    exit 1
}

Write-Host "Building with: $($tools.UnrealBuildTool)"
& $tools.UnrealBuildTool Development Win64 -Project="path\to\project.uproject"
```

---

## AI SESSION REQUIREMENTS

**As an AI assistant, you MUST:**

1. ✅ **Load tool paths at the start of any workflow** that involves executables
2. ✅ **Verify before execute** - never assume a tool exists
3. ✅ **Use full paths** - never rely on PATH environment variable alone
4. ✅ **Handle failures gracefully** - always provide clear error messages
5. ✅ **Ask user for help** if a required tool is not found

**Example AI Workflow:**

```powershell
# Step 1: Load verified tools
Write-Host "Loading verified tool paths..."
$tools = & "Global-Scripts\tool-paths.ps1"

# Step 2: Verify required tools
$requiredTools = @("Python", "Node", "Docker")
$missingTools = @()

foreach ($tool in $requiredTools) {
    if (-not $tools[$tool]) {
        $missingTools += $tool
    }
}

# Step 3: Report and exit if missing
if ($missingTools.Count -gt 0) {
    Write-Error "Missing required tools: $($missingTools -join ', ')"
    Write-Host "Please install missing tools and run startup.ps1 again."
    exit 1
}

# Step 4: Proceed with verified tools
Write-Host "All required tools verified. Proceeding..."
& $tools.Python script.py
```

---

## MAINTENANCE

### Adding New Tools

To add a new tool to the verification system:

1. Edit `Global-Scripts\tool-paths.ps1`
2. Add the tool to `$KnownPaths` with possible locations
3. Update this documentation
4. Test verification with `-ShowAll` flag

### Updating Tool Paths

If a tool is installed in a different location:

1. Update the path in `Global-Scripts\tool-paths.ps1`
2. Add the new path to the list of possible locations
3. Keep old paths for backward compatibility
4. Test with `-Verbose` flag

---

## SUMMARY

✅ **ALWAYS verify tool locations before use**
✅ **ALWAYS use the tool-paths.ps1 script for reliability**
✅ **ALWAYS handle missing tools gracefully**
✅ **NEVER assume a tool is in PATH**
✅ **NEVER use Windows App Aliases (especially Python)**

**This rule prevents session crashes and saves time.**

---

**Last Updated**: 2025-11-07  
**Version**: 1.0.0  
**Enforcement Level**: MANDATORY - Zero Tolerance  
**Applies To**: ALL sessions, ALL tools, ALL executables

