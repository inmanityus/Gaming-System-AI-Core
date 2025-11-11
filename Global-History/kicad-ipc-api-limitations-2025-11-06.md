# Solution: KiCad 9.0 IPC API Limitations for Board Operations

**Issue ID**: kicad-ipc-api-limitations-2025-11-06
**Date Solved**: 2025-11-06
**Project**: Drone Sentinels Comms System - PCB Automation
**Severity**: Medium
**Technology**: KiCad 9.0.6, IPC API, kipy

## Problem Statement

Attempted to use KiCad 9.0 IPC API (`kicad-python` package, imports as `kipy`) for PCB board automation. Connection works, but board operations fail with:

```
KiCad returned error: no handler available for request of type kiapi.common.commands.GetOpenDocuments
```

**Root Cause**: KiCad 9.0.6's IPC API server doesn't have handlers registered for board operations (`GetOpenDocuments`, `get_board()`). The IPC API currently supports:
- ✅ Connection/ping
- ✅ Version retrieval
- ❌ Board operations (not implemented)

## Root Cause

The IPC API in KiCad 9.0.6 is a newer feature and doesn't yet support all board operations. The IPC API server connects successfully, but the handlers for board-related operations are not implemented or registered in the current version.

**Error Details**:
- `kipy.KiCad().ping()` works ✅
- `kipy.KiCad().get_version()` works ✅
- `kipy.KiCad().get_board()` fails ❌
- `kipy.KiCad().get_open_documents()` fails ❌

## Solution

**Use SWIG-based Python API instead of IPC API for board operations.**

### Implementation

**DO NOT USE** (IPC API - doesn't work for boards):
```python
import kipy
kicad = kipy.KiCad()
board = kicad.get_board()  # FAILS - no handler available
```

**USE INSTEAD** (SWIG-based API - works):
```python
import pcbnew
board = pcbnew.LoadBoard("board.kicad_pcb")  # WORKS
```

### When to Use Each API

**IPC API** (`kipy`) - Use for:
- Connection testing
- Version checking
- Future features (when board operations are added)

**SWIG-based API** (`pcbnew`) - Use for:
- ✅ Board loading/saving
- ✅ Component placement
- ✅ Footprint creation
- ✅ Via creation
- ✅ All board manipulation

### Migration Path

1. **Current**: Use SWIG-based API (`pcbnew`) for all board operations
2. **Monitor**: Watch for KiCad IPC API updates that add board operation support
3. **Future**: Migrate to IPC API when board operations are implemented

## Prevention

**Pattern**: For KiCad 9.0.6, always use SWIG-based Python API (`pcbnew`) for board automation. IPC API is not yet ready for board operations.

**Checklist**:
- [ ] Use `pcbnew.LoadBoard()` instead of `kipy.get_board()`
- [ ] Use `pcbnew.FOOTPRINT()` for footprint operations
- [ ] Use SWIG API for all board manipulation
- [ ] Reserve IPC API for connection/version checks only

## Related Issues

- KiCad 9.0 API changes
- wxWidgets initialization requirements
- Output limiting patterns

## Testing

Verified on:
- KiCad 9.0.6
- Windows 10/11
- Python 3.11 (KiCad bundled)
- IPC API connection: ✅ Works
- IPC API board operations: ❌ Not supported

## Status

✅ **DOCUMENTED** - IPC API limitations identified. SWIG-based API is the working solution for board operations.

**Note**: This is a limitation of KiCad 9.0.6, not a bug. Future KiCad versions may add board operation support to IPC API.

