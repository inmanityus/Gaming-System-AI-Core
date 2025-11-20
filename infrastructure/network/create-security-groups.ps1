#!/usr/bin/env pwsh
# Script to create security groups for AI Core infrastructure

param(
    [Parameter(Mandatory=$false)]
    [string]$VpcId = "vpc-0684c566fb7cc6b12",
    
    [Parameter(Mandatory=$false)]
    [string]$Environment = "production"
)

$ErrorActionPreference = "Stop"

Write-Host "=== Creating Security Groups for AI Core ==="
Write-Host "VPC ID: $VpcId"
Write-Host "Environment: $Environment"
Write-Host ""

$securityGroups = @{}

try {
    # ALB Security Group
    Write-Host "Creating ALB Security Group..."
    $albSg = aws ec2 create-security-group `
        --group-name "ai-core-$Environment-alb-sg" `
        --description "Security group for Application Load Balancers" `
        --vpc-id $VpcId `
        --tag-specifications "ResourceType=security-group,Tags=[{Key=Name,Value=ai-core-$Environment-alb-sg},{Key=Environment,Value=$Environment},{Key=Project,Value=AI-Core}]" `
        --output json | ConvertFrom-Json
    
    $securityGroups["ALB"] = $albSg.GroupId
    Write-Host "  Created: $($albSg.GroupId)"
    
    # Add rules for ALB
    aws ec2 authorize-security-group-ingress --group-id $albSg.GroupId --ip-permissions "IpProtocol=tcp,FromPort=80,ToPort=80,IpRanges=[{CidrIp=0.0.0.0/0,Description='HTTP from Internet'}]" | Out-Null
    aws ec2 authorize-security-group-ingress --group-id $albSg.GroupId --ip-permissions "IpProtocol=tcp,FromPort=443,ToPort=443,IpRanges=[{CidrIp=0.0.0.0/0,Description='HTTPS from Internet'}]" | Out-Null
    Write-Host "  Added ingress rules for HTTP/HTTPS"
    
    # ECS Security Group
    Write-Host "`nCreating ECS Security Group..."
    $ecsSg = aws ec2 create-security-group `
        --group-name "ai-core-$Environment-ecs-sg" `
        --description "Security group for ECS tasks" `
        --vpc-id $VpcId `
        --tag-specifications "ResourceType=security-group,Tags=[{Key=Name,Value=ai-core-$Environment-ecs-sg},{Key=Environment,Value=$Environment},{Key=Project,Value=AI-Core}]" `
        --output json | ConvertFrom-Json
    
    $securityGroups["ECS"] = $ecsSg.GroupId
    Write-Host "  Created: $($ecsSg.GroupId)"
    
    # Add rules for ECS
    aws ec2 authorize-security-group-ingress --group-id $ecsSg.GroupId --protocol tcp --port 1-65535 --source-group $albSg.GroupId | Out-Null
    aws ec2 authorize-security-group-ingress --group-id $ecsSg.GroupId --protocol tcp --port 1-65535 --source-group $ecsSg.GroupId | Out-Null
    Write-Host "  Added ingress rules from ALB and self"
    
    # RDS Security Group
    Write-Host "`nCreating RDS Security Group..."
    $rdsSg = aws ec2 create-security-group `
        --group-name "ai-core-$Environment-rds-sg" `
        --description "Security group for RDS databases" `
        --vpc-id $VpcId `
        --tag-specifications "ResourceType=security-group,Tags=[{Key=Name,Value=ai-core-$Environment-rds-sg},{Key=Environment,Value=$Environment},{Key=Project,Value=AI-Core}]" `
        --output json | ConvertFrom-Json
    
    $securityGroups["RDS"] = $rdsSg.GroupId
    Write-Host "  Created: $($rdsSg.GroupId)"
    
    # Add rules for RDS
    aws ec2 authorize-security-group-ingress --group-id $rdsSg.GroupId --protocol tcp --port 5432 --source-group $ecsSg.GroupId | Out-Null
    
    # Also allow from EKS node security group if it exists
    $eksNodeSg = "sg-01bceff63ef314be5"  # From existing infrastructure
    try {
        aws ec2 authorize-security-group-ingress --group-id $rdsSg.GroupId --protocol tcp --port 5432 --source-group $eksNodeSg | Out-Null
        Write-Host "  Added ingress rules from ECS and EKS"
    }
    catch {
        Write-Host "  Added ingress rules from ECS"
    }
    
    # ElastiCache Security Group
    Write-Host "`nCreating ElastiCache Security Group..."
    $cacheSg = aws ec2 create-security-group `
        --group-name "ai-core-$Environment-elasticache-sg" `
        --description "Security group for ElastiCache" `
        --vpc-id $VpcId `
        --tag-specifications "ResourceType=security-group,Tags=[{Key=Name,Value=ai-core-$Environment-elasticache-sg},{Key=Environment,Value=$Environment},{Key=Project,Value=AI-Core}]" `
        --output json | ConvertFrom-Json
    
    $securityGroups["ElastiCache"] = $cacheSg.GroupId
    Write-Host "  Created: $($cacheSg.GroupId)"
    
    # Add rules for ElastiCache
    aws ec2 authorize-security-group-ingress --group-id $cacheSg.GroupId --protocol tcp --port 6379 --source-group $ecsSg.GroupId | Out-Null
    aws ec2 authorize-security-group-ingress --group-id $cacheSg.GroupId --protocol tcp --port 16379 --source-group $ecsSg.GroupId | Out-Null
    try {
        aws ec2 authorize-security-group-ingress --group-id $cacheSg.GroupId --protocol tcp --port 6379 --source-group $eksNodeSg | Out-Null
        Write-Host "  Added ingress rules for Redis from ECS and EKS"
    }
    catch {
        Write-Host "  Added ingress rules for Redis from ECS"
    }
    
    # OpenSearch Security Group
    Write-Host "`nCreating OpenSearch Security Group..."
    $openSearchSg = aws ec2 create-security-group `
        --group-name "ai-core-$Environment-opensearch-sg" `
        --description "Security group for OpenSearch" `
        --vpc-id $VpcId `
        --tag-specifications "ResourceType=security-group,Tags=[{Key=Name,Value=ai-core-$Environment-opensearch-sg},{Key=Environment,Value=$Environment},{Key=Project,Value=AI-Core}]" `
        --output json | ConvertFrom-Json
    
    $securityGroups["OpenSearch"] = $openSearchSg.GroupId
    Write-Host "  Created: $($openSearchSg.GroupId)"
    
    # Add rules for OpenSearch
    aws ec2 authorize-security-group-ingress --group-id $openSearchSg.GroupId --protocol tcp --port 9200 --source-group $ecsSg.GroupId | Out-Null
    aws ec2 authorize-security-group-ingress --group-id $openSearchSg.GroupId --protocol tcp --port 9300 --source-group $openSearchSg.GroupId | Out-Null
    Write-Host "  Added ingress rules for OpenSearch"
    
    # Bastion Security Group (optional - for management access)
    Write-Host "`nCreating Bastion Security Group..."
    $bastionSg = aws ec2 create-security-group `
        --group-name "ai-core-$Environment-bastion-sg" `
        --description "Security group for Bastion hosts" `
        --vpc-id $VpcId `
        --tag-specifications "ResourceType=security-group,Tags=[{Key=Name,Value=ai-core-$Environment-bastion-sg},{Key=Environment,Value=$Environment},{Key=Project,Value=AI-Core}]" `
        --output json | ConvertFrom-Json
    
    $securityGroups["Bastion"] = $bastionSg.GroupId
    Write-Host "  Created: $($bastionSg.GroupId)"
    Write-Host "  Note: Add your IP to bastion security group for SSH access"
    
    # Save configuration
    $config = @{
        VpcId = $VpcId
        Environment = $Environment
        SecurityGroups = $securityGroups
        CreatedDate = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    } | ConvertTo-Json -Depth 10 | Out-File -FilePath "security-groups-config.json" -Encoding UTF8
    
    Write-Host "`n=== Security Groups Created Successfully ==="
    Write-Host "`nSecurity Group Summary:"
    foreach ($sg in $securityGroups.GetEnumerator()) {
        Write-Host "  $($sg.Key): $($sg.Value)"
    }
    
    Write-Host "`nConfiguration saved to: security-groups-config.json"
    
} catch {
    Write-Host "Error: $_"
    Write-Host $_.Exception.Message
    exit 1
}
