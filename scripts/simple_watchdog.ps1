param(
    [string]$Command,
    [string]$Label = "process",
    [int]$TimeoutSec = 1800
)

$LogDir = ".cursor/ai-logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$labelSafe = $Label -replace ' ', '_'
$logFile = Join-Path $LogDir "$stamp-$labelSafe.log"

Write-Host "WATCHDOG: Starting $Label with command: $Command"
Write-Host "WATCHDOG: Log file: $logFile"
Write-Host "WATCHDOG: Timeout: $TimeoutSec seconds"

# Start the process
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = "powershell"
$psi.Arguments = "-NoProfile -Command `"$Command`""
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.UseShellExecute = $false

$proc = New-Object System.Diagnostics.Process
$proc.StartInfo = $psi
$null = $proc.Start()

$start = Get-Date
$buffer = New-Object System.Text.StringBuilder

# Monitor the process
while (-not $proc.HasExited) {
    Start-Sleep -Milliseconds 500
    
    # Read output
    $out = $proc.StandardOutput.ReadToEnd()
    $err = $proc.StandardError.ReadToEnd()
    
    if ($out) { 
        $buffer.Append($out) | Out-Null
        Write-Host $out -NoNewline
    }
    if ($err) { 
        $buffer.Append($err) | Out-Null
        Write-Host $err -NoNewline
    }

    # Check timeout
    $elapsed = (Get-Date) - $start
    if ($elapsed.TotalSeconds -ge $TimeoutSec) {
        Write-Host "`nWATCHDOG: Timeout reached ($TimeoutSec seconds), terminating process"
        try { 
            $proc.CloseMainWindow() | Out-Null 
        } catch {}
        Start-Sleep -Seconds 2
        try { 
            if (-not $proc.HasExited) { 
                $proc.Kill() 
            } 
        } catch {}
        break
    }
}

# Wait for process to exit
if (-not $proc.HasExited) { 
    $proc.WaitForExit() 
}

$exitCode = $proc.ExitCode
$content = $buffer.ToString()

# Save log
$content | Set-Content -Path $logFile -Encoding UTF8

$duration = [int]((Get-Date) - $start).TotalSeconds
Write-Host "`nWATCHDOG: Process completed - Exit: $exitCode, Duration: $duration seconds"
Write-Host "WATCHDOG: Log saved to: $logFile"

exit $exitCode
