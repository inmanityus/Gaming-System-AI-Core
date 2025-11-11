# Solution: KiCad 9.0 wxWidgets Initialization Error

**Issue ID**: kicad-9-wxwidgets-init-2025-11-06
**Date Solved**: 2025-11-06
**Project**: Drone Sentinels Comms System - PCB Automation
**Severity**: Critical
**Technology**: KiCad 9.0.6, Python, wxWidgets

## Problem Statement

When using KiCad 9.0 Python API (`pcbnew`), scripts crashed with error:
```
C:\vcpkg\buildtrees\wxwidgets\src\v3.2.8-5c787d20fc.clean\src\common\stdpbase.cpp(59): 
assert "traits" failed in wxStandardPathsBase::Get(): create wxApp before calling this
```

**Root Cause**: KiCad's Python API relies on wxWidgets internally, and `wx.App` must be initialized before importing `pcbnew` or using any KiCad API functions that internally use wxWidgets (like `wxPoint`).

## Root Cause

KiCad 9.0's Python API (`pcbnew`) has internal dependencies on wxWidgets. Even in headless (non-GUI) operations, wxWidgets must be initialized because many KiCad API functions internally use wxWidgets classes and functions.

The error occurs because:
1. Script imports `pcbnew` without initializing wxWidgets
2. KiCad API internally calls wxWidgets functions (like `wxStandardPathsBase::Get()`)
3. wxWidgets requires `wx.App` to be created before use
4. Assertion fails when wxWidgets functions are called without `wx.App` initialization

## Solution

**CRITICAL**: Always initialize wxWidgets BEFORE importing pcbnew.

### Implementation

```python
import sys
import os

# CRITICAL: Initialize wxWidgets BEFORE importing pcbnew
wx_app = None
try:
    import wx
    # Initialize wxApp for headless operation (no GUI)
    # Must be done before importing pcbnew
    if not wx.GetApp():
        wx_app = wx.App(False)  # False = don't redirect stdout/stderr
        sys.stdout.write("[OK] wxWidgets initialized for headless operation\n")
        sys.stdout.flush()
except ImportError:
    # wxPython not available, but might still work if KiCad handles it
    sys.stderr.write("[WARNING] wxPython not found, continuing anyway...\n")
    sys.stderr.flush()
except Exception as e:
    sys.stderr.write(f"[WARNING] wxWidgets initialization warning: {e}\n")
    sys.stderr.flush()

# NOW safe to import pcbnew
import pcbnew
```

### Key Points

1. **Order Matters**: wxWidgets initialization MUST happen before `import pcbnew`
2. **Headless Operation**: Use `wx.App(False)` - the `False` parameter prevents stdout/stderr redirection
3. **Error Handling**: Wrap in try-except to handle cases where wxPython might not be available
4. **Check Existing**: Use `wx.GetApp()` to check if wxApp already exists (prevents duplicate initialization)

## Prevention

**Pattern**: Always include wxWidgets initialization at the very beginning of any Python script that uses KiCad's `pcbnew` API.

**Template**:
```python
# Always start KiCad Python scripts with:
# 1. wxWidgets initialization
# 2. KiCad Python path setup
# 3. Then import pcbnew
```

## Related Issues

- KiCad 9.0 API changes (VECTOR2I, FOOTPRINT)
- Session crashes due to context window overflow
- Output limiting patterns

## Testing

Verified on:
- KiCad 9.0.6
- Windows 10/11
- Python 3.11 (KiCad bundled)

## Status

✅ **SOLVED** - This solution resolves the wxWidgets initialization error completely.

