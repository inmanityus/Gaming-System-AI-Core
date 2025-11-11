# GPU Training Monitoring Script
# Monitors the LoRA adapter training progress on i-06bbe0eede27ea89f

param(
    [string]$InstanceId = "i-06bbe0eede27ea89f",
    [string]$CommandId = "aca6c659-af60-4824-a245-294ba5e12d58"
)

Write-Host "=== GPU Training Monitor ===" -ForegroundColor Cyan
Write-Host "Instance: $InstanceId" -ForegroundColor White
Write-Host "Command: $CommandId" -ForegroundColor Gray
Write-Host ""

# Check command status
$status = aws ssm list-command-invocations --command-id $CommandId --details --query 'CommandInvocations[0].Status' --output text
Write-Host "Training Status: $status" -ForegroundColor Yellow

# Get training output
Write-Host "`nFetching training logs..." -ForegroundColor Cyan
$output = aws ssm get-command-invocation --command-id $CommandId --instance-id $InstanceId --output json | ConvertFrom-Json

# Show last 50 lines of output
Write-Host "`n=== Last 50 lines of training output ===" -ForegroundColor Green
($output.StandardOutputContent -split "`n") | Select-Object -Last 50 | ForEach-Object {
    if ($_ -match "Training vampire_") { Write-Host $_ -ForegroundColor Yellow }
    elseif ($_ -match "Completed vampire_") { Write-Host $_ -ForegroundColor Green }
    elseif ($_ -match "error|Error|ERROR") { Write-Host $_ -ForegroundColor Red }
    else { Write-Host $_ -ForegroundColor White }
}

# Check GPU status
Write-Host "`n=== Checking GPU Status ===" -ForegroundColor Cyan
$gpuCheck = aws ssm send-command --instance-ids $InstanceId --document-name "AWS-RunShellScript" --parameters 'commands=["nvidia-smi --query-gpu=index,name,utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader"]' --output json | ConvertFrom-Json
Start-Sleep -Seconds 5
$gpuOutput = aws ssm get-command-invocation --command-id $gpuCheck.Command.CommandId --instance-id $InstanceId --output json | ConvertFrom-Json
Write-Host $gpuOutput.StandardOutputContent

# Check training files
Write-Host "`n=== Checking Adapter Files ===" -ForegroundColor Cyan
$filesCheck = aws ssm send-command --instance-ids $InstanceId --document-name "AWS-RunShellScript" --parameters 'commands=["ls -lh /home/ubuntu/training/adapters/vampire/ 2>/dev/null || echo No adapters yet"]' --output json | ConvertFrom-Json
Start-Sleep -Seconds 5
$filesOutput = aws ssm get-command-invocation --command-id $filesCheck.Command.CommandId --instance-id $InstanceId --output json | ConvertFrom-Json
Write-Host $filesOutput.StandardOutputContent

Write-Host "`n=== Monitor Complete ===" -ForegroundColor Cyan
Write-Host "Run this script again to check progress" -ForegroundColor Gray

