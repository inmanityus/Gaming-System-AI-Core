#!/usr/bin/env pwsh
# Script to add database subnets to existing VPC

$ErrorActionPreference = "Stop"

$VpcId = "vpc-0684c566fb7cc6b12"

Write-Host "=== Adding Database Subnets to VPC ==="
Write-Host "VPC ID: $VpcId"

# Create subnet in us-east-1a
Write-Host "Creating database subnet in us-east-1a..."
$subnet1 = aws ec2 create-subnet --vpc-id $VpcId --cidr-block 10.0.21.0/24 --availability-zone us-east-1a --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=ai-core-database-us-east-1a},{Key=Type,Value=database},{Key=Project,Value=AI-Core}]' --output json | ConvertFrom-Json
Write-Host "Created: $($subnet1.Subnet.SubnetId)"

# Create subnet in us-east-1b
Write-Host "Creating database subnet in us-east-1b..."
$subnet2 = aws ec2 create-subnet --vpc-id $VpcId --cidr-block 10.0.22.0/24 --availability-zone us-east-1b --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=ai-core-database-us-east-1b},{Key=Type,Value=database},{Key=Project,Value=AI-Core}]' --output json | ConvertFrom-Json
Write-Host "Created: $($subnet2.Subnet.SubnetId)"

# Create subnet in us-east-1c
Write-Host "Creating database subnet in us-east-1c..."
$subnet3 = aws ec2 create-subnet --vpc-id $VpcId --cidr-block 10.0.23.0/24 --availability-zone us-east-1c --tag-specifications 'ResourceType=subnet,Tags=[{Key=Name,Value=ai-core-database-us-east-1c},{Key=Type,Value=database},{Key=Project,Value=AI-Core}]' --output json | ConvertFrom-Json
Write-Host "Created: $($subnet3.Subnet.SubnetId)"

# Get route tables
Write-Host "`nFinding private route tables..."

# Route table for us-east-1a (NAT: nat-0551c8c2614566997)
$rt1 = aws ec2 describe-route-tables --filters "Name=vpc-id,Values=$VpcId" "Name=route.nat-gateway-id,Values=nat-0551c8c2614566997" --query 'RouteTables[0].RouteTableId' --output text
Write-Host "Route table for us-east-1a: $rt1"

# Route table for us-east-1b (NAT: nat-0ca47f9946692e082)  
$rt2 = aws ec2 describe-route-tables --filters "Name=vpc-id,Values=$VpcId" "Name=route.nat-gateway-id,Values=nat-0ca47f9946692e082" --query 'RouteTables[0].RouteTableId' --output text
Write-Host "Route table for us-east-1b: $rt2"

# Route table for us-east-1c (NAT: nat-005acdf8b3bbf8ce3)
$rt3 = aws ec2 describe-route-tables --filters "Name=vpc-id,Values=$VpcId" "Name=route.nat-gateway-id,Values=nat-005acdf8b3bbf8ce3" --query 'RouteTables[0].RouteTableId' --output text
Write-Host "Route table for us-east-1c: $rt3"

# Associate subnets with route tables
Write-Host "`nAssociating subnets with route tables..."

aws ec2 associate-route-table --subnet-id $subnet1.Subnet.SubnetId --route-table-id $rt1 | Out-Null
Write-Host "Associated $($subnet1.Subnet.SubnetId) with $rt1"

aws ec2 associate-route-table --subnet-id $subnet2.Subnet.SubnetId --route-table-id $rt2 | Out-Null
Write-Host "Associated $($subnet2.Subnet.SubnetId) with $rt2"

aws ec2 associate-route-table --subnet-id $subnet3.Subnet.SubnetId --route-table-id $rt3 | Out-Null
Write-Host "Associated $($subnet3.Subnet.SubnetId) with $rt3"

# Create DB subnet group
Write-Host "`nCreating RDS DB Subnet Group..."

$subnetIds = @($subnet1.Subnet.SubnetId, $subnet2.Subnet.SubnetId, $subnet3.Subnet.SubnetId) -join " "

try {
    aws rds create-db-subnet-group --db-subnet-group-name "ai-core-database-subnet-group" --db-subnet-group-description "Database subnet group for AI Core RDS instances" --subnet-ids $subnetIds --tags "Key=Project,Value=AI-Core" "Key=Environment,Value=production" | Out-Null
    Write-Host "Created DB Subnet Group: ai-core-database-subnet-group"
}
catch {
    Write-Host "DB Subnet Group might already exist"
}

Write-Host "`n=== Database Subnets Created Successfully ==="
Write-Host "Subnet 1 (us-east-1a): $($subnet1.Subnet.SubnetId)"
Write-Host "Subnet 2 (us-east-1b): $($subnet2.Subnet.SubnetId)"
Write-Host "Subnet 3 (us-east-1c): $($subnet3.Subnet.SubnetId)"

# Save configuration
$config = @{
    VpcId = $VpcId
    DatabaseSubnets = @{
        "us-east-1a" = @{
            SubnetId = $subnet1.Subnet.SubnetId
            CidrBlock = "10.0.21.0/24"
        }
        "us-east-1b" = @{
            SubnetId = $subnet2.Subnet.SubnetId
            CidrBlock = "10.0.22.0/24"
        }
        "us-east-1c" = @{
            SubnetId = $subnet3.Subnet.SubnetId
            CidrBlock = "10.0.23.0/24"
        }
    }
    DBSubnetGroup = "ai-core-database-subnet-group"
} | ConvertTo-Json -Depth 10 | Out-File -FilePath "database-subnets-config.json" -Encoding UTF8

Write-Host "`nConfiguration saved to: database-subnets-config.json"
