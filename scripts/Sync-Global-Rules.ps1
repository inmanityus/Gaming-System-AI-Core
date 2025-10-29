param(
    [switch]$Force
)

$homePath = $env:HOME
if ([string]::IsNullOrEmpty($homePath)) {
    $homePath = $env:USERPROFILE
}

if ([string]::IsNullOrEmpty($homePath)) {
    Write-Host "Unable to resolve HOME environment variable." -ForegroundColor Red
    exit 1
}

$globalRoot = Join-Path $homePath ".cursor\global-cursor-repo"
$expectedTargets = @{
    "Docker-Template" = Join-Path $globalRoot "docker-templates"
    "Global-Rules"    = Join-Path $globalRoot "rules"
    "Global-Scripts"  = Join-Path $globalRoot "scripts"
    "Global-Utils"    = Join-Path $globalRoot "utils"
    "Global-Workflows"= Join-Path $globalRoot "workflows"
}

Write-Host "Syncing global resources from $globalRoot" -ForegroundColor Green

if (-not (Test-Path $globalRoot)) {
    Write-Host "Global repository not found: $globalRoot" -ForegroundColor Red
    exit 1
}

$projectRoot = (Get-Item $PSScriptRoot).Parent.FullName
$cursorFolder = Join-Path $projectRoot ".cursor"

if (-not (Test-Path $cursorFolder)) {
    New-Item -ItemType Directory -Path $cursorFolder | Out-Null
}

$globalsLinkedPath = Join-Path $cursorFolder ".globals_linked"
$linkManifest = @{ globalRoot = $globalRoot; projectRoot = $projectRoot; linkedAt = (Get-Date).ToString("o") } | ConvertTo-Json -Depth 2
Set-Content -Path $globalsLinkedPath -Value $linkManifest -Encoding UTF8
Write-Host "[OK] Updated .globals_linked" -ForegroundColor Green

foreach ($entry in $expectedTargets.GetEnumerator()) {
    $linkName = $entry.Key
    $targetPath = $entry.Value
    $linkPath = Join-Path $projectRoot $linkName

    if (-not (Test-Path $targetPath)) {
        Write-Host ("[WARN] Target not found for {0}: {1}" -f $linkName, $targetPath) -ForegroundColor Yellow
        continue
    }

    if (Test-Path $linkPath) {
        $existing = Get-Item $linkPath -Force
        if ($existing -is [System.IO.DirectoryInfo] -and $existing.Attributes -band [IO.FileAttributes]::ReparsePoint) {
            $existingTarget = $existing | Select-Object -ExpandProperty Target -ErrorAction SilentlyContinue
            if ([string]::IsNullOrEmpty($existingTarget)) {
                $existingTarget = $existing.Target
            }

            if (-not [string]::IsNullOrEmpty($existingTarget)) {
                $existingTargetFull = [System.IO.Path]::GetFullPath($existingTarget)
                $targetFull = [System.IO.Path]::GetFullPath($targetPath)
                if ($existingTargetFull -ieq $targetFull) {
                    Write-Host ("[OK] Link {0} already points to {1}" -f $linkName, $targetPath) -ForegroundColor Yellow
                    continue
                }
            }
        }

        if (-not $Force) {
            Write-Host ("[WARN] {0} exists; rerun with -Force to replace." -f $linkName) -ForegroundColor Yellow
            continue
        }

        Remove-Item $linkPath -Recurse -Force
    }

    try {
        New-Item -ItemType Junction -Path $linkPath -Target $targetPath -Force | Out-Null
        Write-Host ("[OK] Linked {0} -> {1}" -f $linkName, $targetPath) -ForegroundColor Green
    } catch {
        Write-Host ("[ERR] Failed to link {0}: {1}" -f $linkName, $_.Exception.Message) -ForegroundColor Red
    }
}

$globalRulesPath = $expectedTargets["Global-Rules"]
if (-not (Test-Path $globalRulesPath)) {
    Write-Host "Global rules directory not found: $globalRulesPath" -ForegroundColor Red
    exit 1
}

$globalCursorRules = Join-Path $globalRulesPath "befreefitness-mobile-app.cursorrules"
$localCursorRules = Join-Path $projectRoot ".cursorrules"

if (Test-Path $globalCursorRules) {
    $copyRules = $Force
    if (-not $copyRules -and -not (Test-Path $localCursorRules)) {
        $copyRules = $true
    }
    if (-not $copyRules) {
        $globalInfo = Get-Item $globalCursorRules
        $localInfo = Get-Item $localCursorRules -ErrorAction SilentlyContinue
        if ($null -eq $localInfo -or $globalInfo.LastWriteTime -gt $localInfo.LastWriteTime) {
            $copyRules = $true
        }
    }

    if ($copyRules) {
        Copy-Item $globalCursorRules $localCursorRules -Force
        Write-Host "[OK] Synced .cursorrules" -ForegroundColor Green
    } else {
        Write-Host "[OK] .cursorrules is up to date" -ForegroundColor Yellow
    }
} else {
    Write-Host "[WARN] Global .cursorrules not found" -ForegroundColor Yellow
}

$globalCursorSettings = Join-Path $globalRulesPath "befreefitness-mobile-app.cursor-settings.json"
$localCursorSettings = Join-Path $projectRoot ".cursor-settings.json"

if (Test-Path $globalCursorSettings) {
    $copySettings = $Force
    if (-not $copySettings -and -not (Test-Path $localCursorSettings)) {
        $copySettings = $true
    }
    if (-not $copySettings) {
        $globalSettingsInfo = Get-Item $globalCursorSettings
        $localSettingsInfo = Get-Item $localCursorSettings -ErrorAction SilentlyContinue
        if ($null -eq $localSettingsInfo -or $globalSettingsInfo.LastWriteTime -gt $localSettingsInfo.LastWriteTime) {
            $copySettings = $true
        }
    }

    if ($copySettings) {
        Copy-Item $globalCursorSettings $localCursorSettings -Force
        Write-Host "[OK] Synced .cursor-settings.json" -ForegroundColor Green
    } else {
        Write-Host "[OK] .cursor-settings.json is up to date" -ForegroundColor Yellow
    }
} else {
    Write-Host "[WARN] Global .cursor-settings.json not found" -ForegroundColor Yellow
}

Write-Host "Global resources sync completed!" -ForegroundColor Green

