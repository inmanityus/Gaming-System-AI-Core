# Peer Coding & Pairwise Testing Enforcement Feature
# Enforces mandatory peer coding and pairwise testing rules at startup

function Initialize-PeerCodingPairwiseEnforcement {
    Write-Host ""
    Write-Host "================================================================" -ForegroundColor Cyan
    Write-Host "PEER CODING & PAIRWISE TESTING ENFORCEMENT" -ForegroundColor Cyan
    Write-Host "================================================================" -ForegroundColor Cyan
    
    Write-Host "[CRITICAL] MANDATORY RULES ACTIVE:" -ForegroundColor Red
    Write-Host "  ✅ Peer-based coding: REQUIRED for ALL code" -ForegroundColor Yellow
    Write-Host "  ✅ Pairwise testing: REQUIRED for ALL tests" -ForegroundColor Yellow
    Write-Host "  ✅ Audit trails: REQUIRED for ALL work" -ForegroundColor Yellow
    Write-Host "  ✅ Minimum model levels: ENFORCED" -ForegroundColor Yellow
    Write-Host "  ✅ Fake/mock code: FORBIDDEN" -ForegroundColor Yellow
    Write-Host ""
    
    # Ensure audit directories exist
    $auditDirs = @(
        ".cursor/audit/code",
        ".cursor/audit/tests",
        ".cursor/mappings"
    )
    
    foreach ($dir in $auditDirs) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            Write-Host "[OK] Created audit directory: $dir" -ForegroundColor Green
        } else {
            Write-Host "[OK] Audit directory exists: $dir" -ForegroundColor Green
        }
    }
    
    # Verify mapping system exists
    $mappingFile = ".cursor/mappings/requirements-to-code-mapping.md"
    if (-not (Test-Path $mappingFile)) {
        Write-Host "[WARNING] Mapping file not found: $mappingFile" -ForegroundColor Yellow
        Write-Host "          Run: pwsh -File scripts/create-mapping-system.ps1" -ForegroundColor Yellow
    } else {
        Write-Host "[OK] Mapping system found: $mappingFile" -ForegroundColor Green
    }
    
    # Verify unified requirements exist
    $unifiedReq = "docs/Requirements/UNIFIED-REQUIREMENTS.md"
    if (-not (Test-Path $unifiedReq)) {
        Write-Host "[WARNING] Unified requirements not found: $unifiedReq" -ForegroundColor Yellow
        Write-Host "          Run: pwsh -File scripts/consolidate-requirements.ps1" -ForegroundColor Yellow
    } else {
        Write-Host "[OK] Unified requirements found: $unifiedReq" -ForegroundColor Green
    }
    
    # Check minimum model levels file
    $minModelLevels = "Global-Workflows/minimum-model-levels.md"
    if (Test-Path $minModelLevels) {
        Write-Host "[OK] Minimum model levels reference found" -ForegroundColor Green
    } else {
        Write-Host "[WARNING] Minimum model levels reference not found: $minModelLevels" -ForegroundColor Yellow
    }
    
    Write-Host ""
    Write-Host "[ENFORCEMENT] All sessions MUST:" -ForegroundColor Cyan
    Write-Host "  1. Use peer-based coding for ALL code" -ForegroundColor White
    Write-Host "  2. Use pairwise testing for ALL tests" -ForegroundColor White
    Write-Host "  3. Create audit trails for ALL work" -ForegroundColor White
    Write-Host "  4. Match code to requirements in mapping system" -ForegroundColor White
    Write-Host "  5. Use only minimum-level models (Claude 4.5+, GPT-5+, Gemini 2.5+)" -ForegroundColor White
    Write-Host "  6. NEVER use fake/mock code in production paths" -ForegroundColor White
    Write-Host ""
    Write-Host "[REFERENCE] Rule file: .cursor/rules/peer-coding-pairwise-mandatory.md" -ForegroundColor Gray
    Write-Host "================================================================" -ForegroundColor Cyan
}

