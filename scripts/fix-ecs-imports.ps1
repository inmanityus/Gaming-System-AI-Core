# Fix ECS Service Import Issues
# Fixes import statements to work with flat Docker structure

param(
    [string]$AWSRegion = "us-east-1",
    [string]$ECRRepository = "bodybroker-services"
)

$ErrorActionPreference = "Stop"

Write-Host "=== FIXING ECS SERVICE IMPORTS ===" -ForegroundColor Cyan

# Get AWS account ID
$accountId = aws sts get-caller-identity --region $AWSRegion --query Account --output text
$ecrUri = "$accountId.dkr.ecr.$AWSRegion.amazonaws.com/$ECRRepository"

# Services that need import fixes
$importFixes = @{
    "model_management" = @{
        "file" = "services\model_management\server.py"
        "old" = "from services.model_management.api_routes import router"
        "new" = "from api_routes import router"
    }
    "quest_system" = @{
        "file" = "services\quest_system\server.py"
        "old" = "from .api_routes import router"
        "new" = "from api_routes import router"
    }
    "payment" = @{
        "file" = "services\payment\server.py"
        "old" = "from .api_routes import router"
        "new" = "from api_routes import router"
    }
    "performance_mode" = @{
        "file" = "services\performance_mode\server.py"
        "old" = "from services.performance_mode import api_routes"
        "new" = "import api_routes"
    }
    "environmental_narrative" = @{
        "file" = "services\environmental_narrative\server.py"
        "old" = "from services.environmental_narrative import api_routes"
        "new" = "import api_routes"
    }
}

# Fix router requirements.txt - add missing httpx
Write-Host "`n[FIX] Adding httpx to router requirements..." -ForegroundColor White
$routerReqs = Get-Content "services\router\requirements.txt" -Raw
if ($routerReqs -notmatch "httpx") {
    Add-Content "services\router\requirements.txt" "httpx>=0.24.0"
    Write-Host "[OK] Added httpx to router requirements" -ForegroundColor Green
}

# Apply import fixes
foreach ($service in $importFixes.Keys) {
    $fix = $importFixes[$service]
    $file = $fix["file"]
    
    if (Test-Path $file) {
        Write-Host "`n[FIX] Fixing imports in $service..." -ForegroundColor White
        
        $content = Get-Content $file -Raw
        if ($content -match [regex]::Escape($fix["old"])) {
            $content = $content -replace [regex]::Escape($fix["old"]), $fix["new"]
            $content | Out-File $file -Encoding utf8 -NoNewline
            Write-Host "[OK] Fixed imports in $service" -ForegroundColor Green
        } else {
            Write-Host "[SKIP] $service already fixed or pattern not found" -ForegroundColor Yellow
        }
    }
}

# Fix language-system separately (complex nested structure)
Write-Host "`n[FIX] Fixing language-system structure..." -ForegroundColor White

# Fix Dockerfile CMD to use correct module path
$langDockerfile = "services\language_system\Dockerfile"
if (Test-Path $langDockerfile) {
    $content = Get-Content $langDockerfile -Raw
    if ($content -match 'CMD \["python", "-m", "uvicorn", "server:app"') {
        $content = $content -replace 'CMD \["python", "-m", "uvicorn", "server:app"', 'CMD ["python", "-m", "uvicorn", "api.server:app"'
        $content | Out-File $langDockerfile -Encoding utf8 -NoNewline
        Write-Host "[OK] Fixed language-system Dockerfile CMD" -ForegroundColor Green
    }
}

# Fix all relative imports in language_system to be absolute
$langFiles = Get-ChildItem "services\language_system" -Recurse -Filter "*.py"
foreach ($file in $langFiles) {
    $content = Get-Content $file.FullName -Raw
    $modified = $false
    
    # Fix relative imports to be absolute from package root
    if ($content -match "from \.\.") {
        $content = $content -replace "from \.\.generation\.", "from generation."
        $content = $content -replace "from \.\.translation\.", "from translation."
        $content = $content -replace "from \.\.core\.", "from core."
        $content = $content -replace "from \.\.integration\.", "from integration."
        $content = $content -replace "from \.\.gameplay\.", "from gameplay."
        $content = $content -replace "from \.\.data\.", "from data."
        $modified = $true
    }
    
    if ($content -match "from \.") {
        $dir = $file.Directory.Name
        if ($dir -ne "language_system") {
            $content = $content -replace "from \.", "from $dir."
            $modified = $true
        }
    }
    
    if ($modified) {
        $content | Out-File $file.FullName -Encoding utf8 -NoNewline
    }
}
Write-Host "[OK] Fixed language-system imports" -ForegroundColor Green

# Login to ECR
Write-Host "`n[ECR] Logging in..." -ForegroundColor White
aws ecr get-login-password --region $AWSRegion | docker login --username AWS --password-stdin $ecrUri | Out-Null

# Services to rebuild
$servicesToRebuild = @(
    @{name="model-management"; dir="model_management"},
    @{name="quest-system"; dir="quest_system"},
    @{name="payment"; dir="payment"},
    @{name="performance-mode"; dir="performance_mode"},
    @{name="router"; dir="router"},
    @{name="environmental-narrative"; dir="environmental_narrative"},
    @{name="language-system"; dir="language_system"}
)

# Rebuild and push images
foreach ($svc in $servicesToRebuild) {
    $name = $svc.name
    $dir = $svc.dir
    
    Write-Host "`n[BUILD] $name..." -ForegroundColor Cyan
    
    Push-Location services
    try {
        $imageTag = "$ecrUri`:$dir-latest"
        
        docker build --no-cache -t $imageTag -f "$dir\Dockerfile" . 2>&1 | Out-Null
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[PUSH] $name..." -ForegroundColor White
            docker push $imageTag 2>&1 | Out-Null
            
            if ($LASTEXITCODE -eq 0) {
                Write-Host "[OK] $name deployed" -ForegroundColor Green
            } else {
                Write-Host "[ERROR] Push failed for $name" -ForegroundColor Red
            }
        } else {
            Write-Host "[ERROR] Build failed for $name" -ForegroundColor Red
        }
    }
    finally {
        Pop-Location
    }
}

# Force redeploy all services
Write-Host "`n[REDEPLOY] Forcing service updates..." -ForegroundColor Cyan
foreach ($svc in $servicesToRebuild) {
    aws ecs update-service --cluster gaming-system-cluster --service $svc.name --force-new-deployment --region $AWSRegion --no-cli-pager | Out-Null
}

Write-Host "`n[WAIT] Waiting 2 minutes for services to start..." -ForegroundColor White
Start-Sleep -Seconds 120

# Check status
Write-Host "`n[STATUS] Checking service status..." -ForegroundColor Cyan
$serviceNames = $servicesToRebuild | ForEach-Object { $_.name }
$result = aws ecs describe-services --cluster gaming-system-cluster --services $serviceNames --region $AWSRegion --query "services[*].[serviceName,runningCount,desiredCount]" --output text

$runningCount = 0
$failingCount = 0

$result -split "`n" | ForEach-Object {
    $parts = $_ -split "`t"
    if ($parts.Length -ge 3) {
        $svcName = $parts[0]
        $running = [int]$parts[1]
        $desired = [int]$parts[2]
        
        if ($running -eq $desired -and $running -gt 0) {
            Write-Host "[OK] $svcName : $running/$desired" -ForegroundColor Green
            $runningCount++
        } else {
            Write-Host "[FAIL] $svcName : $running/$desired" -ForegroundColor Red
            $failingCount++
        }
    }
}

Write-Host "`n=== SUMMARY ===" -ForegroundColor Cyan
Write-Host "Running: $runningCount services" -ForegroundColor Green
Write-Host "Failing: $failingCount services" -ForegroundColor $(if ($failingCount -eq 0) { "Green" } else { "Red" })

if ($failingCount -eq 0) {
    Write-Host "`n✓ ALL SERVICES HEALTHY" -ForegroundColor Green
    exit 0
} else {
    exit 1
}

