<#
  Starts the Be Free Fitness visual testing stack (API + web) and records
  process metadata so it can be torn down deterministically after the tests
  complete. Use the companion stop-visual-test-env.ps1 script for cleanup.
#>

[CmdletBinding()]
param(
    [switch]$SkipApi,
    [switch]$SkipWeb,
    [string]$ApiCommand = "pnpm --filter api start:dev",
    [string]$WebCommand = "pnpm --filter web dev",
    [int]$ApiPort = 4000,
    [int]$WebPort = 3000,
    [int]$StartupGraceSeconds = 20,
    [string]$SessionFile = ".cursor/visual-testing-session.json"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$workspaceRoot = (Get-Item (Join-Path $scriptDir ".." )).FullName
Set-Location $workspaceRoot

function Stop-PortProcesses {
    param(
        [int]$Port,
        [string]$ServiceName
    )

    if (-not $Port) { return }

    try {
        $connections = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction Stop
    } catch {
        Write-Host "[VisualEnv] Unable to query port $Port for $ServiceName: $($_.Exception.Message)" -ForegroundColor Yellow
        return
    }

    if (-not $connections) { return }

    $pids = $connections | Select-Object -ExpandProperty OwningProcess -Unique | Where-Object { $_ -gt 0 }
    foreach ($pid in $pids) {
        try {
            $proc = Get-Process -Id $pid -ErrorAction Stop
            Write-Host "[VisualEnv] Stopping existing process using port $Port for $ServiceName (PID $pid - $($proc.ProcessName))"
            Stop-Process -Id $pid -ErrorAction Stop
            Start-Sleep -Seconds 1
        } catch {
            Write-Host "[VisualEnv] Failed to stop PID $pid on port $Port: $($_.Exception.Message)" -ForegroundColor Yellow
        }
    }
}

function Resolve-SessionPath {
    param([string]$Path)
    if ([System.IO.Path]::IsPathRooted($Path)) {
        return $Path
    }
    return (Join-Path -Path $workspaceRoot -ChildPath $Path)
}

$sessionPath = Resolve-SessionPath -Path $SessionFile
$sessionDir = Split-Path -Path $sessionPath -Parent
if (-not [string]::IsNullOrWhiteSpace($sessionDir)) {
    New-Item -ItemType Directory -Path $sessionDir -Force | Out-Null
}

if (Test-Path -Path $sessionPath) {
    throw "Visual testing session already exists at '$sessionPath'. Run stop-visual-test-env.ps1 before starting a new session."
}

$logDir = Join-Path -Path $workspaceRoot -ChildPath ".cursor/ai-logs"
New-Item -ItemType Directory -Path $logDir -Force | Out-Null

$services = @()
if (-not $SkipApi) {
    $services += [pscustomobject]@{ name = "api"; command = $ApiCommand; port = $ApiPort }
}
if (-not $SkipWeb) {
    $services += [pscustomobject]@{ name = "web"; command = $WebCommand; port = $WebPort }
}

if ($services.Count -eq 0) {
    throw "No services selected. Provide at least one service to start or remove both Skip switches."
}

$managedProcesses = @()

foreach ($svc in $services) {
    if ($svc.PSObject.Properties["port"]) {
        Stop-PortProcesses -Port $svc.port -ServiceName $svc.name
    }

    $labelSafe = ($svc.name -replace "[^a-zA-Z0-9-]", "_")
    $stamp = Get-Date -Format "yyyyMMdd-HHmmss"
    $logPath = Join-Path -Path $logDir -ChildPath ("{0}-{1}.dev.log" -f $stamp, $labelSafe)

    Write-Host "Launching $($svc.name) using command: $($svc.command)"

    $command = "Set-Location `"$workspaceRoot`"; $($svc.command) | Tee-Object -FilePath `"$logPath`" -Append"
    $proc = Start-Process -FilePath "powershell.exe" `
        -ArgumentList "-NoLogo", "-NoProfile", "-NoExit", "-Command", $command `
        -WindowStyle Normal `
        -PassThru

    Start-Sleep -Milliseconds 500

    if ($proc.HasExited) {
        $exit = $proc.ExitCode
        $logPreview = ""
        if (Test-Path -Path $logPath) {
            $previewLines = Get-Content -Path $logPath -Tail 20
            $logPreview = [string]::Join([Environment]::NewLine, $previewLines)
        }
        throw "Service '$($svc.name)' exited immediately with code $exit. See log: $logPath`n$logPreview"
    }

    $stopCommand = "Stop-Process -Id $($proc.Id) -ErrorAction SilentlyContinue"

    $managedProcesses += [pscustomobject]@{
        name        = $svc.name
        command     = $svc.command
        logPath     = $logPath
        pid         = $proc.Id
        port        = $svc.PSObject.Properties["port"].Value
        stopCommand = $stopCommand
    }

    Write-Host "Started $($svc.name) (PID $($proc.Id)); logging to $logPath"
}

if ($StartupGraceSeconds -gt 0) {
    Write-Host "Waiting $StartupGraceSeconds second(s) for services to warm up..."
    Start-Sleep -Seconds $StartupGraceSeconds
}

$sessionData = @{
    createdAt        = (Get-Date).ToString("o")
    workingDirectory = $workspaceRoot
    services         = $managedProcesses
}

$sessionJson = $sessionData | ConvertTo-Json -Depth 4
Set-Content -Path $sessionPath -Value $sessionJson -Encoding UTF8

Write-Host "Visual testing session created at $sessionPath"
Write-Host "Remember to run scripts/stop-visual-test-env.ps1 when the visual testing run is complete."

