# Minimum Model Level Enforcement Feature
# This feature loads and enforces minimum model level requirements

function Initialize-MinimumModelLevels {
    Write-Host ""
    Write-Host "Loading Minimum Model Level Rules..." -ForegroundColor Yellow
    $minModelRules = "Global-Workflows\minimum-model-levels.md"
    if (Test-Path $minModelRules) {
        Write-Host "[OK] Minimum model level rules found: $minModelRules" -ForegroundColor Green
        
        # Read the file to extract actual minimums
        $minModelContent = Get-Content $minModelRules -Raw
        Write-Host "[CRITICAL] Model Selection Requirements:" -ForegroundColor Cyan
        
        # Extract minimums from file content
        if ($minModelContent -match "Claude.*?Minimum:.*?([4-9]\.[0-9]+)") {
            $claudeMin = $matches[1]
            Write-Host "  - Claude: Minimum $claudeMin Sonnet/Opus" -ForegroundColor White
        } else {
            Write-Host "  - Claude: Minimum 4.5 Sonnet, 4.1 Opus" -ForegroundColor White
        }
        
        if ($minModelContent -match "GPT.*?Minimum:.*?([4-9])") {
            $gptMin = $matches[1]
            Write-Host "  - GPT: Minimum $gptMin or $gptMin-Pro (NO GPT-4.x allowed)" -ForegroundColor White
        } else {
            Write-Host "  - GPT: Minimum 5, 5-Pro (NO GPT-4.x allowed)" -ForegroundColor White
        }
        
        if ($minModelContent -match "Gemini.*?Minimum:.*?([0-9]\.[0-9]+)") {
            $geminiMin = $matches[1]
            Write-Host "  - Gemini: Minimum $geminiMin Pro" -ForegroundColor White
        } else {
            Write-Host "  - Gemini: Minimum 2.5 Pro" -ForegroundColor White
        }
        
        if ($minModelContent -match "DeepSeek.*?Minimum:.*?([0-9]\.[0-9]+)") {
            $deepseekMin = $matches[1]
            Write-Host "  - DeepSeek: Minimum $deepseekMin Terminus/R1" -ForegroundColor White
        } else {
            Write-Host "  - DeepSeek: Minimum 3.1 Terminus" -ForegroundColor White
        }
        
        Write-Host ""
        Write-Host "[ENFORCEMENT] When using OpenRouter AI or switching models:" -ForegroundColor Yellow
        Write-Host "  - ALWAYS verify model meets minimum requirements" -ForegroundColor White
        Write-Host "  - NEVER use older generations below minimum" -ForegroundColor White
        Write-Host "  - ALWAYS check Global-Workflows/minimum-model-levels.md before selection" -ForegroundColor White
        Write-Host "  - Use OpenRouter search_models to verify availability" -ForegroundColor White
        Write-Host "  - Reference file: $minModelRules" -ForegroundColor Gray
    } else {
        Write-Host "[ERROR] Minimum model level rules NOT FOUND: $minModelRules" -ForegroundColor Red
        Write-Host "        Model selection enforcement DISABLED" -ForegroundColor Red
        Write-Host "        This may result in using older, inferior models" -ForegroundColor Yellow
        Write-Host "        ACTION REQUIRED: Verify Global-Workflows junction exists" -ForegroundColor Yellow
    }
}

