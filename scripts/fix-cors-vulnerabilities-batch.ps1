# Batch Fix: CORS Vulnerabilities Across 12 Services
# Issue #19: CRITICAL - allow_origins=['*'] on 12 services
# Coder: Claude Sonnet 4.5
# Reviewer: GPT-Codex-2 (Pending)

$services = @(
    "services\language_system\api\server.py",
    "services\story_teller\server.py",
    "services\world_state\server.py",
    "services\settings\server.py",
    "services\router\server.py",
    "services\npc_behavior\server.py",
    "services\feedback\api\server.py",
    "services\capability-registry\main.py",
    "services\payment\server.py",
    "services\orchestration\server.py",
    "services\srl_rlvr_training\api\server.py",
    "services\quest_system\server.py",
    "services\state_manager\server.py"
)

$fixPattern = @'
allow_origins=\[".*"\],
'@

$replacement = @'
allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:5000").split(","),
'@

Write-Host "🔒 Fixing CORS vulnerabilities in 12 services..."

$fixed = 0
$failed = 0

foreach ($service in $services) {
    if (Test-Path $service) {
        Write-Host "  Fixing: $service"
        
        try {
            $content = Get-Content $service -Raw
            
            # Check if already has proper CORS
            if ($content -match 'allow_origins=\["\*"\]') {
                # Needs fix - add import if not present
                if ($content -notmatch "^import os" -and $content -notmatch "\nimport os") {
                    # Add import after first import block
                    $content = $content -replace '(from fastapi\.middleware\.cors import CORSMiddleware)', "`$1`nimport os"
                }
                
                # Fix CORS
                $content = $content -replace 'allow_origins=\["\*"\]', 'allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")'
                
                Set-Content -Path $service -Value $content -NoNewline
                Write-Host "    ✅ Fixed" -ForegroundColor Green
                $fixed++
            } else {
                Write-Host "    ℹ️ Already secure or different pattern" -ForegroundColor Cyan
            }
        } catch {
            Write-Host "    ❌ Error: $_" -ForegroundColor Red
            $failed++
        }
    } else {
        Write-Host "  ⚠️ File not found: $service" -ForegroundColor Yellow
    }
}

Write-Host "`n📊 Results:"
Write-Host "  Fixed: $fixed"
Write-Host "  Failed: $failed"
Write-Host "  Total: $($services.Count)"

if ($failed -eq 0) {
    Write-Host "`n✅ All CORS vulnerabilities fixed!" -ForegroundColor Green
} else {
    Write-Host "`n⚠️ Some services failed - review manually" -ForegroundColor Yellow
}

