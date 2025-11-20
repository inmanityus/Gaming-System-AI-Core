#!/usr/bin/env pwsh
# Script to add database subnets to existing VPC
# These subnets will be used for RDS instances

param(
    [Parameter(Mandatory=$false)]
    [string]$VpcId = "vpc-0684c566fb7cc6b12",
    
    [Parameter(Mandatory=$false)]
    [string]$Region = "us-east-1"
)

$ErrorActionPreference = "Stop"

# Colors for output
$GREEN = "`e[32m"
$YELLOW = "`e[33m"
$RED = "`e[31m"
$NC = "`e[0m"

Write-Host "${GREEN}=== Adding Database Subnets to VPC ===${NC}"
Write-Host "VPC ID: $VpcId"
Write-Host ""

# Define database subnet configuration
$databaseSubnets = @(
    @{ 
        Name = "ai-core-database-us-east-1a"
        CIDR = "10.0.21.0/24"
        AZ = "us-east-1a"
    },
    @{ 
        Name = "ai-core-database-us-east-1b"
        CIDR = "10.0.22.0/24"
        AZ = "us-east-1b"
    },
    @{ 
        Name = "ai-core-database-us-east-1c"
        CIDR = "10.0.23.0/24"
        AZ = "us-east-1c"
    }
)

$createdSubnets = @()

try {
    # Create database subnets
    Write-Host "${YELLOW}Creating database subnets...${NC}"
    
    foreach ($subnet in $databaseSubnets) {
        Write-Host "  Creating subnet $($subnet.Name) ($($subnet.CIDR))..."
        
        $result = aws ec2 create-subnet `
            --vpc-id $VpcId `
            --cidr-block $subnet.CIDR `
            --availability-zone $subnet.AZ `
            --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=$($subnet.Name)},{Key=Type,Value=database},{Key=Project,Value=AI-Core}]" `
            --output json | ConvertFrom-Json
            
        $subnetId = $result.Subnet.SubnetId
        Write-Host "${GREEN}    ✓ Created: $subnetId${NC}"
        
        $createdSubnets += @{
            SubnetId = $subnetId
            Name = $subnet.Name
            CIDR = $subnet.CIDR
            AZ = $subnet.AZ
        }
    }
    
    # Get private route table IDs (one per AZ)
    Write-Host "`n${YELLOW}Finding private route tables...${NC}"
    
    # Get NAT Gateways to find their route tables
    $natGateways = aws ec2 describe-nat-gateways `
        --filter "Name=vpc-id,Values=$VpcId" `
        --query 'NatGateways[*].[NatGatewayId,SubnetId]' `
        --output json | ConvertFrom-Json
    
    $routeTableMap = @{}
    
    foreach ($nat in $natGateways) {
        $natId = $nat[0]
        $subnetId = $nat[1]
        
        # Get subnet details to find AZ
        $subnet = aws ec2 describe-subnets `
            --subnet-ids $subnetId `
            --query 'Subnets[0].[AvailabilityZone]' `
            --output text
        
        # Find route table with this NAT Gateway
        $routeTable = aws ec2 describe-route-tables `
            --filters "Name=vpc-id,Values=$VpcId" "Name=route.nat-gateway-id,Values=$natId" `
            --query 'RouteTables[0].RouteTableId' `
            --output text
            
        if ($routeTable -ne "None") {
            $routeTableMap[$subnet] = $routeTable
            Write-Host "  Found route table $routeTable for AZ $subnet (NAT: $natId)"
        }
    }
    
    # Associate database subnets with private route tables
    Write-Host "`n${YELLOW}Associating database subnets with route tables...${NC}"
    
    foreach ($subnet in $createdSubnets) {
        $routeTableId = $routeTableMap[$subnet.AZ]
        
        if ($routeTableId) {
            $assoc = aws ec2 associate-route-table `
                --subnet-id $subnet.SubnetId `
                --route-table-id $routeTableId `
                --output json | ConvertFrom-Json
                
            Write-Host "${GREEN}  ✓ Associated $($subnet.Name) with route table $routeTableId${NC}"
        } else {
            Write-Host "${YELLOW}  ! Could not find route table for AZ $($subnet.AZ)${NC}"
        }
    }
    
    # Create DB subnet group for RDS
    Write-Host "`n${YELLOW}Creating RDS DB Subnet Group...${NC}"
    
    $dbSubnetIds = $createdSubnets | ForEach-Object { $_.SubnetId }
    
    try {
        $dbSubnetGroup = aws rds create-db-subnet-group `
            --db-subnet-group-name "ai-core-database-subnet-group" `
            --db-subnet-group-description "Database subnet group for AI Core RDS instances" `
            --subnet-ids $dbSubnetIds `
            --tags "Key=Project,Value=AI-Core" "Key=Environment,Value=production" `
            --output json | ConvertFrom-Json
            
        Write-Host "${GREEN}✓ Created DB Subnet Group: ai-core-database-subnet-group${NC}"
    }
    catch {
        if ($_.Exception.Message -like "*DBSubnetGroupAlreadyExists*") {
            Write-Host "${YELLOW}! DB Subnet Group already exists${NC}"
        } else {
            throw
        }
    }
    
    # Output summary
    Write-Host "`n${GREEN}=== Database Subnets Created Successfully ===${NC}"
    Write-Host "`nSubnet Summary:"
    foreach ($subnet in $createdSubnets) {
        Write-Host "  - $($subnet.Name): $($subnet.SubnetId) ($($subnet.CIDR))"
    }
    
    # Save configuration
    $config = @{
        DatabaseSubnets = $createdSubnets
        DBSubnetGroup = "ai-core-database-subnet-group"
        CreatedDate = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    }
    
    $configPath = "database-subnets-config.json"
    $config | ConvertTo-Json -Depth 10 | Out-File -FilePath $configPath -Encoding UTF8
    Write-Host "`nConfiguration saved to: $configPath"
    
} catch {
    Write-Host "${RED}Error: $_${NC}"
    Write-Host $_.Exception.Message
    
    # Cleanup on error
    if ($createdSubnets.Count -gt 0) {
        Write-Host "`n${YELLOW}Cleaning up created subnets...${NC}"
        foreach ($subnet in $createdSubnets) {
            try {
                aws ec2 delete-subnet --subnet-id $subnet.SubnetId
                Write-Host "  Deleted $($subnet.SubnetId)"
            } catch {
                Write-Host "  Failed to delete $($subnet.SubnetId)"
            }
        }
    }
    
    exit 1
}
