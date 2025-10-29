<#
  Stops processes launched via start-visual-test-env.ps1 and also ensures
  browser automation processes (Playwright, Chromium, Edge, Chrome) are
  terminated so subsequent visual testing runs start clean.
#>

[CmdletBinding()]
param(
    [string]$SessionFile = ".cursor/visual-testing-session.json",
    [switch]$IncludeBrowsers,
    [string[]]$BrowserProcesses = @("chrome", "msedge", "chromium", "playwright"),
    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$workspaceRoot = (Get-Item (Join-Path $scriptDir ".." )).FullName
Set-Location $workspaceRoot

function Resolve-SessionPath {
    param([string]$Path)
    if ([System.IO.Path]::IsPathRooted($Path)) {
        return $Path
    }
    return (Join-Path -Path $workspaceRoot -ChildPath $Path)
}

$sessionPath = Resolve-SessionPath -Path $SessionFile
if (-not (Test-Path -Path $sessionPath)) {
    if ($Force) {
        Write-Host "No session file found at '$sessionPath'. Nothing to stop."

        if (Test-Path $SessionFile) {
            try {
                Remove-Item $SessionFile -Force
            } catch {}
        }

        if (Test-Path $SessionFile) {
            try { Remove-Item $SessionFile -Force } catch {}
        }
        return
    }
    throw "Visual testing session file not found at '$sessionPath'."
}

$session = Get-Content -Path $sessionPath -Raw | ConvertFrom-Json

$stopped = @()
$failures = @()

foreach ($svc in $session.services) {
    $pid = [int]$svc.pid
    try {
        $proc = Get-Process -Id $pid -ErrorAction Stop
        Write-Host "Stopping service '$($svc.name)' (PID $pid)..."
        Stop-Process -Id $pid -Force
        $stopped += $svc
    } catch {
        Write-Warning "Unable to stop service '$($svc.name)' (PID $pid): $_"
        $failures += $svc
    }

    if ($svc.PSObject.Properties["port"] -and $svc.port) {
        try {
            $connections = Get-NetTCPConnection -LocalPort ([int]$svc.port) -ErrorAction SilentlyContinue
            if (-not $connections) {
                Write-Host "Port $($svc.port) released for service '$($svc.name)'"
            } else {
                $otherPids = $connections | Select-Object -ExpandProperty OwningProcess -Unique | Where-Object { $_ -ne $pid }
                foreach ($otherPid in $otherPids) {
                    try {
                        $otherProc = Get-Process -Id $otherPid -ErrorAction Stop
                        Write-Host "Stopping lingering process on port $($svc.port) (PID $otherPid - $($otherProc.ProcessName))"
                        Stop-Process -Id $otherPid -Force
                    } catch {
                        Write-Warning "Failed to stop lingering PID $otherPid on port $($svc.port): $_"
                    }
                }
            }
        } catch {
            Write-Warning "Port cleanup for $($svc.name) on $($svc.port) failed: $($_.Exception.Message)"
        }
    }
}

if ($IncludeBrowsers) {
    foreach ($name in $BrowserProcesses) {
        try {
            $procs = Get-Process -Name $name -ErrorAction SilentlyContinue
            if ($procs) {
                Write-Host "Stopping browser processes with name '$name'..."
                $procs | Stop-Process -Force
            }
        } catch {
            Write-Warning "Failed to stop browser process '$name': $_"
        }
    }
}

Remove-Item -Path $sessionPath -Force
Write-Host "Removed session file $sessionPath"

if ($failures.Count -gt 0) {
    $failedNames = $failures | ForEach-Object { $_.name } | Sort-Object -Unique
    throw "Failed to stop services: $([string]::Join(', ', $failedNames))"
}

Write-Host "Stopped $($stopped.Count) service(s). Visual testing environment shut down."

