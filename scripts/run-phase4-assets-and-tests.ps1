# Phase 4 Asset Creation & Testing Automation Script
# PowerShell script to run UE5 Python scripts for asset creation and testing

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("CreateAssets", "RunTests", "Both")]
    [string]$Action = "Both",
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipEditor
)

$UEEnginePath = "C:\Program Files\Epic Games\UE_5.6"
$ProjectPath = "E:\Vibe Code\Gaming System\AI Core\unreal\BodyBroker.uproject"
$ScriptsPath = "E:\Vibe Code\Gaming System\AI Core\unreal\Scripts"

Write-Host "=== Phase 4 Asset Creation & Testing ===" -ForegroundColor Cyan
Write-Host ""

# Verify UE5 installation
if (-not (Test-Path $UEEnginePath)) {
    Write-Host "❌ UE 5.6.1 not found at: $UEEnginePath" -ForegroundColor Red
    exit 1
}

Write-Host "✓ UE 5.6.1 found" -ForegroundColor Green

# Check if scripts exist
$CreateAssetsScript = Join-Path $ScriptsPath "create_phase4_assets.py"
$RunTestsScript = Join-Path $ScriptsPath "run_phase4_tests.py"

if (-not (Test-Path $CreateAssetsScript)) {
    Write-Host "❌ Asset creation script not found: $CreateAssetsScript" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $RunTestsScript)) {
    Write-Host "❌ Test script not found: $RunTestsScript" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Scripts found" -ForegroundColor Green
Write-Host ""

# Function to run Python script in UE5 Editor
function Run-UE5PythonScript {
    param(
        [string]$ScriptPath,
        [string]$Description
    )
    
    Write-Host "Running: $Description" -ForegroundColor Yellow
    
    # Method 1: Use UE5 Editor command line with Python execution
    $EditorExe = Join-Path $UEEnginePath "Engine\Binaries\Win64\UnrealEditor.exe"
    
    if (-not (Test-Path $EditorExe)) {
        Write-Host "❌ UnrealEditor.exe not found" -ForegroundColor Red
        return $false
    }
    
    # Create a temporary Python script that imports and runs our script
    $TempScript = Join-Path $env:TEMP "ue5_python_wrapper.py"
    $ScriptContent = @"
import sys
import os

# Add scripts directory to path
sys.path.insert(0, r'$ScriptsPath')

# Import and run the script
try:
    import create_phase4_assets
    create_phase4_assets.main()
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
"@
    
    $ScriptContent | Out-File -FilePath $TempScript -Encoding UTF8
    
    # Run UE5 Editor with Python script execution
    # Note: UE5 Editor needs to be launched with -ExecutePythonScript parameter
    $PythonCommand = "-ExecutePythonScript=`"$TempScript`""
    
    Write-Host "  → Launching UE5 Editor with Python script..." -ForegroundColor White
    Write-Host "  → This will open UE5 Editor and execute the script" -ForegroundColor White
    Write-Host ""
    
    # Start UE5 Editor process
    $Process = Start-Process -FilePath $EditorExe -ArgumentList $ProjectPath, $PythonCommand -PassThru -NoNewWindow
    
    Write-Host "  → UE5 Editor launched (PID: $($Process.Id))" -ForegroundColor Green
    Write-Host "  → Check UE5 Editor Output Log for script results" -ForegroundColor Yellow
    Write-Host ""
    
    return $true
}

# Execute based on action
if ($Action -eq "CreateAssets" -or $Action -eq "Both") {
    Write-Host "=== ASSET CREATION ===" -ForegroundColor Cyan
    Run-UE5PythonScript -ScriptPath $CreateAssetsScript -Description "Asset Creation"
    Write-Host ""
}

if ($Action -eq "RunTests" -or $Action -eq "Both") {
    Write-Host "=== RUNTIME TESTING ===" -ForegroundColor Cyan
    Write-Host "Note: Tests require:" -ForegroundColor Yellow
    Write-Host "  1. UE5 Editor open with project loaded" -ForegroundColor White
    Write-Host "  2. BP_Phase4TestActor spawned in level" -ForegroundColor White
    Write-Host "  3. All components configured" -ForegroundColor White
    Write-Host ""
    Write-Host "To run tests manually:" -ForegroundColor Yellow
    Write-Host "  1. Open UE5 Editor" -ForegroundColor White
    Write-Host "  2. Open Python console (Window > Developer Tools > Python Console)" -ForegroundColor White
    Write-Host "  3. Run: exec(open(r'$RunTestsScript').read())" -ForegroundColor White
    Write-Host ""
}

Write-Host "=== COMPLETE ===" -ForegroundColor Green
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "  1. Open UE5 Editor manually" -ForegroundColor White
Write-Host "  2. Run Python scripts from Python Console" -ForegroundColor White
Write-Host "  3. Or use UE5 Editor's Python API directly" -ForegroundColor White
Write-Host ""
Write-Host "See docs/testing/PHASE4-RUNTIME-TESTING-GUIDE.md for detailed instructions" -ForegroundColor Cyan

