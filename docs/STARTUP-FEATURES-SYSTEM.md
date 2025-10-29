# Startup Features Modular System

## Overview

The startup system has been refactored to use a modular features architecture. All startup features are now loaded from `Global-Workflows/startup-features/` automatically, allowing new features to be added without modifying `startup.ps1`.

## Architecture

### Features Directory
- **Location**: `Global-Workflows/startup-features/`
- **Purpose**: Contains modular feature scripts that extend startup functionality
- **Auto-Loading**: `startup.ps1` automatically discovers and loads all `.ps1` files in this directory

### Feature Module Structure

Each feature is a PowerShell script following this pattern:

```powershell
# feature-name.ps1
function Initialize-FeatureName {
    Write-Host "[FEATURE] Initializing FeatureName..." -ForegroundColor Cyan
    # Feature implementation here
    Write-Host "[OK] FeatureName ready" -ForegroundColor Green
}
```

**Naming Convention:**
- **File**: `feature-name.ps1` (kebab-case)
- **Function**: `Initialize-FeatureName` (PascalCase, "Initialize-" prefix)

### Current Features

1. **timer-service.ps1**
   - Initializes timer service to prevent session traps
   - Function: `Initialize-TimerService`

2. **minimum-model-levels.ps1**
   - Loads and enforces minimum AI model requirements
   - Function: `Initialize-MinimumModelLevels`

3. **memory-structure.ps1**
   - Creates and manages AI session memory structure
   - Function: `Initialize-MemoryStructure`

4. **resource-management.ps1**
   - Initializes resource management tools and health monitoring
   - Function: `Initialize-ResourceManagement`

5. **documentation-placement.ps1**
   - Verifies documentation is properly organized
   - Function: `Initialize-DocumentationPlacement`

## How It Works

### Automatic Feature Loading

The `startup.ps1` script:

1. Discovers all `.ps1` files in `Global-Workflows/startup-features/`
2. Sorts them alphabetically for consistent execution order
3. Dot-sources each file (loads the function into scope)
4. Converts filename to PascalCase and calls `Initialize-<FeatureName>`
5. Handles errors gracefully (continues with other features if one fails)

### Execution Order

Features execute in alphabetical order. To enforce a specific order, prefix filenames:
- `01-timer-service.ps1`
- `02-minimum-model-levels.ps1`
- etc.

## Adding New Features

### Quick Start

1. Create a new `.ps1` file in `Global-Workflows/startup-features/`
2. Name it using kebab-case (e.g., `my-new-feature.ps1`)
3. Define function using PascalCase (e.g., `Initialize-MyNewFeature`)
4. Feature will automatically load on next startup!

### Example Feature

```powershell
# my-new-feature.ps1
function Initialize-MyNewFeature {
    Write-Host "[MYFEATURE] Initializing..." -ForegroundColor Cyan
    
    # Your initialization code
    if (Test-Path "some-file.txt") {
        Write-Host "[OK] MyNewFeature ready" -ForegroundColor Green
    } else {
        Write-Host "[WARNING] MyNewFeature configuration missing" -ForegroundColor Yellow
    }
}
```

### Best Practices

- **Error Handling**: Use try/catch blocks
- **Status Messages**: Provide clear feedback
- **Idempotency**: Safe to run multiple times
- **Documentation**: Comment complex logic
- **Dependencies**: Check for required files/tools before proceeding

## Migration for Existing Projects

### Using the Migration Script

Run from any project directory:

```powershell
pwsh -ExecutionPolicy Bypass -File "Global-Scripts\migrate-startup-features.ps1"
```

**Options:**
- `-Backup` (default: true): Creates backup before migration
- `-DryRun`: Preview changes without modifying files
- `-ProjectPath`: Specify custom project path

### What the Migration Does

1. **Preserves Project-Specific Code**: Identifies and keeps all custom startup code
2. **Adds Modular Loader**: Inserts the features loader section
3. **Removes Duplicates**: Removes hardcoded feature code that's now in modules
4. **Creates Backup**: Safely backs up original file

### Manual Migration

If the script doesn't work for your project:

1. Open `startup.ps1`
2. Find where "MCP Protection Command available" appears
3. Insert the modular loader section (from shared startup.ps1)
4. Remove duplicate feature code (timer, model levels, memory, resource management)
5. Keep all project-specific code intact

## Benefits

### For New Projects
- ✅ No need to modify `startup.ps1` for new features
- ✅ Features automatically available to all projects
- ✅ Consistent feature loading across projects

### For Existing Projects
- ✅ Migration script preserves custom code
- ✅ Can selectively enable/disable features
- ✅ Easy to add project-specific features alongside global ones

### For Feature Development
- ✅ Isolated feature files (easier to maintain)
- ✅ Standardized initialization pattern
- ✅ Easy to test features independently
- ✅ Clear documentation per feature

## Troubleshooting

### Feature Not Loading

**Check:**
1. File is in `Global-Workflows/startup-features/`
2. File has `.ps1` extension
3. Function follows naming convention: `Initialize-<FeatureName>`
4. `Global-Workflows` junction exists and is linked correctly

### Feature Loads But Function Not Called

**Check:**
1. Function name matches converted filename
   - File: `my-feature.ps1` → Function: `Initialize-MyFeature`
2. Function is exported (not private)
3. No syntax errors in feature file

### Project-Specific Code Removed

**Solution:**
1. Restore from backup (`.backup-YYYYMMDD-HHMMSS`)
2. Re-run migration with `-DryRun` first
3. Manually merge project-specific sections

## File Locations

- **Features Directory**: `Global-Workflows/startup-features/`
- **Migration Script**: `Global-Scripts/migrate-startup-features.ps1`
- **Shared Startup**: `C:\Users\kento\.cursor\Deployment\For Every Project\startup.ps1`
- **Documentation**: `Global-Workflows/startup-features/README.md`

## Next Steps

1. **Test Current Setup**: Run `startup.ps1` to verify all features load
2. **Migrate Other Projects**: Use migration script on existing projects
3. **Add New Features**: Create new `.ps1` files in features directory
4. **Update Documentation**: Update this file as features are added

---

**Created**: January 2025  
**Status**: Active  
**Maintained By**: Global-Workflows system (accessible via Global-Workflows junction)

