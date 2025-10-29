# Generate Secure Secrets for Be Free Fitness
# This script generates cryptographically secure random keys for your .env file

Write-Host "=== Generating Secure Keys for Be Free Fitness ===" -ForegroundColor Cyan
Write-Host ""

# Generate JWT_SECRET (64 random bytes as base64)
$jwtBytes = New-Object byte[] 64
[System.Security.Cryptography.RandomNumberGenerator]::Fill($jwtBytes)
$jwtSecret = [Convert]::ToBase64String($jwtBytes)

# Generate JWT_REFRESH_SECRET (64 random bytes as base64)
$jwtRefreshBytes = New-Object byte[] 64
[System.Security.Cryptography.RandomNumberGenerator]::Fill($jwtRefreshBytes)
$jwtRefreshSecret = [Convert]::ToBase64String($jwtRefreshBytes)

# Generate SESSION_SECRET (64 random bytes as base64)
$sessionBytes = New-Object byte[] 64
[System.Security.Cryptography.RandomNumberGenerator]::Fill($sessionBytes)
$sessionSecret = [Convert]::ToBase64String($sessionBytes)

# Generate ENCRYPTION_KEY (32 random bytes as hex - for AES-256)
$encryptionBytes = New-Object byte[] 32
[System.Security.Cryptography.RandomNumberGenerator]::Fill($encryptionBytes)
$encryptionKey = [BitConverter]::ToString($encryptionBytes).Replace('-', '').ToLower()

# Generate VIDEO_ENCRYPTION_KEY (64 hex characters - 32 bytes)
$videoEncryptionBytes = New-Object byte[] 32
[System.Security.Cryptography.RandomNumberGenerator]::Fill($videoEncryptionBytes)
$videoEncryptionKey = [BitConverter]::ToString($videoEncryptionBytes).Replace('-', '').ToLower()

Write-Host "Copy these values to your .env file:" -ForegroundColor Green
Write-Host ""
Write-Host "# Security Configuration" -ForegroundColor Gray
Write-Host "JWT_SECRET=$jwtSecret" -ForegroundColor White
Write-Host "JWT_REFRESH_SECRET=$jwtRefreshSecret" -ForegroundColor White
Write-Host "SESSION_SECRET=$sessionSecret" -ForegroundColor White
Write-Host "ENCRYPTION_KEY=$encryptionKey" -ForegroundColor White
Write-Host "VIDEO_ENCRYPTION_KEY=$videoEncryptionKey" -ForegroundColor White
Write-Host ""

Write-Host "=== IMPORTANT SECURITY NOTES ===" -ForegroundColor Red
Write-Host ""
Write-Host "✓ JWT_SECRET: Used for signing authentication tokens (must be kept secret)" -ForegroundColor Yellow
Write-Host "✓ JWT_REFRESH_SECRET: Used for refresh token signing" -ForegroundColor Yellow
Write-Host "✓ SESSION_SECRET: Used for session cookie encryption" -ForegroundColor Yellow
Write-Host "✓ ENCRYPTION_KEY: Used for general data encryption (32 bytes = 64 hex chars)" -ForegroundColor Yellow
Write-Host "✓ VIDEO_ENCRYPTION_KEY: Used for video file encryption (32 bytes = 64 hex chars)" -ForegroundColor Yellow
Write-Host ""
Write-Host "SECURITY BEST PRACTICES:" -ForegroundColor Cyan
Write-Host "1. Never commit these keys to version control (they're in .gitignore)" -ForegroundColor White
Write-Host "2. Use different keys for development, staging, and production environments" -ForegroundColor White
Write-Host "3. Store production keys securely (Azure Key Vault, AWS Secrets Manager, etc.)" -ForegroundColor White
Write-Host "4. If keys are ever compromised, regenerate them immediately" -ForegroundColor White
Write-Host "5. Keep a secure backup of production keys in a password manager" -ForegroundColor White
Write-Host "6. Rotate keys periodically (every 90-180 days for production)" -ForegroundColor White
Write-Host ""
