# Test Azure AI Endpoint
# Corrected script for Azure OpenAI-compatible API

# Azure AI endpoint should be the OpenAI-compatible endpoint
# Format: https://{resource-name}.openai.azure.com/
$endpoint = "https://ai-gaming-core.openai.azure.com"
$apiKey = "7j51TXZmlmBd4vVFVPwLXIMbqffLcVyfnisUCuQwQ2zh5gpaLgBMJQQJ99BJAC4f1cMXJ3w3AAAAACOGjiNj"
# Update this with your actual deployment name
# Common names: "gpt-4-turbo", "gpt-4o-mini", "gpt-35-turbo"
$deploymentName = "gpt-4-turbo"  # Change this to your deployment name

# Construct headers
$headers = @{
    "api-key" = $apiKey
    "Content-Type" = "application/json"
}

# Construct request body
$body = @{
    messages = @(
        @{
            role = "user"
            content = "Test message"
        }
    )
} | ConvertTo-Json -Depth 10

# Construct URI - NO trailing slash on endpoint, add path directly
$uri = "$endpoint/openai/deployments/$deploymentName/chat/completions?api-version=2024-02-15-preview"

Write-Host "Testing Azure AI endpoint..." -ForegroundColor Cyan
Write-Host "Endpoint: $endpoint" -ForegroundColor Gray
Write-Host "Deployment: $deploymentName" -ForegroundColor Gray
Write-Host "URI: $uri" -ForegroundColor Gray

try {
    $response = Invoke-RestMethod -Uri $uri -Method POST -Headers $headers -Body $body
    
    Write-Host "`n✅ SUCCESS!" -ForegroundColor Green
    Write-Host "Response:" -ForegroundColor Cyan
    $response | ConvertTo-Json -Depth 10
}
catch {
    Write-Host "`n❌ ERROR:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Yellow
    
    if ($_.ErrorDetails.Message) {
        Write-Host "`nError Details:" -ForegroundColor Red
        Write-Host $_.ErrorDetails.Message -ForegroundColor Yellow
    }
    
    Write-Host "`nTroubleshooting:" -ForegroundColor Cyan
    Write-Host "1. Verify endpoint format: https://{resource-name}.openai.azure.com" -ForegroundColor Gray
    Write-Host "2. Check deployment name in Azure Portal" -ForegroundColor Gray
    Write-Host "3. Verify API key is correct" -ForegroundColor Gray
    Write-Host "4. Confirm deployment is active" -ForegroundColor Gray
}

