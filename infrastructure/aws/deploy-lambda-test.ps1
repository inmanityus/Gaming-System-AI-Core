# Deploy Lambda Performance Test Function

$ErrorActionPreference = "Stop"

Write-Host "Deploying Lambda Performance Test Function..."

# Get VPC information
Write-Host "Getting VPC information..."
$VPC = aws ec2 describe-vpcs --filters "Name=tag:Name,Values=gaming-ai-vpc" --query "Vpcs[0].VpcId" --output text
if (-not $VPC) {
    $VPC = aws ec2 describe-vpcs --query "Vpcs[0].VpcId" --output text
}
Write-Host "VPC: $VPC"

# Get private subnets
$Subnets = aws ec2 describe-subnets `
    --filters "Name=vpc-id,Values=$VPC" "Name=tag:Type,Values=private" `
    --query "Subnets[*].SubnetId" --output text

if (-not $Subnets) {
    # Try without tag filter
    $Subnets = aws ec2 describe-subnets `
        --filters "Name=vpc-id,Values=$VPC" `
        --query "Subnets[?MapPublicIpOnLaunch==``false``].SubnetId" --output text
}

# Convert to comma-separated list
$SubnetList = $Subnets -replace '\s+', ','
Write-Host "Private Subnets: $SubnetList"

# Get database security group
$DBSecurityGroup = aws ec2 describe-security-groups `
    --filters "Name=group-name,Values=gaming-system-aurora-db-db-sg" `
    --query "SecurityGroups[0].GroupId" --output text
Write-Host "Database Security Group: $DBSecurityGroup"

# Deploy the stack
Write-Host "`nDeploying CloudFormation stack..."
aws cloudformation create-stack `
    --stack-name gaming-aurora-performance-test `
    --template-body file://infrastructure/aws/lambda/aurora-performance-test-stack.yaml `
    --parameters `
        ParameterKey=VPCId,ParameterValue=$VPC `
        ParameterKey=PrivateSubnetIds,ParameterValue=$SubnetList `
        ParameterKey=DatabaseSecurityGroupId,ParameterValue=$DBSecurityGroup `
    --capabilities CAPABILITY_NAMED_IAM

Write-Host "Waiting for stack creation to complete..."
aws cloudformation wait stack-create-complete --stack-name gaming-aurora-performance-test

# Get outputs
$FunctionName = aws cloudformation describe-stacks `
    --stack-name gaming-aurora-performance-test `
    --query "Stacks[0].Outputs[?OutputKey=='FunctionName'].OutputValue" `
    --output text

Write-Host "`nStack deployed successfully!"
Write-Host "Lambda Function: $FunctionName"

# Test the function
Write-Host "`nInvoking Lambda function to test performance..."
$Result = aws lambda invoke `
    --function-name $FunctionName `
    --payload '{}' `
    response.json

# Display results
Write-Host "`nPerformance Test Results:"
Get-Content response.json | ConvertFrom-Json | ConvertTo-Json -Depth 10
Remove-Item response.json

Write-Host "`nLambda deployment and test complete!"
