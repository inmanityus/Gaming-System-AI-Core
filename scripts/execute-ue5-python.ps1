# Execute UE5 Python Script and Capture Output
# Fixed version without $Error variable conflict

param(
    [string]$ScriptPath = "E:\Vibe Code\Gaming System\AI Core\unreal\Scripts\create_phase4_assets_enhanced.py",
    [int]$WaitSeconds = 30
)

$UEEditor = "C:\Program Files\Epic Games\UE_5.6\Engine\Binaries\Win64\UnrealEditor.exe"
$ProjectPath = "E:\Vibe Code\Gaming System\AI Core\unreal\BodyBroker.uproject"
$LogDir = "E:\Vibe Code\Gaming System\AI Core\unreal\Saved\Logs"

Write-Host "=== Executing UE5 Python Script ===" -ForegroundColor Cyan
Write-Host "Script: $ScriptPath" -ForegroundColor White
Write-Host "Project: $ProjectPath" -ForegroundColor White
Write-Host ""

# Create log directory if it doesn't exist
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Path $LogDir -Force | Out-Null
}

# Execute UE5 Editor with Python script
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $UEEditor
$psi.Arguments = "`"$ProjectPath`" -ExecutePythonScript=`"$ScriptPath`" -Unattended -NoSplash -NullRHI -Log=`"$LogDir\PythonExecution.log`""
$psi.UseShellExecute = $false
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.CreateNoWindow = $true

Write-Host "Starting UE5 Editor process..." -ForegroundColor Yellow
$process = [System.Diagnostics.Process]::Start($psi)

if ($process) {
    Write-Host "Process started (PID: $($process.Id))" -ForegroundColor Green
    Write-Host "Waiting $WaitSeconds seconds for script execution..." -ForegroundColor Yellow
    
    # Wait for script execution
    Start-Sleep -Seconds $WaitSeconds
    
    # Try to read output (may be empty if process hasn't flushed)
    try {
        $stdout = $process.StandardOutput.ReadToEnd()
        $stderr = $process.StandardError.ReadToEnd()
        
        if ($stdout) {
            Write-Host "`n=== STDOUT ===" -ForegroundColor Cyan
            Write-Host $stdout
        }
        
        if ($stderr) {
            Write-Host "`n=== STDERR ===" -ForegroundColor Yellow
            Write-Host $stderr
        }
    } catch {
        Write-Host "Could not read process output: $_" -ForegroundColor Yellow
    }
    
    # Check if process is still running
    if (-not $process.HasExited) {
        Write-Host "`nProcess still running. Terminating..." -ForegroundColor Yellow
        $process.Kill()
        Start-Sleep -Seconds 2
    }
    
    Write-Host "`n=== Checking Log Files ===" -ForegroundColor Cyan
    
    # Check Python execution log
    $pythonLog = Join-Path $LogDir "PythonExecution.log"
    if (Test-Path $pythonLog) {
        Write-Host "Python Execution Log:" -ForegroundColor Green
        Get-Content $pythonLog -Tail 50 | Select-String -Pattern "Phase|Asset|Reverb|Blueprint|Error|Exception|Python" -Context 0,1
    }
    
    # Check main UE5 log
    $mainLog = Join-Path $LogDir "BodyBroker.log"
    if (Test-Path $mainLog) {
        Write-Host "`nMain UE5 Log (Python-related):" -ForegroundColor Green
        Get-Content $mainLog -Tail 100 | Select-String -Pattern "Phase|Asset|Reverb|Blueprint|Error|Exception|Python|Script" -Context 0,1 | Select-Object -Last 30
    }
    
} else {
    Write-Host "Failed to start process" -ForegroundColor Red
    exit 1
}

Write-Host "`n=== Checking Created Assets ===" -ForegroundColor Cyan
$contentRoot = "E:\Vibe Code\Gaming System\AI Core\unreal\Content"

# Check directories
$dirs = @(
    "Audio\MetaSounds",
    "Audio\Reverb",
    "Data\Expressions",
    "Data\Gestures",
    "Blueprints",
    "Maps"
)

foreach ($dir in $dirs) {
    $fullPath = Join-Path $contentRoot $dir
    if (Test-Path $fullPath) {
        Write-Host "✓ $dir exists" -ForegroundColor Green
        $files = Get-ChildItem $fullPath -File -ErrorAction SilentlyContinue
        if ($files) {
            Write-Host "  Files ($($files.Count)):" -ForegroundColor White
            $files | Select-Object -First 5 | ForEach-Object { Write-Host "    - $($_.Name)" -ForegroundColor Gray }
            if ($files.Count -gt 5) {
                Write-Host "    ... and $($files.Count - 5) more" -ForegroundColor Gray
            }
        }
    } else {
        Write-Host "✗ $dir does not exist" -ForegroundColor Red
    }
}

Write-Host "`n=== Execution Complete ===" -ForegroundColor Green

