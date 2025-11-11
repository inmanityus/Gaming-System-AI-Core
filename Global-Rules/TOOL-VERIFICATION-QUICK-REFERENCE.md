# 🚀 Tool Verification - Quick Reference for AI Sessions

## MANDATORY: Verify Before Execute

**NEVER run a tool without verification!**

---

## Quick Start (Method 1 - Use Global Variable)

After startup, tools are already loaded in `$global:ToolPaths`:

```powershell
# Python
if ($global:ToolPaths.Python) {
    & $global:ToolPaths.Python script.py
} else {
    Write-Error "Python not found!"
}

# Node
if ($global:ToolPaths.Node) {
    & $global:ToolPaths.Node app.js
}

# Docker
if ($global:ToolPaths.Docker) {
    & $global:ToolPaths.Docker ps
}
```

---

## Quick Start (Method 2 - Helper Function)

Use the helper function for quick verification:

```powershell
# Verify and get path
$pythonPath = & "Global-Scripts\verify-tool.ps1" -Tool Python -ShowPath

if ($pythonPath) {
    & $pythonPath script.py
}

# Require or exit (exits if not found)
$nodePath = & "Global-Scripts\verify-tool.ps1" -Tool Node -RequireOrExit
& $nodePath app.js
```

---

## Quick Start (Method 3 - Direct Check)

For one-off checks:

```powershell
if (Test-Path "C:\Users\kento\AppData\Local\Programs\Python\Python313\python.exe") {
    & "C:\Users\kento\AppData\Local\Programs\Python\Python313\python.exe" script.py
} else {
    Write-Error "Python 3.13 not found!"
}
```

---

## Common Tool Paths

| Tool | Verified Path |
|------|---------------|
| Python 3.13 | `C:\Users\kento\AppData\Local\Programs\Python\Python313\python.exe` |
| Node.js | `C:\Program Files\nodejs\node.exe` |
| NPM | `C:\Program Files\nodejs\npm.cmd` |
| Docker | `C:\Program Files\Docker\Docker\resources\bin\docker.exe` |
| Git | `C:\Program Files\Git\cmd\git.exe` |
| AWS CLI | `C:\Program Files\Amazon\AWSCLIV2\aws.exe` |
| UE5 Editor | `C:\Program Files\Epic Games\UE_5.6\Engine\Binaries\Win64\UnrealEditor.exe` |
| UE5 Build Tool | `C:\Program Files\Epic Games\UE_5.6\Engine\Build\BatchFiles\Build.bat` |

---

## AI Session Checklist

Before executing ANY command with a tool:

1. ✅ Is the tool path verified?
2. ✅ Am I using the full path or `$global:ToolPaths`?
3. ✅ Do I have error handling if tool is missing?
4. ✅ For Python, am I avoiding Windows App Alias?

---

## Full Documentation

See: `Global-Rules/TOOL-VERIFICATION-MANDATORY.md`

