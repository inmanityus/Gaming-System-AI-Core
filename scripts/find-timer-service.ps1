param(
  [string[]]$Roots = @()
)

$ErrorActionPreference = 'Stop'

Write-Host "=== Find Timer Windows Service & Script Locations ===" -ForegroundColor Cyan

function Get-TimerServices {
  try {
    $svc = Get-CimInstance Win32_Service | Where-Object {
      ($_.Name -match '(?i)timer') -or ($_.DisplayName -match '(?i)timer')
    } | Select-Object Name, DisplayName, State, StartMode, PathName
  } catch {
    $svc = @()
  }
  return ,$svc
}

function Search-ProjectRoots {
  param(
    [string[]]$Roots
  )
  $results = @()
  $nameTargets = @(
    'global-command-timer.ps1',
    'cleanup-orphaned-timers-auto.ps1',
    'RuleEnforcerService.ps1'
  )
  $contentTargets = @(
    'New-Service',
    'sc.exe create',
    'Register-ScheduledTask',
    'nssm'
  )

  foreach ($root in $Roots) {
    if (-not (Test-Path $root)) {
      $results += [pscustomobject]@{
        Root   = $root
        Type   = 'root-missing'
        Path   = $null
        Match  = $null
        Stamp  = $null
      }
      continue
    }

    # Filename matches
    foreach ($n in $nameTargets) {
      try {
        $files = Get-ChildItem -Path (Join-Path $root '*') -Recurse -File -Filter $n -ErrorAction SilentlyContinue
      } catch {
        $files = @()
      }
      foreach ($f in $files) {
        $results += [pscustomobject]@{
          Root   = $root
          Type   = 'filename'
          Path   = $f.FullName
          Match  = $n
          Stamp  = $f.LastWriteTime
        }
      }
    }

    # Content matches (powershell files)
    try {
      $psFiles = Get-ChildItem -Path (Join-Path $root '*') -Recurse -File -Include *.ps1 -ErrorAction SilentlyContinue
    } catch {
      $psFiles = @()
    }

    foreach ($f in $psFiles) {
      foreach ($pat in $contentTargets) {
        try {
          $hit = Select-String -Path $f.FullName -Pattern $pat -SimpleMatch -Quiet -ErrorAction SilentlyContinue
        } catch {
          $hit = $false
        }
        if ($hit) {
          $results += [pscustomobject]@{
            Root   = $root
            Type   = 'content'
            Path   = $f.FullName
            Match  = $pat
            Stamp  = $f.LastWriteTime
          }
        }
      }
    }
  }

  return ,$results
}

$timerSvcs = Get-TimerServices
$searchRes = @()
if ($Roots -and $Roots.Count -gt 0) {
  $searchRes = Search-ProjectRoots -Roots $Roots
}

$out = [pscustomobject]@{
  Services = $timerSvcs
  Search   = $searchRes | Sort-Object Stamp -Descending
}

$json = $out | ConvertTo-Json -Depth 6
Write-Output $json






