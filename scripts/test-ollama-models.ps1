# Test All Available Ollama Models
# Quick test to verify models are working

Write-Host "=== Testing Ollama Models ===" -ForegroundColor Cyan
Write-Host ""

$models = @(
    @{Name="phi3:mini"; Tier=1; Use="Tier 1 NPCs"},
    @{Name="tinyllama"; Tier=1; Use="Tier 1 NPCs (fastest)"},
    @{Name="qwen2.5:3b"; Tier=1; Use="Tier 1 NPCs"},
    @{Name="llama3.1:8b"; Tier=2; Use="Tier 2/3 NPCs (base)"},
    @{Name="mistral:7b"; Tier=2; Use="Tier 2/3 NPCs (base)"},
    @{Name="qwen2.5:7b"; Tier=2; Use="Tier 2 NPCs"},
    @{Name="deepseek-r1"; Tier="Specialized"; Use="Reasoning tasks"}
)

$results = @()

foreach ($model in $models) {
    Write-Host "Testing $($model.Name)..." -ForegroundColor Yellow
    
    try {
        $response = ollama run $model.Name "Say hello in one word" 2>&1
        
        if ($LASTEXITCODE -eq 0) {
            $results += @{
                Model = $model.Name
                Tier = $model.Tier
                Status = "✅ OK"
                Use = $model.Use
                Response = ($response -join " ").Substring(0, [Math]::Min(50, ($response -join " ").Length))
            }
            Write-Host "  ✅ $($model.Name): OK" -ForegroundColor Green
        } else {
            $results += @{
                Model = $model.Name
                Tier = $model.Tier
                Status = "❌ Failed"
                Use = $model.Use
                Response = "Error: $response"
            }
            Write-Host "  ❌ $($model.Name): Failed" -ForegroundColor Red
        }
    } catch {
        $results += @{
            Model = $model.Name
            Tier = $model.Tier
            Status = "❌ Error"
            Use = $model.Use
            Response = $_.Exception.Message
        }
        Write-Host "  ❌ $($model.Name): Error" -ForegroundColor Red
    }
    
    Start-Sleep -Seconds 1  # Brief pause between tests
}

Write-Host "`n=== Test Results ===" -ForegroundColor Cyan
$results | Format-Table -AutoSize -Property Model, Tier, Status, Use

$successCount = ($results | Where-Object { $_.Status -like "✅*" }).Count
Write-Host "`nSuccess: $successCount/$($models.Count) models" -ForegroundColor $(if ($successCount -eq $models.Count) { "Green" } else { "Yellow" })

