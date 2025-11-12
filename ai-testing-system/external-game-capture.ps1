# External Game Screenshot Capture Tool
# Works with ANY game (Marvel Rivals, Steam games, etc.)
# Generates GameObserver-compatible captures for vision analysis testing

param(
    [string]$GameName = "Marvel Rivals",
    [int]$CaptureCount = 10,
    [int]$IntervalSeconds = 5
)

$ErrorActionPreference = "Stop"

Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  External Game Capture Tool" -ForegroundColor Cyan
Write-Host "  Testing AI Vision System with Real Games" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
Write-Host "Game: $GameName" -ForegroundColor Yellow
Write-Host "Captures: $CaptureCount screenshots" -ForegroundColor Yellow
Write-Host "Interval: $IntervalSeconds seconds" -ForegroundColor Yellow
Write-Host ""

# Load Windows Forms for screenshot capture
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# Output directory
$OutputDir = "unreal\GameObserver\Captures"
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

Write-Host "Output Directory: $OutputDir" -ForegroundColor Cyan
Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "  READY TO CAPTURE" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "Instructions:" -ForegroundColor Yellow
Write-Host "1. Launch $GameName NOW" -ForegroundColor White
Write-Host "2. Get into gameplay (menu, combat, any scene)" -ForegroundColor White
Write-Host "3. This script will capture $CaptureCount screenshots every $IntervalSeconds seconds" -ForegroundColor White
Write-Host "4. Switch between different scenes to test various scenarios" -ForegroundColor White
Write-Host ""
Write-Host "Starting in 10 seconds..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host ""
Write-Host "CAPTURING STARTED - Keep playing the game!" -ForegroundColor Green
Write-Host "════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""

for ($i = 1; $i -le $CaptureCount; $i++) {
    $Timestamp = Get-Date -Format "yyyyMMdd_HHmmss_fff"
    $Counter = "{0:D4}" -f $i
    
    # Determine event type based on capture number (simulate different events)
    $EventTypes = @("Baseline", "OnPlayerDamage", "OnCombatStart", "OnEnterNewZone", "OnUIPopup")
    $EventType = $EventTypes[($i % $EventTypes.Count)]
    
    $ScreenshotFile = Join-Path $OutputDir "${EventType}_${Counter}_${Timestamp}.png"
    $TelemetryFile = Join-Path $OutputDir "${EventType}_${Counter}_${Timestamp}.json"
    
    Write-Host "[Capture $i/$CaptureCount] $(Get-Date -Format 'HH:mm:ss') - $EventType..." -NoNewline
    
    try {
        # Capture screenshot
        $Screen = [System.Windows.Forms.Screen]::PrimaryScreen
        $Bitmap = New-Object System.Drawing.Bitmap $Screen.Bounds.Width, $Screen.Bounds.Height
        $Graphics = [System.Drawing.Graphics]::FromImage($Bitmap)
        $Graphics.CopyFromScreen($Screen.Bounds.Location, [System.Drawing.Point]::Empty, $Screen.Bounds.Size)
        $Bitmap.Save($ScreenshotFile, [System.Drawing.Imaging.ImageFormat]::Png)
        $Graphics.Dispose()
        $Bitmap.Dispose()
        
        # Generate telemetry JSON
        $Telemetry = @{
            screenshot_filename = (Split-Path $ScreenshotFile -Leaf)
            timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss.fffZ")
            event_type = $EventType
            capture_trigger = @{
                event_type = $EventType
                source = "ExternalCapture"
                game_name = $GameName
                capture_method = "Windows Screen Capture"
            }
            player_data = @{
                location = @{ x = (Get-Random -Min 1000 -Max 2000); y = (Get-Random -Min 5000 -Max 8000); z = (Get-Random -Min 200 -Max 400) }
                rotation = @{ pitch = (Get-Random -Min -30 -Max 30); yaw = (Get-Random -Min 0 -Max 360); roll = 0 }
                velocity = @{ x = 0; y = 0; z = 0 }
                health = (Get-Random -Min 50 -Max 100)
                is_in_combat = ($EventType -eq "OnPlayerDamage" -or $EventType -eq "OnCombatStart")
            }
            world_data = @{
                zone_name = "$GameName Scene $i"
                current_objective_id = "OBJ_Validation_Test"
                game_name = $GameName
            }
            rendering_data = @{
                resolution = "$($Screen.Bounds.Width)x$($Screen.Bounds.Height)"
                current_fps = (Get-Random -Min 55 -Max 144)
                camera_fov = 90
            }
            test_metadata = @{
                is_external_game = $true
                game_name = $GameName
                capture_sequence = $i
                total_captures = $CaptureCount
            }
        }
        
        $Telemetry | ConvertTo-Json -Depth 10 | Out-File $TelemetryFile -Encoding UTF8
        
        Write-Host " ✓ Captured" -ForegroundColor Green
        
    } catch {
        Write-Host " ✗ Failed: $_" -ForegroundColor Red
    }
    
    # Wait for next capture (except on last iteration)
    if ($i -lt $CaptureCount) {
        Start-Sleep -Seconds $IntervalSeconds
    }
}

Write-Host ""
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "  ✓ CAPTURE COMPLETE" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════════" -ForegroundColor Green
Write-Host ""
Write-Host "Captured: $CaptureCount screenshots + telemetry" -ForegroundColor White
Write-Host "Location: $OutputDir" -ForegroundColor White
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Yellow
Write-Host "1. Start Local Test Runner Agent:" -ForegroundColor White
Write-Host "   cd ai-testing-system/local-test-runner" -ForegroundColor Gray
Write-Host "   python agent.py" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Agent will detect files and upload to S3" -ForegroundColor White
Write-Host "3. Orchestrator will trigger 3-model vision analysis" -ForegroundColor White
Write-Host "4. View results in Triage Dashboard: http://localhost:3000" -ForegroundColor White
Write-Host ""
Write-Host "Expected Analysis Time: 30-60 seconds per capture" -ForegroundColor Cyan

