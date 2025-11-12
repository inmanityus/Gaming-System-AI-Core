param(
  [string]$SourceWebsite = 'E:\Vibe Code\Be Free Fitness\Website',
  [string]$DestProject   = 'E:\Vibe Code\Gaming System\AI Core'
)

$ErrorActionPreference = 'Stop'

$dstGlobal = Join-Path $DestProject 'Global-Scripts'
$dstRuleEnf = Join-Path $dstGlobal 'rule-enforcement'
New-Item -ItemType Directory -Force -Path $dstGlobal | Out-Null
New-Item -ItemType Directory -Force -Path $dstRuleEnf | Out-Null

$srcTimer      = Join-Path $SourceWebsite '.cursor\scripts\global-command-timer.ps1'
$srcCleanupA   = Join-Path $SourceWebsite 'scripts\cleanup-orphaned-timers-auto.ps1'
$srcCleanupB   = Join-Path $SourceWebsite '.cursor\scripts\cleanup-orphaned-timers-auto.ps1'
$srcRuleEnf    = Join-Path $SourceWebsite '.cursor\scripts\rule-enforcement\RuleEnforcerService.ps1'

# Copy global-command-timer.ps1
if (Test-Path $srcTimer -PathType Leaf) {
  Copy-Item -Path $srcTimer -Destination (Join-Path $dstGlobal 'global-command-timer.ps1') -Force
  Write-Host "[OK] Copied global-command-timer.ps1" -ForegroundColor Green
} else {
  Write-Host "[MISS] Not found: $srcTimer" -ForegroundColor Yellow
}

# Choose newest cleanup-orphaned-timers-auto.ps1
$chosenCleanup = $null
$hasA = Test-Path $srcCleanupA -PathType Leaf
$hasB = Test-Path $srcCleanupB -PathType Leaf
if ($hasA -and $hasB) {
  $a = (Get-Item -LiteralPath $srcCleanupA).LastWriteTime
  $b = (Get-Item -LiteralPath $srcCleanupB).LastWriteTime
  $chosenCleanup = if ($a -ge $b) { $srcCleanupA } else { $srcCleanupB }
} elseif ($hasA) {
  $chosenCleanup = $srcCleanupA
} elseif ($hasB) {
  $chosenCleanup = $srcCleanupB
}
if ($chosenCleanup) {
  Copy-Item -Path $chosenCleanup -Destination (Join-Path $dstGlobal 'cleanup-orphaned-timers-auto.ps1') -Force
  Write-Host "[OK] Copied cleanup-orphaned-timers-auto.ps1 (source: $chosenCleanup)" -ForegroundColor Green
} else {
  Write-Host "[MISS] cleanup-orphaned-timers-auto.ps1 not found in expected sources" -ForegroundColor Yellow
}

# Copy RuleEnforcerService.ps1
if (Test-Path $srcRuleEnf -PathType Leaf) {
  Copy-Item -Path $srcRuleEnf -Destination (Join-Path $dstRuleEnf 'RuleEnforcerService.ps1') -Force
  Write-Host "[OK] Copied RuleEnforcerService.ps1" -ForegroundColor Green
} else {
  Write-Host "[MISS] Not found: $srcRuleEnf" -ForegroundColor Yellow
}

Write-Host "DONE" -ForegroundColor Cyan


