param(
    [string]$Region = "us-east-1"
)

Write-Host "Creating RDS Enhanced Monitoring Role..." -ForegroundColor Cyan

# Create trust policy for RDS monitoring
$trustPolicy = @'
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "",
            "Effect": "Allow",
            "Principal": {
                "Service": "monitoring.rds.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
'@

$trustPolicy | Out-File -FilePath "rds-monitoring-trust.json" -Encoding UTF8

# Create the role
$roleExists = aws iam get-role --role-name rds-enhanced-monitoring-role --query "Role.RoleName" --output text 2>$null

if ($roleExists -ne "rds-enhanced-monitoring-role") {
    aws iam create-role `
        --role-name rds-enhanced-monitoring-role `
        --assume-role-policy-document file://rds-monitoring-trust.json `
        --description "Role for RDS Enhanced Monitoring"
    
    # Attach the required policy
    aws iam attach-role-policy `
        --role-name rds-enhanced-monitoring-role `
        --policy-arn arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole
    
    Write-Host "✓ RDS Enhanced Monitoring role created" -ForegroundColor Green
} else {
    Write-Host "✓ RDS Enhanced Monitoring role already exists" -ForegroundColor Green
}

# Clean up
Remove-Item -Path "rds-monitoring-trust.json" -ErrorAction SilentlyContinue

Write-Host "Role ARN: arn:aws:iam::$((aws sts get-caller-identity --query Account --output text)):role/rds-enhanced-monitoring-role" -ForegroundColor White

