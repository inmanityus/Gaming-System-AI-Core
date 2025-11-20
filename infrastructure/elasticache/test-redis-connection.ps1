param(
    [string]$SecretName = "elasticache/ai-core-redis-cluster/auth-token"
)

# Get credentials from Secrets Manager
$secret = aws secretsmanager get-secret-value --secret-id $SecretName --query SecretString --output text | ConvertFrom-Json

# Install redis-cli if needed
if (-not (Get-Command redis-cli -ErrorAction SilentlyContinue)) {
    Write-Host "Installing redis-cli..." -ForegroundColor Yellow
    # For Windows, use WSL or download Redis for Windows
    Write-Host "Please install redis-cli manually or use WSL" -ForegroundColor Red
    exit 1
}

# Test connection
Write-Host "Testing Redis cluster connection..." -ForegroundColor Cyan
Write-Host "Endpoint: $($secret.configurationEndpoint):$($secret.port)" -ForegroundColor White

# Test with redis-cli
redis-cli -h $secret.configurationEndpoint -p $secret.port -a $secret.authToken --no-auth-warning CLUSTER INFO

# Test basic operations
Write-Host "`nTesting basic operations..." -ForegroundColor Cyan
redis-cli -h $secret.configurationEndpoint -p $secret.port -a $secret.authToken --no-auth-warning SET test:key "Hello from AI Core"
redis-cli -h $secret.configurationEndpoint -p $secret.port -a $secret.authToken --no-auth-warning GET test:key
redis-cli -h $secret.configurationEndpoint -p $secret.port -a $secret.authToken --no-auth-warning DEL test:key

Write-Host "`n✓ Connection test complete" -ForegroundColor Green
