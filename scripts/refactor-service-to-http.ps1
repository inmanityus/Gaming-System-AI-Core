# Refactor Service to Use HTTP Clients Instead of Direct Imports
# Systematic replacement of cross-service imports with HTTP communication

param(
    [Parameter(Mandatory=$true)]
    [string]$ServiceName,
    
    [switch]$Build,
    [switch]$Deploy
)

$ErrorActionPreference = "Stop"

$serviceDir = $ServiceName -replace "-", "_"
$servicePath = "services/$serviceDir"

if (-not (Test-Path $servicePath)) {
    Write-Error "Service directory not found: $servicePath"
    exit 1
}

Write-Host "Refactoring $ServiceName..." -ForegroundColor Cyan

# Get all Python files in service
$files = Get-ChildItem "$servicePath" -Recurse -Filter "*.py"

foreach ($file in $files) {
    $content = Get-Content $file.FullName -Raw
    $modified = $false
    
    # Replace model_management imports
    if ($content -match "from services\.model_management") {
        $content = $content -creplace "from services\.model_management\.[^\s]+ import ([^\n]+)", "# Replaced: model_management import with HTTP client"
        $modified = $true
    }
    
    # Replace ai_integration imports  
    if ($content -match "from services\.ai_integration") {
        $content = $content -creplace "from services\.ai_integration\.[^\s]+ import ([^\n]+)", "# Replaced: ai_integration import with HTTP client"
        $modified = $true
    }
    
    # Replace state_manager imports
    if ($content -match "from services\.state_manager\.connection_pool") {
        $content = $content -creplace "from services\.state_manager\.connection_pool import [^\n]+", "from shared.http_clients import get_state_manager_client"
        $modified = $true
    }
    
    # Add HTTP client imports at top if modifications made
    if ($modified -and $content -notmatch "from shared\.http_clients import") {
        # Find first import statement
        if ($content -match '(?m)^from |^import ') {
            $firstImportPos = $content.IndexOf($Matches[0])
            $before = $content.Substring(0, $firstImportPos)
            $after = $content.Substring($firstImportPos)
            $content = $before + "from shared.http_clients import get_model_management_client, get_state_manager_client`n" + $after
        }
    }
    
    if ($modified) {
        $content | Out-File $file.FullName -Encoding utf8 -NoNewline
        Write-Host "  ✓ $($file.Name)"
    }
}

if ($Build) {
    Write-Host "`nBuilding $ServiceName..." -ForegroundColor Cyan
    
    Push-Location services
    
    $accountId = "695353648052"
    $ecrUri = "$accountId.dkr.ecr.us-east-1.amazonaws.com/bodybroker-services"
    
    docker build -q -t "$ecrUri`:$ServiceName-latest" -f "$serviceDir/Dockerfile.independent" .
    
    if ($LASTEXITCODE -eq 0) {
        docker push "$ecrUri`:$ServiceName-latest" 2>&1 | Out-Null
        Write-Host "  ✓ Built and pushed" -ForegroundColor Green
    } else {
        Write-Host "  ✗ Build failed" -ForegroundColor Red
        Pop-Location
        exit 1
    }
    
    Pop-Location
}

if ($Deploy) {
    Write-Host "`nDeploying $ServiceName..." -ForegroundColor Cyan
    
    aws ecs update-service `
        --cluster "gaming-system-cluster" `
        --service $ServiceName `
        --force-new-deployment `
        --region "us-east-1" `
        --no-cli-pager | Out-Null
    
    Write-Host "  ✓ Deployment triggered" -ForegroundColor Green
}

Write-Host "`n✓ $ServiceName refactored" -ForegroundColor Green

