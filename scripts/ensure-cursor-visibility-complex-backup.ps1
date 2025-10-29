param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path $scriptDir -Parent
$timestamp = Get-Date

$markerPath = Join-Path $projectRoot ".cursor\ai-logs\visibility-marker.json"
$aiLogsDir = Split-Path $markerPath -Parent

function Clear-HiddenAttribute {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return }
    $item = Get-Item $Path -Force
    if ($item.Attributes -band [IO.FileAttributes]::Hidden) {
        $item.Attributes = $item.Attributes -bxor [IO.FileAttributes]::Hidden
    }
}

function Try-GetLinkTarget {
    param([System.IO.FileSystemInfo]$Item)
    if ($null -eq $Item) { return $null }
    foreach ($propName in @("Target", "LinkTarget")) {
        if ($Item.PSObject.Properties.Name -contains $propName) {
            $value = $Item.$propName
            if ($value) { return $value }
        }
    }
    try {
        return $Item.GetLinkTarget()
    } catch {
        return $null
    }
}

function Ensure-Link {
    param(
        [string]$Label,
        [string]$LinkPath,
        [string]$TargetPath,
        [switch]$ForceLink
    )

    if (-not (Test-Path $TargetPath)) {
        Write-Host "[VISIBILITY] Missing target for ${Label}: $TargetPath" -ForegroundColor Yellow
        return [pscustomobject]@{
            label = $Label
            link = $LinkPath
            target = $TargetPath
            status = "target-missing"
        }
    }

    $targetFull = [System.IO.Path]::GetFullPath($TargetPath)

    if (Test-Path $LinkPath) {
        $existing = Get-Item $LinkPath -Force
        $isLink = $existing.Attributes -band [IO.FileAttributes]::ReparsePoint
        $existingTarget = $null
        if ($isLink) {
            $existingTarget = Try-GetLinkTarget -Item $existing
        }

        if ($existingTarget) {
            $existingFull = [System.IO.Path]::GetFullPath($existingTarget)
            if ($existingFull -ieq $targetFull) {
                return [pscustomobject]@{
                    label = $Label
                    link = $LinkPath
                    target = $targetFull
                    status = "unchanged"
                }
            }
        }

        if ($isLink -or $ForceLink) {
            try {
                Remove-Item -Recurse -Force $LinkPath
            } catch {
                Write-Host "[VISIBILITY] Failed to remove existing ${Label}: $($_.Exception.Message)" -ForegroundColor Red
                return [pscustomobject]@{
                    label = $Label
                    link = $LinkPath
                    target = $targetFull
                    status = "error"
                    message = $_.Exception.Message
                }
            }
        } else {
            Write-Host "[VISIBILITY] Skipping $Label because it already exists. Use -Force to replace." -ForegroundColor Yellow
            return [pscustomobject]@{
                label = $Label
                link = $LinkPath
                target = $targetFull
                status = "skipped"
            }
        }
    }

    $parentDir = Split-Path $LinkPath -Parent
    if ($parentDir -and -not (Test-Path $parentDir)) {
        New-Item -ItemType Directory -Force -Path $parentDir | Out-Null
    }

    try {
        New-Item -ItemType Junction -Path $LinkPath -Target $TargetPath | Out-Null
        Write-Host "[VISIBILITY] Linked ${Label} -> $targetFull" -ForegroundColor Green
        return [pscustomobject]@{
            label = $Label
            link = $LinkPath
            target = $targetFull
            status = "linked"
        }
    } catch {
        Write-Host "[VISIBILITY] Failed to link ${Label}: $($_.Exception.Message)" -ForegroundColor Red
        return [pscustomobject]@{
            label = $Label
            link = $LinkPath
            target = $targetFull
            status = "error"
            message = $_.Exception.Message
        }
    }
}


function Invoke-StartupScript {
    param(
        [string]$Name,
        [string]$ScriptPath
    )

    if (-not (Test-Path $ScriptPath)) {
        Write-Host "[VISIBILITY] Startup script $Name missing at $ScriptPath" -ForegroundColor Yellow
        return [pscustomobject]@{
            name = $Name
            path = $ScriptPath
            status = "missing"
            exitCode = $null
            output = @()
        }
    }

    $command = "& powershell -NoProfile -ExecutionPolicy Bypass -File `"$ScriptPath`""
    $output = & powershell -NoProfile -ExecutionPolicy Bypass -Command $command 2>&1
    $exitCode = $LASTEXITCODE

    if ($exitCode -eq 0) {
        Write-Host "[VISIBILITY] Startup script $Name completed." -ForegroundColor Green
    } else {
        Write-Host "[VISIBILITY] Startup script $Name exited with code $exitCode" -ForegroundColor Yellow
    }

    return [pscustomobject]@{
        name = $Name
        path = $ScriptPath
        status = if ($exitCode -eq 0) { "ok" } else { "error" }
        exitCode = $exitCode
        output = @($output | ForEach-Object { $_.ToString() })
    }
}

function Test-ProgressionRule {
    param([string]$WorkflowPath)

    if (-not (Test-Path $WorkflowPath)) {
        Write-Host "[VISIBILITY] Progression rule check: workflow file missing at $WorkflowPath" -ForegroundColor Yellow
        return [pscustomobject]@{
            workflowPath = $WorkflowPath
            status = "missing"
            details = "workflow not found"
        }
    }

    $content = Get-Content $WorkflowPath -Raw
    if ($content -match "Progression Rule") {
        Write-Host "[VISIBILITY] Progression rule found in Project-Workflow." -ForegroundColor Green
        return [pscustomobject]@{
            workflowPath = $WorkflowPath
            status = "ok"
            details = "contains Progression Rule"
        }
    }

    Write-Host "[VISIBILITY] Progression rule NOT found in Project-Workflow." -ForegroundColor Yellow
    return [pscustomobject]@{
        workflowPath = $WorkflowPath
        status = "not-found"
        details = "keyword missing"
    }
}

$summary = $null

try {
    $homePath = $env:USERPROFILE
    if ([string]::IsNullOrEmpty($homePath)) {
        $homePath = $env:HOME
    }
    if ([string]::IsNullOrEmpty($homePath)) {
        throw "Unable to determine user home directory."
    }

    $globalFolder = Join-Path $homePath ".cursor"
    $env:GLOBAL_FOLDER = $globalFolder
    [Environment]::SetEnvironmentVariable("GLOBAL_FOLDER", $globalFolder, "Process")

    $env:PROJECT_ROOT = $projectRoot
    [Environment]::SetEnvironmentVariable("PROJECT_ROOT", $projectRoot, "Process")

    $globalRepo = Join-Path $globalFolder "global-cursor-repo"
    $globalRepoExists = Test-Path $globalRepo

    if (-not (Test-Path $aiLogsDir)) {
        New-Item -ItemType Directory -Force -Path $aiLogsDir | Out-Null
    }

    $cursorDir = Join-Path $projectRoot ".cursor"
    if (-not (Test-Path $cursorDir)) {
        New-Item -ItemType Directory -Force -Path $cursorDir | Out-Null
    }
    Clear-HiddenAttribute -Path $cursorDir

    $projectScriptsDir = Join-Path $projectRoot "scripts"
    if (-not (Test-Path $projectScriptsDir)) {
        New-Item -ItemType Directory -Force -Path $projectScriptsDir | Out-Null
    }
    Clear-HiddenAttribute -Path $projectScriptsDir

    foreach ($path in @("Global-Rules", "Global-Scripts", "Global-Workflows", "Global-Utils")) {
        $fullPath = Join-Path $projectRoot $path
        if (Test-Path $fullPath) {
            Clear-HiddenAttribute -Path $fullPath
        }
    }

    $cursorLinkResults = @()
    $cursorMappings = @(
        @{ Label = ".cursor\\rules"; Link = Join-Path $cursorDir "rules"; Target = Join-Path $globalRepo "rules"; ForceLink = $true },
        @{ Label = ".cursor\\workflows"; Link = Join-Path $cursorDir "workflows"; Target = Join-Path $globalRepo "workflows"; ForceLink = $true },
        @{ Label = ".cursor\\scripts"; Link = Join-Path $cursorDir "scripts"; Target = Join-Path $globalRepo "scripts"; ForceLink = $true },
        @{ Label = ".cursor\\utils"; Link = Join-Path $cursorDir "utils"; Target = Join-Path $globalRepo "utils"; ForceLink = $true }
    )

    foreach ($map in $cursorMappings) {
        $result = Ensure-Link -Label $map.Label -LinkPath $map.Link -TargetPath $map.Target -ForceLink:($map.ForceLink)
        $cursorLinkResults += $result
        if ($result.status -ne "target-missing" -and $result.status -ne "error") {
            Clear-HiddenAttribute -Path $map.Link
        }
    }

    $topLevelLinkResults = @()
    $topMappings = @(
        @{ Label = "Global-Rules"; Link = Join-Path $projectRoot "Global-Rules"; Target = Join-Path $globalRepo "rules"; ForceLink = $Force },
        @{ Label = "Global-Scripts"; Link = Join-Path $projectRoot "Global-Scripts"; Target = Join-Path $globalRepo "scripts"; ForceLink = $Force },
        @{ Label = "Global-Workflows"; Link = Join-Path $projectRoot "Global-Workflows"; Target = Join-Path $globalRepo "workflows"; ForceLink = $Force },
        @{ Label = "Global-Utils"; Link = Join-Path $projectRoot "Global-Utils"; Target = Join-Path $globalRepo "utils"; ForceLink = $Force }
    )

    foreach ($map in $topMappings) {
        $result = Ensure-Link -Label $map.Label -LinkPath $map.Link -TargetPath $map.Target -ForceLink:($map.ForceLink)
        $topLevelLinkResults += $result
        if (Test-Path $map.Link) {
            Clear-HiddenAttribute -Path $map.Link
        }
    }

    $cursorRulesPath = Join-Path $cursorDir "rules"
    $cursorRulesHaveMdc = $false
    if (Test-Path $cursorRulesPath) {
        $cursorRulesHaveMdc = @(Get-ChildItem $cursorRulesPath -Filter *.mdc -ErrorAction SilentlyContinue).Count -gt 0
        if (-not $cursorRulesHaveMdc) {
            Write-Host "[VISIBILITY] .cursor\\rules has no .mdc files. Ensure global rules repository is synced." -ForegroundColor Yellow
        }
    }

    $startupResults = @()

    $workflowPath = Join-Path $projectRoot "Project-Management\Project-Workflow.md"
    $progressionCheck = Test-ProgressionRule -WorkflowPath $workflowPath

    $summary = [ordered]@{
        lastRun = $timestamp.ToString("o")
        projectRoot = $projectRoot
        globalFolder = $globalFolder
        globalRepo = $globalRepo
        globalRepoFound = $globalRepoExists
        cursorLinks = $cursorLinkResults
        topLevelLinks = $topLevelLinkResults
        cursorRulesHaveMdc = $cursorRulesHaveMdc
        progressionRule = $progressionCheck
    }

    $startupScriptSpecs = @(
        @{ name = "setup-watchdog-wrapper"; path = Join-Path $globalRepo "scripts\setup-watchdog-wrapper.ps1" },
        @{ name = "ensure-progression-rule"; path = Join-Path $globalRepo "scripts\ensure-progression-rule.ps1" }
    )

    foreach ($spec in $startupScriptSpecs) {
        $startupResults += Invoke-StartupScript -Name $spec.name -ScriptPath $spec.path
    }

    $summary.startupScripts = $startupResults

    $summary | ConvertTo-Json -Depth 6 | Set-Content -Path $markerPath -Encoding UTF8
} catch {
    Write-Host "[VISIBILITY] Unexpected error: $($_.Exception.Message)" -ForegroundColor Red
    if (-not (Test-Path $aiLogsDir)) {
        New-Item -ItemType Directory -Force -Path $aiLogsDir | Out-Null
    }
    $errorSummary = [ordered]@{
        lastRun = $timestamp.ToString("o")
        projectRoot = $projectRoot
        error = $_.Exception.Message
        stack = $_.ScriptStackTrace
    }
    $errorSummary | ConvertTo-Json -Depth 4 | Set-Content -Path $markerPath -Encoding UTF8
}

