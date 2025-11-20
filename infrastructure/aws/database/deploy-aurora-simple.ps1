# Simple Aurora PostgreSQL deployment script for Gaming System
# This script deploys Aurora without complex parameter handling

$ErrorActionPreference = "Stop"

# Configuration
$StackName = "gaming-system-aurora-db"
$Region = "us-east-1"
$TemplateFile = "infrastructure/aws/database/rds-aurora-postgresql-simple.yaml"

# Get VPC and subnet information
Write-Host "Getting VPC information..."
$VPC = aws ec2 describe-vpcs --region $Region --filters "Name=isDefault,Values=true" --query "Vpcs[0].VpcId" --output text
if (-not $VPC) {
    $VPC = aws ec2 describe-vpcs --region $Region --query "Vpcs[0].VpcId" --output text
}

Write-Host "VPC: $VPC"

# Get subnets (need at least 2 in different AZs)
Write-Host "Getting subnet information..."
$Subnets = aws ec2 describe-subnets --region $Region --filters "Name=vpc-id,Values=$VPC" --query "Subnets[*].[SubnetId,AvailabilityZone]" --output json | ConvertFrom-Json

# Group by AZ and pick one from each
$SubnetsByAZ = @{}
foreach ($subnet in $Subnets) {
    $az = $subnet[1]
    if (-not $SubnetsByAZ.ContainsKey($az)) {
        $SubnetsByAZ[$az] = $subnet[0]
    }
}

# Get at least 2 subnets from different AZs
$SelectedSubnets = $SubnetsByAZ.Values | Select-Object -First 3
$SubnetList = $SelectedSubnets -join ","

Write-Host "Subnets: $SubnetList"

# Create or get application security group
Write-Host "Creating/getting application security group..."
$AppSG = aws ec2 describe-security-groups --region $Region --group-names "gaming-system-app-sg" --filters "Name=vpc-id,Values=$VPC" --query "SecurityGroups[0].GroupId" --output text 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Creating new application security group..."
    $AppSG = aws ec2 create-security-group --region $Region --group-name "gaming-system-app-sg" --description "Gaming System Application Security Group" --vpc-id $VPC --query "GroupId" --output text
}

Write-Host "Application Security Group: $AppSG"

# Deploy the stack
Write-Host "Deploying CloudFormation stack..."
$Parameters = @"
[
    {"ParameterKey": "VPCId", "ParameterValue": "$VPC"},
    {"ParameterKey": "PrivateSubnetIds", "ParameterValue": "$SubnetList"},
    {"ParameterKey": "ApplicationSecurityGroupId", "ParameterValue": "$AppSG"},
    {"ParameterKey": "Environment", "ParameterValue": "production"}
]
"@

# Save parameters to file
$Parameters | Out-File -FilePath "temp-params.json" -Encoding UTF8

try {
    # Check if simplified template exists, if not create it
    if (-not (Test-Path $TemplateFile)) {
        Write-Host "Creating simplified Aurora template..."
        # We'll create this next
    }
    
    # Create the stack
    aws cloudformation create-stack `
        --stack-name $StackName `
        --region $Region `
        --template-body file://$TemplateFile `
        --parameters file://temp-params.json `
        --capabilities CAPABILITY_NAMED_IAM `
        --tags Key=Project,Value=GamingSystemAICore Key=Environment,Value=production `
        --disable-rollback
        
    Write-Host "Stack creation initiated. Waiting for completion..."
    
    # Wait for stack creation
    aws cloudformation wait stack-create-complete --stack-name $StackName --region $Region
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Stack created successfully!"
        
        # Get outputs
        $Outputs = aws cloudformation describe-stacks --stack-name $StackName --region $Region --query "Stacks[0].Outputs" --output json | ConvertFrom-Json
        
        Write-Host "`nStack Outputs:"
        foreach ($output in $Outputs) {
            Write-Host "$($output.OutputKey): $($output.OutputValue)"
        }
        
        # Get secret ARN for credentials
        $SecretArn = ($Outputs | Where-Object { $_.OutputKey -eq "DBSecretArn" }).OutputValue
        if ($SecretArn) {
            Write-Host "`nRetrieving database credentials..."
            $Credentials = aws secretsmanager get-secret-value --secret-id $SecretArn --query SecretString --output text | ConvertFrom-Json
            Write-Host "Database Username: $($Credentials.username)"
            Write-Host "Database Password is stored in Secrets Manager"
        }
    }
    else {
        Write-Host "Stack creation failed. Check CloudFormation console for details."
        # Show recent events
        aws cloudformation describe-stack-events --stack-name $StackName --region $Region --max-items 10 --query "StackEvents[?ResourceStatus=='CREATE_FAILED'].[LogicalResourceId, ResourceStatusReason]" --output table
    }
}
finally {
    # Clean up
    Remove-Item -Path "temp-params.json" -ErrorAction SilentlyContinue
}

Write-Host "`nDeployment script completed."
