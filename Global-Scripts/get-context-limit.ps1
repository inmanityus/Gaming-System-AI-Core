# Get Context Limit for Current Model
# This script detects the current Cursor model and returns the appropriate context limit

param(
    [string]$ModelName = ""
)

# Model context sizes (90% of total)
$contextSizes = @{
    "Composer 1" = 180000
    "Claude 4.5 Sonnet" = 180000
    "Claude 4.1 Opus" = 180000
    "GPT-5.1 Codex High" = 244800
    "GPT-5.1" = 244800
    "GPT-5 Pro" = 244800
    "Gemini 2.5 Pro" = 180000
    "DeepSeek V3.1" = 115200
    "Grok Code" = 230400
    "Grok 4" = 230400
}

# Function to detect current model
function Get-CursorModel {
    # Check environment variables
    $envModel = $env:CURSOR_MODEL_NAME
    if ($envModel) {
        return $envModel
    }
    
    # Check cursor config files
    $cursorConfig = Join-Path $env:USERPROFILE ".cursor/config.json"
    if (Test-Path $cursorConfig) {
        try {
            $config = Get-Content $cursorConfig -Raw | ConvertFrom-Json
            if ($config.currentModel) {
                return $config.currentModel
            }
        } catch {
            # Config parsing failed
        }
    }
    
    # Check session marker
    $sessionMarker = Join-Path (Get-Location) ".cursor/session-model.txt"
    if (Test-Path $sessionMarker) {
        $model = Get-Content $sessionMarker -Raw
        if ($model) {
            return $model.Trim()
        }
    }
    
    return $null
}

# Main logic
if ($ModelName) {
    # Model explicitly provided
    $currentModel = $ModelName
} else {
    # Try to detect model
    $currentModel = Get-CursorModel
}

if ($currentModel -and $contextSizes.ContainsKey($currentModel)) {
    $limit = $contextSizes[$currentModel]
    Write-Host "✅ Model: $currentModel" -ForegroundColor Green
    Write-Host "✅ Context Limit: $($limit.ToString('N0')) tokens (90% of total)" -ForegroundColor Green
    
    # Write to session file for future reference
    $sessionDir = Join-Path (Get-Location) ".cursor"
    if (-not (Test-Path $sessionDir)) {
        New-Item -ItemType Directory -Path $sessionDir -Force | Out-Null
    }
    Set-Content -Path (Join-Path $sessionDir "session-model.txt") -Value $currentModel
    Set-Content -Path (Join-Path $sessionDir "context-limit.txt") -Value $limit
    
    return $limit
} else {
    Write-Host "❌ Cannot determine model or model not found in context size table" -ForegroundColor Red
    Write-Host ""
    Write-Host "Available models:" -ForegroundColor Yellow
    foreach ($model in $contextSizes.Keys | Sort-Object) {
        Write-Host "  - $model" -ForegroundColor White
    }
    Write-Host ""
    Write-Host "Please specify your model:" -ForegroundColor Yellow
    Write-Host "  pwsh -File Global-Scripts/get-context-limit.ps1 -ModelName 'ModelName'" -ForegroundColor Cyan
    
    # Return conservative default
    return 115200  # Smallest context size as safe default
}
