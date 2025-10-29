# Startup Features Directory

This directory contains modular startup features that are automatically loaded by `startup.ps1`. 

## How It Works

Each feature is a PowerShell script that exports a function following the naming pattern:
- Function: `Initialize-<FeatureName>`
- File: `<feature-name>.ps1`

The startup script automatically:
1. Discovers all `.ps1` files in this directory
2. Dot-sources each file (loads the function)
3. Calls the `Initialize-<FeatureName>` function for each loaded feature

## Adding New Features

To add a new startup feature:

1. Create a new `.ps1` file in this directory (e.g., `my-new-feature.ps1`)
2. Define a function: `function Initialize-MyNewFeature { ... }`
3. The feature will automatically load on next startup

**Example:**
```powershell
# my-new-feature.ps1
function Initialize-MyNewFeature {
    Write-Host "[FEATURE] My New Feature initializing..." -ForegroundColor Cyan
    # Your initialization code here
    Write-Host "[OK] My New Feature ready" -ForegroundColor Green
}
```

## Current Features

- **timer-service.ps1**: Initializes timer service to prevent session traps
- **minimum-model-levels.ps1**: Loads and enforces minimum AI model requirements
- **memory-structure.ps1**: Creates and manages AI session memory structure
- **resource-management.ps1**: Initializes resource management tools and health monitoring
- **documentation-placement.ps1**: Verifies documentation is properly organized

## Feature Execution Order

Features are executed in alphabetical order by filename. If you need a specific execution order, prefix filenames with numbers:
- `01-timer-service.ps1`
- `02-minimum-model-levels.ps1`
- etc.

## Notes

- All features receive the same environment (PowerShell session scope)
- Features can access `$ProjectRoot` variable set by startup.ps1
- Features should handle errors gracefully (use try/catch)
- Features should provide clear status messages
- Features should be idempotent (safe to run multiple times)

