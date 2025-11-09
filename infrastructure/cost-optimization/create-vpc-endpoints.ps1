# Create VPC Endpoints for Cost Optimization
# Eliminates data transfer charges for AWS service access
# Estimated savings: $50-150/mo

$ErrorActionPreference = "Stop"

Write-Host "🔌 Creating VPC Endpoints for Cost Optimization" -ForegroundColor Cyan
Write-Host "=" * 70

$region = "us-east-1"
$vpcId = "vpc-045c9e283c23ae01e"  # From aws-resources.csv
$routeTableId = $null  # Will discover

# Get route table
Write-Host "`nDiscovering VPC route tables..."
$routeTables = aws ec2 describe-route-tables `
    --filters "Name=vpc-id,Values=$vpcId" `
    --region $region `
    --query "RouteTables[].RouteTableId" `
    --output json | ConvertFrom-Json

$routeTableId = $routeTables[0]
Write-Host "Using route table: $routeTableId"

# Get subnet IDs
$subnets = aws ec2 describe-subnets `
    --filters "Name=vpc-id,Values=$vpcId" `
    --region $region `
    --query "Subnets[].SubnetId" `
    --output json | ConvertFrom-Json

Write-Host "Found $($subnets.Count) subnets"

# Get security group (for interface endpoints)
$securityGroup = "sg-00419f4094a7d2101"  # AI-Gaming-Services-SG from aws-resources.csv

# VPC Endpoints to create
$endpoints = @{
    "S3" = @{
        Type = "Gateway"
        ServiceName = "com.amazonaws.$region.s3"
        RouteTableIds = @($routeTableId)
        Description = "S3 Gateway Endpoint - Saves data transfer for ECR image layers"
    }
    "ECR-API" = @{
        Type = "Interface"
        ServiceName = "com.amazonaws.$region.ecr.api"
        SubnetIds = $subnets
        SecurityGroupIds = @($securityGroup)
        PrivateDnsEnabled = $true
        Description = "ECR API Endpoint - Eliminates NAT charges for Docker pulls"
    }
    "ECR-DKR" = @{
        Type = "Interface"
        ServiceName = "com.amazonaws.$region.ecr.dkr"
        SubnetIds = $subnets
        SecurityGroupIds = @($securityGroup)
        PrivateDnsEnabled = $true
        Description = "ECR Docker Endpoint - Eliminates NAT charges for image layers"
    }
    "CloudWatch-Logs" = @{
        Type = "Interface"
        ServiceName = "com.amazonaws.$region.logs"
        SubnetIds = $subnets
        SecurityGroupIds = @($securityGroup)
        PrivateDnsEnabled = $true
        Description = "CloudWatch Logs Endpoint - Saves on log shipping costs"
    }
    "CloudWatch-Monitoring" = @{
        Type = "Interface"
        ServiceName = "com.amazonaws.$region.monitoring"
        SubnetIds = $subnets
        SecurityGroupIds = @($securityGroup)
        PrivateDnsEnabled = $true
        Description = "CloudWatch Monitoring Endpoint - Saves on metrics publishing"
    }
    "ECS" = @{
        Type = "Interface"
        ServiceName = "com.amazonaws.$region.ecs"
        SubnetIds = $subnets
        SecurityGroupIds = @($securityGroup)
        PrivateDnsEnabled = $true
        Description = "ECS Endpoint - Saves on ECS API calls"
    }
    "ECS-Agent" = @{
        Type = "Interface"
        ServiceName = "com.amazonaws.$region.ecs-agent"
        SubnetIds = $subnets
        SecurityGroupIds = @($securityGroup)
        PrivateDnsEnabled = $true
        Description = "ECS Agent Endpoint - Saves on task communication"
    }
    "ECS-Telemetry" = @{
        Type = "Interface"
        ServiceName = "com.amazonaws.$region.ecs-telemetry"
        SubnetIds = $subnets
        SecurityGroupIds = @($securityGroup)
        PrivateDnsEnabled = $true
        Description = "ECS Telemetry Endpoint - Saves on metrics/logs from tasks"
    }
}

$created = 0
$skipped = 0
$failed = 0

foreach ($endpoint in $endpoints.GetEnumerator()) {
    $name = $endpoint.Key
    $config = $endpoint.Value
    
    Write-Host "`nCreating $name endpoint..." -ForegroundColor Yellow
    Write-Host "  Type: $($config.Type)"
    Write-Host "  Service: $($config.ServiceName)"
    
    try {
        # Check if endpoint already exists
        $existing = aws ec2 describe-vpc-endpoints `
            --filters "Name=vpc-id,Values=$vpcId" "Name=service-name,Values=$($config.ServiceName)" `
            --region $region `
            --query "VpcEndpoints[0].VpcEndpointId" `
            --output text
        
        if ($existing -and $existing -ne "None") {
            Write-Host "  ℹ️ Endpoint already exists: $existing" -ForegroundColor Gray
            $skipped++
            continue
        }
        
        # Create endpoint based on type
        if ($config.Type -eq "Gateway") {
            # Gateway endpoint (S3, DynamoDB)
            $result = aws ec2 create-vpc-endpoint `
                --vpc-id $vpcId `
                --service-name $config.ServiceName `
                --route-table-ids $config.RouteTableIds `
                --region $region `
                --output json | ConvertFrom-Json
            
            Write-Host "  ✅ Created Gateway Endpoint: $($result.VpcEndpoint.VpcEndpointId)" -ForegroundColor Green
            
        } else {
            # Interface endpoint (most AWS services)
            $result = aws ec2 create-vpc-endpoint `
                --vpc-id $vpcId `
                --service-name $config.ServiceName `
                --vpc-endpoint-type Interface `
                --subnet-ids $config.SubnetIds `
                --security-group-ids $config.SecurityGroupIds `
                --private-dns-enabled `
                --region $region `
                --output json | ConvertFrom-Json
            
            Write-Host "  ✅ Created Interface Endpoint: $($result.VpcEndpoint.VpcEndpointId)" -ForegroundColor Green
        }
        
        $created++
        
    } catch {
        Write-Host "  ❌ Failed to create $name endpoint: $_" -ForegroundColor Red
        $failed++
    }
}

# Summary
Write-Host "`n" + ("=" * 70)
Write-Host "✅ VPC ENDPOINT DEPLOYMENT COMPLETE" -ForegroundColor Green
Write-Host ("=" * 70)

Write-Host "`nResults:"
Write-Host "  Created: $created endpoints"
Write-Host "  Skipped (already exist): $skipped endpoints"
Write-Host "  Failed: $failed endpoints"

Write-Host "`nEstimated Savings:"
Write-Host "  - Data transfer elimination: ~$50-150/mo"
Write-Host "  - ECR image pulls: No NAT Gateway charges"
Write-Host "  - CloudWatch logs/metrics: No data transfer charges"
Write-Host "  - S3 access: No NAT Gateway charges"

Write-Host "`nCreated Endpoints:"
$allEndpoints = aws ec2 describe-vpc-endpoints `
    --filters "Name=vpc-id,Values=$vpcId" `
    --region $region `
    --query "VpcEndpoints[].[VpcEndpointId,ServiceName,State]" `
    --output table

Write-Host $allEndpoints

Write-Host ""

