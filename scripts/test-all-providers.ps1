# Test All API Providers
# Tests connectivity to all configured API providers

Write-Host "=== Testing All API Providers ===" -ForegroundColor Cyan
Write-Host ""

# Load .env if it exists
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match '^\s*([^#][^=]+)=(.*)$') {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            Set-Item -Path "env:$key" -Value $value
        }
    }
    Write-Host "[OK] Loaded .env file" -ForegroundColor Green
}

$results = @()

# Test Azure AI
Write-Host "Testing Azure AI..." -ForegroundColor Yellow
try {
    $endpoint = $env:AZURE_AI_ENDPOINT
    $apiKey = $env:AZURE_AI_API_KEY
    $deployment = "DeepSeek-V3.1"  # Start with one deployment
    
    if ($endpoint -and $apiKey) {
        $headers = @{
            "api-key" = $apiKey
            "Content-Type" = "application/json"
        }
        $body = @{
            messages = @(
                @{ role = "user"; content = "Say hello" }
            )
        } | ConvertTo-Json -Depth 10
        
        $uri = "$endpoint/openai/deployments/$deployment/chat/completions?api-version=2024-02-15-preview"
        $response = Invoke-RestMethod -Uri $uri -Method POST -Headers $headers -Body $body -ErrorAction Stop
        $results += @{Provider="Azure AI ($deployment)"; Status="✅ Success"; Details=$response.choices[0].message.content}
        Write-Host "  ✅ Azure AI ($deployment): OK" -ForegroundColor Green
    } else {
        $results += @{Provider="Azure AI"; Status="⏭️ Skipped"; Details="Missing credentials"}
        Write-Host "  ⏭️ Azure AI: Skipped (missing credentials)" -ForegroundColor Gray
    }
} catch {
    $results += @{Provider="Azure AI"; Status="❌ Failed"; Details=$_.Exception.Message}
    Write-Host "  ❌ Azure AI: Failed" -ForegroundColor Red
}

# Test OpenAI Direct
Write-Host "Testing OpenAI Direct..." -ForegroundColor Yellow
try {
    $apiKey = $env:OPENAI_API_KEY
    if ($apiKey) {
        $headers = @{
            "Authorization" = "Bearer $apiKey"
            "Content-Type" = "application/json"
        }
        $body = @{
            model = "gpt-4o-mini"
            messages = @(
                @{ role = "user"; content = "Say hello" }
            )
        } | ConvertTo-Json -Depth 10
        
        $uri = "$($env:OPENAI_BASE_URL)/chat/completions"
        if (-not $uri) { $uri = "https://api.openai.com/v1/chat/completions" }
        
        $response = Invoke-RestMethod -Uri $uri -Method POST -Headers $headers -Body $body -ErrorAction Stop
        $results += @{Provider="OpenAI Direct"; Status="✅ Success"; Details=$response.choices[0].message.content}
        Write-Host "  ✅ OpenAI Direct: OK" -ForegroundColor Green
    } else {
        $results += @{Provider="OpenAI Direct"; Status="⏭️ Skipped"; Details="Missing credentials"}
        Write-Host "  ⏭️ OpenAI Direct: Skipped" -ForegroundColor Gray
    }
} catch {
    $results += @{Provider="OpenAI Direct"; Status="❌ Failed"; Details=$_.Exception.Message}
    Write-Host "  ❌ OpenAI Direct: Failed" -ForegroundColor Red
}

# Test Anthropic
Write-Host "Testing Anthropic (Claude)..." -ForegroundColor Yellow
try {
    $apiKey = $env:ANTHROPIC_API_KEY
    if ($apiKey) {
        $headers = @{
            "x-api-key" = $apiKey
            "anthropic-version" = "2023-06-01"
            "Content-Type" = "application/json"
        }
        $body = @{
            model = "claude-sonnet-4-20250514"
            max_tokens = 100
            messages = @(
                @{ role = "user"; content = "Say hello" }
            )
        } | ConvertTo-Json -Depth 10
        
        $response = Invoke-RestMethod -Uri "https://api.anthropic.com/v1/messages" -Method POST -Headers $headers -Body $body -ErrorAction Stop
        $results += @{Provider="Anthropic (Claude)"; Status="✅ Success"; Details=$response.content[0].text}
        Write-Host "  ✅ Anthropic: OK" -ForegroundColor Green
    } else {
        $results += @{Provider="Anthropic"; Status="⏭️ Skipped"; Details="Missing credentials"}
        Write-Host "  ⏭️ Anthropic: Skipped" -ForegroundColor Gray
    }
} catch {
    $results += @{Provider="Anthropic"; Status="❌ Failed"; Details=$_.Exception.Message}
    Write-Host "  ❌ Anthropic: Failed" -ForegroundColor Red
}

# Test DeepSeek Direct
Write-Host "Testing DeepSeek Direct..." -ForegroundColor Yellow
try {
    $apiKey = $env:DEEPSEEK_API_KEY
    if ($apiKey) {
        $headers = @{
            "Authorization" = "Bearer $apiKey"
            "Content-Type" = "application/json"
        }
        $body = @{
            model = "deepseek-chat"
            messages = @(
                @{ role = "user"; content = "Say hello" }
            )
        } | ConvertTo-Json -Depth 10
        
        $uri = "$($env:DEEPSEEK_BASE_URL)/chat/completions"
        if (-not $uri) { $uri = "https://api.deepseek.com/v1/chat/completions" }
        
        $response = Invoke-RestMethod -Uri $uri -Method POST -Headers $headers -Body $body -ErrorAction Stop
        $results += @{Provider="DeepSeek Direct"; Status="✅ Success"; Details=$response.choices[0].message.content}
        Write-Host "  ✅ DeepSeek Direct: OK" -ForegroundColor Green
    } else {
        $results += @{Provider="DeepSeek Direct"; Status="⏭️ Skipped"; Details="Missing credentials"}
        Write-Host "  ⏭️ DeepSeek Direct: Skipped" -ForegroundColor Gray
    }
} catch {
    $results += @{Provider="DeepSeek Direct"; Status="❌ Failed"; Details=$_.Exception.Message}
    Write-Host "  ❌ DeepSeek Direct: Failed" -ForegroundColor Red
}

# Summary
Write-Host "`n=== Test Summary ===" -ForegroundColor Cyan
$results | Format-Table -AutoSize

$successCount = ($results | Where-Object { $_.Status -eq "✅ Success" }).Count
$totalCount = $results.Count

Write-Host "`nSuccess: $successCount/$totalCount providers" -ForegroundColor $(if ($successCount -eq $totalCount) { "Green" } else { "Yellow" })

