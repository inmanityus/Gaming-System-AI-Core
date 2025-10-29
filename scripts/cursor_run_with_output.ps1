param(
  [int]$TimeoutSec = 900,
  [string]$Label = "cmd",
  [Parameter(ValueFromRemainingArguments=$true)]
  [string[]]$Args
)

if (-not $Args -or $Args.Count -eq 0) {
  Write-Host "Usage: cursor_run_with_output.ps1 -TimeoutSec <sec> -Label <name> -- <command...>"
  exit 2
}

$cursorRunPath = Join-Path $PSScriptRoot "cursor_run.ps1"
if (-not (Test-Path $cursorRunPath)) {
  Write-Host "ERROR: Unable to locate cursor_run.ps1 at $cursorRunPath"
  exit 2
}

& $cursorRunPath -TimeoutSec $TimeoutSec -Label $Label -Args $Args
$exitCode = $LASTEXITCODE

$logDir = Join-Path (Get-Location) ".cursor/ai-logs"
if (-not (Test-Path $logDir)) {
  Write-Host "WATCHDOG+: Log directory not found at $logDir"
  exit $exitCode
}

$labelSafe = $Label -replace ' ', '_'
$latestLog = Get-ChildItem $logDir -Filter "*${labelSafe}*.log" -ErrorAction SilentlyContinue |
  Sort-Object LastWriteTime -Descending |
  Select-Object -First 1

if ($null -ne $latestLog) {
  Write-Host "---- begin watchdog log: $($latestLog.Name) ----"
  Get-Content $latestLog.FullName
  Write-Host "---- end watchdog log ----"
  Write-Host "WATCHDOG+: Tail complete. Log saved at $($latestLog.FullName)"
} else {
  Write-Host "WATCHDOG+: No log file found for label '$Label'."
}

exit $exitCode
