# Occupied Ports Check - Startup Feature
# Prevents port conflicts by checking Global-Docs/Occupied-Ports.md before allocating ports

$FEATURE_NAME = "occupied-ports-check"

Write-Host "[PORTS] Initializing Occupied Ports Check..." -ForegroundColor Cyan
Write-Host "PROTECTIVE RATIONALE: Prevents port conflicts across all projects" -ForegroundColor DarkGray
Write-Host "by requiring port availability verification before service startup" -ForegroundColor DarkGray

# Check if Global-Docs/Occupied-Ports.md exists
$occupiedPortsFile = Join-Path $ROOT_DIR "Global-Docs\Occupied-Ports.md"

if (Test-Path $occupiedPortsFile) {
    Write-Host "[OK] Occupied ports registry found: Global-Docs\Occupied-Ports.md" -ForegroundColor Green
    
    # Create port check rule
    $portCheckRule = @"
# Occupied Ports Check - MANDATORY RULE

**CRITICAL**: Before starting ANY server or service, you MUST check ``Global-Docs/Occupied-Ports.md``

## Port Allocation Rules

1. **Check Occupied-Ports.md FIRST** before selecting any port
2. **Minimum Spacing**: 10 ports between any two application servers
3. **Update Immediately**: Add your port to Occupied-Ports.md when claiming it
4. **Reserved Ranges**: Respect Windows system services (135, 139, 445, 49664-50000)
5. **Infrastructure Ports**: Docker (8000), PostgreSQL (5432, 5443)

## Current Occupied Ports

**Frontend (Node.js/Next.js)**:
- 3000: Be Free Fitness Frontend
- 3010: Drone Sentinels Frontend

**Backend (Node/Python)**:
- 4000: Be Free Fitness API
- 8000: Docker infrastructure (PROTECTED)
- 8010: Body Broker QA Orchestrator

**Database**:
- 5432: PostgreSQL primary
- 5443: PostgreSQL (Gaming System AI Core)

**Infrastructure**:
- 6379: Redis
- 3001-3002: Docker backend

## Available Port Ranges

- Frontend: 3020+ (Node.js/Next.js apps)
- Backend: 4010+ (Node.js APIs)
- Python/FastAPI: 8020+ (Python services)
- Custom: 9000-9999, 10000+

## Before Starting Server

``````powershell
# 1. Check Global-Docs/Occupied-Ports.md
Get-Content "Global-Docs\Occupied-Ports.md"

# 2. Verify port is available (10+ ports away from occupied)
# 3. Update Occupied-Ports.md with your port
# 4. Start your server
``````

**VIOLATION CONSEQUENCE**: Port conflicts cause service failures and difficult debugging.

**Reference**: ``Global-Docs/Occupied-Ports.md``
"@

    $ruleFile = Join-Path $ROOT_DIR ".cursor\occupied-ports-check-rules.md"
    $portCheckRule | Out-File -FilePath $ruleFile -Encoding UTF8 -Force
    Write-Host "[OK] Port check rules saved: .cursor\occupied-ports-check-rules.md" -ForegroundColor Green
    
    Write-Host ""
    Write-Host "[PORTS] Occupied Ports Check initialized" -ForegroundColor Green
    Write-Host "         Rules file: .cursor\occupied-ports-check-rules.md" -ForegroundColor DarkGray
    Write-Host "         Registry: Global-Docs\Occupied-Ports.md" -ForegroundColor DarkGray
    Write-Host "         Status: Active - port check MANDATORY before server startup" -ForegroundColor DarkGray
} else {
    Write-Host "[WARN] Occupied ports registry not found: Global-Docs\Occupied-Ports.md" -ForegroundColor Yellow
    Write-Host "         Port conflicts may occur without registry" -ForegroundColor DarkGray
}

Write-Host "[OK] Feature '$FEATURE_NAME' initialized successfully" -ForegroundColor Green

