param(
  [string]$SearchRoot = 'E:\Vibe Code',
  [string]$ProjectRoot = (Get-Location).Path
)

$ErrorActionPreference = 'Stop'

Write-Host "=== Restore Global Scripts ===" -ForegroundColor Cyan
Write-Host "SearchRoot : $SearchRoot" -ForegroundColor Gray
Write-Host "ProjectRoot: $ProjectRoot" -ForegroundColor Gray
Write-Host ""

if (-not (Test-Path $SearchRoot)) {
  Write-Host "ERROR: SearchRoot does not exist: $SearchRoot" -ForegroundColor Red
  exit 2
}
if (-not (Test-Path $ProjectRoot)) {
  Write-Host "ERROR: ProjectRoot does not exist: $ProjectRoot" -ForegroundColor Red
  exit 2
}

# Targets to restore (filename -> destination full path)
$targets = @{
  'git-push-to-github.ps1'       = (Join-Path $ProjectRoot 'Global-Scripts\git-push-to-github.ps1')
  'git-commit-and-push.ps1'      = (Join-Path $ProjectRoot 'Global-Scripts\git-commit-and-push.ps1')
  'migrate-startup-features.ps1' = (Join-Path $ProjectRoot 'Global-Scripts\migrate-startup-features.ps1')
  'monitor-resources.ps1'        = (Join-Path $ProjectRoot 'Global-Scripts\monitor-resources.ps1')
  'resource-cleanup.ps1'         = (Join-Path $ProjectRoot 'Global-Scripts\resource-cleanup.ps1')
  'emergency-flush.ps1'          = (Join-Path $ProjectRoot 'Global-Scripts\emergency-flush.ps1')
  'rule-retriever.ps1'           = (Join-Path $ProjectRoot 'Global-Scripts\rule-memory\rule-retriever.ps1')
  'start-accept-burst.ps1'       = 'C:\Users\kento\.cursor\start-accept-burst.ps1'  # outside repo
}

$restored = New-Object System.Collections.Generic.List[string]
$missing  = New-Object System.Collections.Generic.List[string]

function Restore-FileByNewest {
  param(
    [Parameter(Mandatory=$true)][string]$FileName,
    [Parameter(Mandatory=$true)][string]$Destination
  )
  try {
    $matches = Get-ChildItem -Path $SearchRoot -Filter $FileName -Recurse -File -ErrorAction SilentlyContinue
  } catch {
    $matches = @()
  }
  if ($matches -and $matches.Count -gt 0) {
    $best = $matches | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    $destDir = Split-Path $Destination -Parent
    if (-not (Test-Path $destDir)) {
      New-Item -ItemType Directory -Force -Path $destDir | Out-Null
    }
    Copy-Item -Path $best.FullName -Destination $Destination -Force
    Write-Host ("[OK] Restored {0} -> {1} (from {2})" -f $FileName, $Destination, $best.FullName) -ForegroundColor Green
    $script:restored.Add($FileName)
  } else {
    Write-Host ("[MISS] Not found under {0}: {1}" -f $SearchRoot, $FileName) -ForegroundColor Yellow
    $script:missing.Add($FileName)
  }
}

# Restore files
foreach ($key in $targets.Keys) {
  Restore-FileByNewest -FileName $key -Destination $targets[$key]
}

# Restore startup-features folder (directory)
$startupFeaturesDest = Join-Path $ProjectRoot 'Global-Workflows\startup-features'
try {
  $startupCandidates = Get-ChildItem -Path $SearchRoot -Directory -Recurse -ErrorAction SilentlyContinue | Where-Object { $_.Name -eq 'startup-features' }
} catch {
  $startupCandidates = @()
}

if ($startupCandidates -and $startupCandidates.Count -gt 0) {
  $bestDir = $startupCandidates | Sort-Object LastWriteTime -Descending | Select-Object -First 1
  if (-not (Test-Path $startupFeaturesDest)) {
    New-Item -ItemType Directory -Force -Path $startupFeaturesDest | Out-Null
  }
  # Prefer robocopy for speed/preservation on Windows
  $robocopy = (Get-Command robocopy -ErrorAction SilentlyContinue)
  if ($robocopy) {
    $null = robocopy $bestDir.FullName $startupFeaturesDest /E /NFL /NDL /NJH /NJS
  } else {
    Copy-Item -Path (Join-Path $bestDir.FullName '*') -Destination $startupFeaturesDest -Recurse -Force -ErrorAction SilentlyContinue
  }
  Write-Host ("[OK] Restored folder startup-features -> {0} (from {1})" -f $startupFeaturesDest, $bestDir.FullName) -ForegroundColor Green
  $restored.Add('startup-features (folder)')
} else {
  Write-Host ("[MISS] Not found under {0}: Global-Workflows\startup-features (folder)" -f $SearchRoot) -ForegroundColor Yellow
  $missing.Add('startup-features (folder)')
}

# Verification
Write-Host ""
Write-Host "=== Verification ===" -ForegroundColor Cyan
foreach ($kvp in $targets.GetEnumerator()) {
  $exists = Test-Path $kvp.Value
  $status = if ($exists) { 'OK' } else { 'MISSING' }
  $color  = if ($exists) { 'Green' } else { 'Yellow' }
  Write-Host ("{0,-36} : {1} -> {2}" -f $kvp.Key, $status, $kvp.Value) -ForegroundColor $color
}
$sfExists = Test-Path $startupFeaturesDest
$sfStatus = if ($sfExists) { 'OK' } else { 'MISSING' }
$sfColor  = if ($sfExists) { 'Green' } else { 'Yellow' }
Write-Host ("{0,-36} : {1} -> {2}" -f 'startup-features (folder)', $sfStatus, $startupFeaturesDest) -ForegroundColor $sfColor

Write-Host ""
Write-Host "=== Summary ===" -ForegroundColor Cyan
Write-Host ("Restored: {0}" -f ($restored -join ', ')) -ForegroundColor Green
if ($missing.Count -gt 0) {
  Write-Host ("Missing : {0}" -f ($missing -join ', ')) -ForegroundColor Yellow
} else {
  Write-Host "Missing : none" -ForegroundColor Green
}

# Exit success even if some items are missing; goal is to run to completion reliably
exit 0


