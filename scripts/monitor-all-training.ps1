# Monitor all training jobs

$instanceId = "i-05a16e074a5d79473"
$commands = @{
    "GPU Setup" = "321b62a7-6d3b-4f25-b7a7-4fe063d0efc4"
    "Vampire Training" = "267fb42d-086e-4e5b-9b38-0018400fdf7b"
    "Zombie Training" = "2f51aec2-55ab-4afc-a4cd-124b24c3e721"
}

Write-Host "Monitoring all training jobs on $instanceId`n" -ForegroundColor Cyan

while ($true) {
    Clear-Host
    Write-Host "=== TRAINING MONITOR ===" -ForegroundColor Cyan
    Write-Host "Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')`n"
    
    foreach ($cmd in $commands.GetEnumerator()) {
        $status = aws ssm list-command-invocations --instance-id $instanceId --command-id $cmd.Value --query "CommandInvocations[0].Status" --output text 2>$null
        
        $color = switch ($status) {
            "Success" { "Green" }
            "InProgress" { "Yellow" }
            "Pending" { "Cyan" }
            "Failed" { "Red" }
            default { "White" }
        }
        
        Write-Host "$($cmd.Key): " -NoNewline
        Write-Host $status -ForegroundColor $color
    }
    
    Write-Host "`nPress Ctrl+C to exit"
    Start-Sleep -Seconds 30
}

