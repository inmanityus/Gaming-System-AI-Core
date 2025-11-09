# Monitor training progress on GPU instance

param(
    [string]$InstanceId = "i-05a16e074a5d79473",
    [string]$CommandId = "721be0e5-6e42-4d4e-b5eb-96cae523e2f8"
)

Write-Host "Monitoring training on instance $InstanceId..." -ForegroundColor Cyan

while ($true) {
    $status = aws ssm list-command-invocations `
        --instance-id $InstanceId `
        --command-id $CommandId `
        --details `
        --query "CommandInvocations[0].[Status,StandardOutputContent]" `
        --output text
    
    Write-Host "`r[$(Get-Date -Format 'HH:mm:ss')] Status: $($status.Split()[0])" -NoNewline
    
    if ($status -match "Success|Failed|TimedOut") {
        Write-Host "`n`nFinal output:"
        Write-Host $status
        break
    }
    
    Start-Sleep -Seconds 30
}
