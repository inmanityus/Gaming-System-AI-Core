param(
  [int]$TimeoutSec = 900,
  [string]$Label = "cmd",
  [Parameter(ValueFromRemainingArguments=$true)]
  [string[]]$Args
)

if (-not $Args -or $Args.Count -eq 0) {
  Write-Host "Usage: cursor_run.ps1 -TimeoutSec <sec> -Label <name> -- <command...>"
  exit 2
}

$LogDir = ".cursor/ai-logs"
New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$labelSafe = $Label -replace ' ', '_'
$logFile = Join-Path $LogDir "$stamp-$labelSafe.log"
$metaFile = "$logFile.meta.json"

# idempotency (2 minutes window)
$lastCmds = Join-Path $LogDir "last-commands.jsonl"
$hashInput = (Get-Location).Path + "`0" + ($Args -join ' ')
$sha256 = [System.BitConverter]::ToString((New-Object -TypeName System.Security.Cryptography.SHA256Managed).ComputeHash([Text.Encoding]::UTF8.GetBytes($hashInput))).Replace("-", "").ToLower()
$now = [int][double]::Parse((Get-Date -UFormat %s))

if (Test-Path $lastCmds) {
  $recent = Select-String -Path $lastCmds -Pattern "`"hash`":`"$sha256`"" -SimpleMatch
  if ($recent) {
    $line = (Get-Content $lastCmds | Where-Object { $_ -match "`"hash`":`"$sha256`"" } | Select-Object -Last 1)
    if ($line -match '"ts":(\d+)') {
      $ts = [int]$Matches[1]
      if (($now - $ts) -lt 120) {
        Write-Host "WATCHDOG: Skipping duplicate command (within 120s). Hash=$sha256"
        exit 0
      }
    }
  }
}
"{""ts"":$now,""cwd"":""$((Get-Location).Path.Replace('"','\"'))"",""hash"":""$sha256"",""label"":""$Label"",""cmd"":""$([Text.Encoding]::UTF8.GetString([Text.Encoding]::UTF8.GetBytes(($Args -join ' '))))""}" | Add-Content -Path $lastCmds

# Start process with timeout & heartbeat
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = "powershell"
$psi.Arguments = "-NoProfile -Command $($Args -join ' ')"
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.UseShellExecute = $false
$proc = New-Object System.Diagnostics.Process
$proc.StartInfo = $psi
$null = $proc.Start()

$start = Get-Date
$lastBytes = 0
$buffer = New-Object System.Text.StringBuilder

while (-not $proc.HasExited) {
  Start-Sleep -Milliseconds 500
  $out = $proc.StandardOutput.ReadToEnd()
  $err = $proc.StandardError.ReadToEnd()
  if ($out) { $buffer.Append($out) | Out-Null }
  if ($err) { $buffer.Append($err) | Out-Null }

  $elapsed = (Get-Date) - $start
  if ($elapsed.TotalSeconds -ge $TimeoutSec) {
    try { $proc.CloseMainWindow() | Out-Null } catch {}
    Start-Sleep -Seconds 5
    try { if (-not $proc.HasExited) { $proc.Kill() } } catch {}
    $buffer.AppendLine("WATCHDOG: Killed after $TimeoutSec s") | Out-Null
    break
  }
}

if (-not $proc.HasExited) { $proc.WaitForExit() }
$exit = $proc.ExitCode
$content = $buffer.ToString()
$lines = ($content -split "`r?`n").Count
$truncated = $false
if ($lines -gt 2000) {
  $head = ($content -split "`r?`n")[0..999] -join "`n"
  $tail = ($content -split "`r?`n")[-1000..-1] -join "`n"
  "$head`n--- [truncated] ---`n$tail" | Set-Content -Path $logFile -Encoding UTF8
  $truncated = $true
} else {
  $content | Set-Content -Path $logFile -Encoding UTF8
}

$dur = [int]((Get-Date) - $start).TotalSeconds
Write-Host "WATCHDOG: label=$Label exit=$exit durationSec=$dur log=$logFile truncated=$truncated"
"{""exitCode"":$exit,""durationSec"":$dur,""logPath"":""$logFile"",""truncated"":$truncated}" | Set-Content -Path $metaFile -Encoding UTF8
exit $exit
