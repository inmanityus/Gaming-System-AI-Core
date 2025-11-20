# KiCad 9.0 Footprint Loading Guide

**Version**: 1.0  
**Last Updated**: 2025-11-06  
**KiCad Version**: 9.0.6+  
**Python Version**: 3.11 (KiCad bundled)

## Overview

This guide explains how to load real footprints from KiCad 9.0 libraries using Python automation. KiCad 9.0 changed the footprint loading API from version 8.x, requiring a different approach.

## Prerequisites

- KiCad 9.0.6 or later installed
- Python 3.11 (bundled with KiCad)
- wxWidgets initialized (required for pcbnew)

## Key API Changes in KiCad 9.0

### What Changed

- ❌ `PCB_IO()` class is **abstract** and cannot be instantiated
- ❌ `FOOTPRINT_IO` class **doesn't exist**
- ✅ `FootprintLoad()` is a **module-level function**

### Correct API Usage

```python
import pcbnew

# Correct: Module-level function
footprint = pcbnew.FootprintLoad(library_directory, footprint_name)
```

**Parameters**:
- `library_directory`: Path to `.pretty` directory (e.g., `C:\Program Files\KiCad\9.0\share\kicad\footprints\LED_SMD.pretty`)
- `footprint_name`: Footprint name without extension (e.g., `LED_0603_1608Metric`)

## Complete Implementation

### Step 1: Initialize wxWidgets

```python
import wx
import sys
import os

# CRITICAL: Initialize wxWidgets BEFORE importing pcbnew
wx_app = None
try:
    import wx
    if not wx.GetApp():
        wx_app = wx.App(False)
except ImportError:
    pass  # Continue if wxPython not available
```

### Step 2: Set Up KiCad Python Path

```python
# Add KiCad Python path
kicad_python_path = r'C:\Program Files\KiCad\9.0\bin\Lib\site-packages'
if os.path.exists(kicad_python_path):
    if kicad_python_path not in sys.path:
        sys.path.insert(0, kicad_python_path)

# Add KiCad bin to PATH for DLL loading
kicad_bin_path = r'C:\Program Files\KiCad\9.0\bin'
if kicad_bin_path not in os.environ.get('PATH', ''):
    os.environ['PATH'] = kicad_bin_path + os.pathsep + os.environ.get('PATH', '')
```

### Step 3: Import pcbnew

```python
import pcbnew
```

### Step 4: Find Footprint Libraries

```python
def find_footprint_libraries():
    """Find footprint library directories."""
    libraries = []
    
    # Standard KiCad library paths
    search_paths = [
        r"C:\Program Files\KiCad\9.0\share\kicad\footprints",  # Windows
        os.path.expanduser(r"~\Documents\KiCad\9.0\footprints"),  # User libraries
        "/usr/share/kicad/footprints",  # Linux
        os.path.expanduser("~/Documents/KiCad/9.0/footprints"),  # Linux user
    ]
    
    for base_path in search_paths:
        if not os.path.exists(base_path):
            continue
        
        # Find .pretty directories
        for item in os.listdir(base_path):
            item_path = os.path.join(base_path, item)
            if os.path.isdir(item_path) and item.endswith('.pretty'):
                lib_name = item[:-7]  # Remove .pretty
                libraries.append({
                    'name': lib_name,
                    'path': item_path
                })
    
    return libraries
```

### Step 5: Locate Footprint File

```python
def find_footprint_file(lib_name, footprint_name, libraries):
    """Find .kicad_mod file for a footprint."""
    for lib in libraries:
        if lib['name'] == lib_name:
            footprint_file = os.path.join(lib['path'], footprint_name + '.kicad_mod')
            if os.path.exists(footprint_file):
                return footprint_file
    return None
```

### Step 6: Load Footprint

```python
def load_footprint_from_library(lib_name, footprint_name, libraries):
    """Load footprint from KiCad library."""
    # Find footprint file
    footprint_file = find_footprint_file(lib_name, footprint_name, libraries)
    
    if not footprint_file:
        return None
    
    # Get library directory and footprint name
    lib_dir = os.path.dirname(footprint_file)
    fp_name = os.path.basename(footprint_file).replace('.kicad_mod', '')
    
    # Load footprint using module-level function
    try:
        footprint = pcbnew.FootprintLoad(lib_dir, fp_name)
        return footprint
    except Exception as e:
        print(f"Error loading footprint: {e}")
        return None
```

### Step 7: Replace Placeholder Footprints

```python
def replace_placeholders_with_real_footprints(board_path):
    """Replace placeholder footprints with real library footprints."""
    # Load board
    board = pcbnew.LoadBoard(board_path)
    if board is None:
        return False
    
    # Find libraries
    libraries = find_footprint_libraries()
    
    # Get all footprints
    footprints = board.GetFootprints()
    replaced_count = 0
    
    for footprint in footprints:
        ref = footprint.GetReference()
        fpid = footprint.GetFPID()
        lib_name = str(fpid.GetLibNickname())
        footprint_name = str(fpid.GetLibItemName())
        
        # Identify placeholders (e.g., single pad)
        pads = footprint.Pads()
        if len(pads) == 1:  # Placeholder indicator
            # Load real footprint
            real_footprint = load_footprint_from_library(lib_name, footprint_name, libraries)
            
            if real_footprint:
                # Preserve position, rotation, layer
                pos = footprint.GetPosition()
                rotation = footprint.GetOrientation()
                layer = footprint.GetLayer()
                
                # Remove placeholder
                board.Remove(footprint)
                
                # Set properties on real footprint
                real_footprint.SetReference(ref)
                real_footprint.SetPosition(pos)
                real_footprint.SetOrientation(rotation)
                if real_footprint.GetLayer() != layer:
                    real_footprint.Flip(pos, False)
                
                # Add to board
                board.Add(real_footprint)
                replaced_count += 1
    
    # Save board
    if replaced_count > 0:
        board.Save(board_path)
    
    return replaced_count > 0
```

## Complete Example

```python
#!/usr/bin/env python3
"""Load real footprints from KiCad 9.0 libraries."""

import sys
import os

# Initialize wxWidgets
import wx
if not wx.GetApp():
    wx_app = wx.App(False)

# Set up KiCad paths
kicad_python_path = r'C:\Program Files\KiCad\9.0\bin\Lib\site-packages'
if os.path.exists(kicad_python_path):
    sys.path.insert(0, kicad_python_path)

import pcbnew

def load_footprint(lib_name, footprint_name):
    """Load footprint from library."""
    search_paths = [
        r"C:\Program Files\KiCad\9.0\share\kicad\footprints",
        os.path.expanduser(r"~\Documents\KiCad\9.0\footprints"),
    ]
    
    for base_path in search_paths:
        if not os.path.exists(base_path):
            continue
        
        for item in os.listdir(base_path):
            item_path = os.path.join(base_path, item)
            if os.path.isdir(item_path) and item.endswith('.pretty'):
                if lib_name in item:
                    footprint_file = os.path.join(item_path, footprint_name + '.kicad_mod')
                    if os.path.exists(footprint_file):
                        lib_dir = os.path.dirname(footprint_file)
                        fp_name = os.path.basename(footprint_file).replace('.kicad_mod', '')
                        return pcbnew.FootprintLoad(lib_dir, fp_name)
    
    return None

# Usage
footprint = load_footprint("LED_SMD", "LED_0603_1608Metric")
if footprint:
    print("Footprint loaded successfully!")
```

## Common Issues

### Issue 1: "No constructor defined - class is abstract"

**Cause**: Trying to instantiate `PCB_IO()` which is abstract  
**Solution**: Use `pcbnew.FootprintLoad()` module-level function instead

### Issue 2: "AttributeError: module 'pcbnew' has no attribute 'FOOTPRINT_IO'"

**Cause**: `FOOTPRINT_IO` class doesn't exist in KiCad 9.0  
**Solution**: Use `pcbnew.FootprintLoad()` module-level function

### Issue 3: Footprint not found

**Cause**: Library name or footprint name mismatch  
**Solution**: Verify library and footprint names match exactly (case-sensitive)

### Issue 4: wxWidgets errors

**Cause**: wxWidgets not initialized before importing pcbnew  
**Solution**: Initialize `wx.App(False)` before importing pcbnew

## Library Organization

Footprint libraries are organized as:

```
footprints/
├── LED_SMD.pretty/
│   ├── LED_0603_1608Metric.kicad_mod
│   ├── LED_0805_2012Metric.kicad_mod
│   └── ...
├── Capacitor_SMD.pretty/
│   ├── C_0402_1005Metric.kicad_mod
│   └── ...
└── ...
```

## Best Practices

1. **Always initialize wxWidgets** before importing pcbnew
2. **Use module-level function** `pcbnew.FootprintLoad()`, not class methods
3. **Verify footprint exists** before attempting to load
4. **Preserve properties** (position, rotation, layer) when replacing footprints
5. **Handle errors gracefully** - not all footprints may be found

## Testing

Test with:
- KiCad 9.0.6+
- Windows 10/11
- Linux (Ubuntu)
- Python 3.11

## Related Documentation

- KiCad 9.0 Python API Documentation
- Global Memory: `kicad-9-footprint-loading-pattern.md`
- Global History: `kicad-9-load-real-footprints-solution.md`

## Status

✅ **VERIFIED** - Guide works with KiCad 9.0.6+



