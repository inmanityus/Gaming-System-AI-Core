#!/usr/bin/env pwsh
# VPC Infrastructure Setup Script
# TASK-002: Network Foundation - Creates VPCs with 3 AZs
# This script creates the network infrastructure for the AI Core

param(
    [Parameter(Mandatory=$false)]
    [string]$Environment = "dev",
    
    [Parameter(Mandatory=$false)]
    [string]$Region = "us-east-1",
    
    [Parameter(Mandatory=$false)]
    [string]$VpcCidr = "10.0.0.0/16",
    
    [Parameter(Mandatory=$false)]
    [switch]$DryRun = $false
)

$ErrorActionPreference = "Stop"

# Colors for output
$GREEN = "`e[32m"
$YELLOW = "`e[33m"
$RED = "`e[31m"
$NC = "`e[0m"

Write-Host "${GREEN}=== VPC Infrastructure Setup ===${NC}"
Write-Host "Environment: $Environment"
Write-Host "Region: $Region"
Write-Host "VPC CIDR: $VpcCidr"
Write-Host ""

# Define subnet configuration
$subnetConfig = @{
    PublicSubnets = @(
        @{ Name = "public-1a"; CIDR = "10.0.1.0/24"; AZ = "${Region}a" },
        @{ Name = "public-1b"; CIDR = "10.0.2.0/24"; AZ = "${Region}b" },
        @{ Name = "public-1c"; CIDR = "10.0.3.0/24"; AZ = "${Region}c" }
    )
    PrivateSubnets = @(
        @{ Name = "private-1a"; CIDR = "10.0.11.0/24"; AZ = "${Region}a" },
        @{ Name = "private-1b"; CIDR = "10.0.12.0/24"; AZ = "${Region}b" },
        @{ Name = "private-1c"; CIDR = "10.0.13.0/24"; AZ = "${Region}c" }
    )
    DatabaseSubnets = @(
        @{ Name = "database-1a"; CIDR = "10.0.21.0/24"; AZ = "${Region}a" },
        @{ Name = "database-1b"; CIDR = "10.0.22.0/24"; AZ = "${Region}b" },
        @{ Name = "database-1c"; CIDR = "10.0.23.0/24"; AZ = "${Region}c" }
    )
}

# Function to create VPC
function New-VPCInfrastructure {
    Write-Host "${YELLOW}Creating VPC...${NC}"
    
    if ($DryRun) {
        Write-Host "${YELLOW}[DRY RUN] Would create VPC with CIDR $VpcCidr${NC}"
        return @{ VpcId = "vpc-dryrun123" }
    }
    
    # Create VPC
    $vpc = aws ec2 create-vpc `
        --cidr-block $VpcCidr `
        --tag-specifications "ResourceType=vpc,Tags=[{Key=Name,Value=ai-core-$Environment},{Key=Environment,Value=$Environment},{Key=Project,Value=AI-Core}]" `
        --output json | ConvertFrom-Json
        
    $vpcId = $vpc.Vpc.VpcId
    Write-Host "${GREEN}✓ VPC created: $vpcId${NC}"
    
    # Enable DNS hostnames
    aws ec2 modify-vpc-attribute `
        --vpc-id $vpcId `
        --enable-dns-hostnames `
        --output json | Out-Null
        
    # Enable DNS support
    aws ec2 modify-vpc-attribute `
        --vpc-id $vpcId `
        --enable-dns-support `
        --output json | Out-Null
        
    Write-Host "${GREEN}✓ DNS support enabled${NC}"
    
    return $vpc.Vpc
}

# Function to create Internet Gateway
function New-InternetGateway {
    param([string]$VpcId)
    
    Write-Host "${YELLOW}Creating Internet Gateway...${NC}"
    
    if ($DryRun) {
        Write-Host "${YELLOW}[DRY RUN] Would create Internet Gateway${NC}"
        return "igw-dryrun123"
    }
    
    # Create Internet Gateway
    $igw = aws ec2 create-internet-gateway `
        --tag-specifications "ResourceType=internet-gateway,Tags=[{Key=Name,Value=ai-core-$Environment-igw},{Key=Environment,Value=$Environment}]" `
        --output json | ConvertFrom-Json
        
    $igwId = $igw.InternetGateway.InternetGatewayId
    Write-Host "${GREEN}✓ Internet Gateway created: $igwId${NC}"
    
    # Attach to VPC
    aws ec2 attach-internet-gateway `
        --vpc-id $VpcId `
        --internet-gateway-id $igwId `
        --output json | Out-Null
        
    Write-Host "${GREEN}✓ Internet Gateway attached to VPC${NC}"
    
    return $igwId
}

# Function to create subnets
function New-Subnets {
    param(
        [string]$VpcId,
        [array]$SubnetList,
        [string]$SubnetType
    )
    
    Write-Host "${YELLOW}Creating $SubnetType subnets...${NC}"
    
    $subnetIds = @()
    
    foreach ($subnet in $SubnetList) {
        if ($DryRun) {
            Write-Host "${YELLOW}[DRY RUN] Would create subnet $($subnet.Name) with CIDR $($subnet.CIDR)${NC}"
            $subnetIds += "subnet-dryrun-$($subnet.Name)"
            continue
        }
        
        $subnetResult = aws ec2 create-subnet `
            --vpc-id $VpcId `
            --cidr-block $subnet.CIDR `
            --availability-zone $subnet.AZ `
            --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=ai-core-$Environment-$($subnet.Name)},{Key=Environment,Value=$Environment},{Key=Type,Value=$SubnetType}]" `
            --output json | ConvertFrom-Json
            
        $subnetId = $subnetResult.Subnet.SubnetId
        $subnetIds += $subnetId
        
        Write-Host "${GREEN}  ✓ Subnet created: $($subnet.Name) - $subnetId${NC}"
        
        # Enable auto-assign public IP for public subnets
        if ($SubnetType -eq "public") {
            aws ec2 modify-subnet-attribute `
                --subnet-id $subnetId `
                --map-public-ip-on-launch `
                --output json | Out-Null
        }
    }
    
    return $subnetIds
}

# Function to create NAT Gateways
function New-NATGateways {
    param([array]$PublicSubnetIds)
    
    Write-Host "${YELLOW}Creating NAT Gateways...${NC}"
    
    $natGatewayIds = @()
    
    for ($i = 0; $i -lt $PublicSubnetIds.Count; $i++) {
        $az = @("a", "b", "c")[$i]
        
        if ($DryRun) {
            Write-Host "${YELLOW}[DRY RUN] Would create NAT Gateway in AZ $az${NC}"
            $natGatewayIds += "nat-dryrun-$az"
            continue
        }
        
        # Allocate Elastic IP
        $eip = aws ec2 allocate-address `
            --domain vpc `
            --tag-specifications "ResourceType=elastic-ip,Tags=[{Key=Name,Value=ai-core-$Environment-nat-eip-$az},{Key=Environment,Value=$Environment}]" `
            --output json | ConvertFrom-Json
            
        $allocationId = $eip.AllocationId
        
        # Create NAT Gateway
        $nat = aws ec2 create-nat-gateway `
            --subnet-id $PublicSubnetIds[$i] `
            --allocation-id $allocationId `
            --tag-specifications "ResourceType=nat-gateway,Tags=[{Key=Name,Value=ai-core-$Environment-nat-$az},{Key=Environment,Value=$Environment}]" `
            --output json | ConvertFrom-Json
            
        $natGatewayIds += $nat.NatGateway.NatGatewayId
        
        Write-Host "${GREEN}  ✓ NAT Gateway created in AZ $az: $($nat.NatGateway.NatGatewayId)${NC}"
    }
    
    # Wait for NAT Gateways to be available
    if (-not $DryRun) {
        Write-Host "  Waiting for NAT Gateways to become available..."
        foreach ($natId in $natGatewayIds) {
            aws ec2 wait nat-gateway-available --nat-gateway-ids $natId
        }
        Write-Host "${GREEN}  ✓ All NAT Gateways are available${NC}"
    }
    
    return $natGatewayIds
}

# Function to create route tables
function New-RouteTables {
    param(
        [string]$VpcId,
        [string]$InternetGatewayId,
        [array]$NatGatewayIds,
        [hashtable]$SubnetIds
    )
    
    Write-Host "${YELLOW}Creating route tables...${NC}"
    
    if ($DryRun) {
        Write-Host "${YELLOW}[DRY RUN] Would create route tables${NC}"
        return
    }
    
    # Create public route table
    $publicRT = aws ec2 create-route-table `
        --vpc-id $VpcId `
        --tag-specifications "ResourceType=route-table,Tags=[{Key=Name,Value=ai-core-$Environment-public-rt},{Key=Environment,Value=$Environment}]" `
        --output json | ConvertFrom-Json
        
    $publicRTId = $publicRT.RouteTable.RouteTableId
    Write-Host "${GREEN}  ✓ Public route table created: $publicRTId${NC}"
    
    # Add route to Internet Gateway
    aws ec2 create-route `
        --route-table-id $publicRTId `
        --destination-cidr-block "0.0.0.0/0" `
        --gateway-id $InternetGatewayId `
        --output json | Out-Null
        
    # Associate public subnets with public route table
    foreach ($subnetId in $SubnetIds.PublicSubnets) {
        aws ec2 associate-route-table `
            --subnet-id $subnetId `
            --route-table-id $publicRTId `
            --output json | Out-Null
    }
    
    # Create private route tables (one per AZ for NAT Gateway)
    for ($i = 0; $i -lt $NatGatewayIds.Count; $i++) {
        $az = @("a", "b", "c")[$i]
        
        $privateRT = aws ec2 create-route-table `
            --vpc-id $VpcId `
            --tag-specifications "ResourceType=route-table,Tags=[{Key=Name,Value=ai-core-$Environment-private-rt-$az},{Key=Environment,Value=$Environment}]" `
            --output json | ConvertFrom-Json
            
        $privateRTId = $privateRT.RouteTable.RouteTableId
        Write-Host "${GREEN}  ✓ Private route table created for AZ $az`: $privateRTId${NC}"
        
        # Add route to NAT Gateway
        aws ec2 create-route `
            --route-table-id $privateRTId `
            --destination-cidr-block "0.0.0.0/0" `
            --nat-gateway-id $NatGatewayIds[$i] `
            --output json | Out-Null
            
        # Associate private and database subnets in this AZ
        aws ec2 associate-route-table `
            --subnet-id $SubnetIds.PrivateSubnets[$i] `
            --route-table-id $privateRTId `
            --output json | Out-Null
            
        aws ec2 associate-route-table `
            --subnet-id $SubnetIds.DatabaseSubnets[$i] `
            --route-table-id $privateRTId `
            --output json | Out-Null
    }
    
    Write-Host "${GREEN}  ✓ Route tables configured${NC}"
}

# Function to create security groups
function New-SecurityGroups {
    param([string]$VpcId)
    
    Write-Host "${YELLOW}Creating security groups...${NC}"
    
    $securityGroups = @{}
    
    if ($DryRun) {
        Write-Host "${YELLOW}[DRY RUN] Would create security groups${NC}"
        return $securityGroups
    }
    
    # ALB Security Group
    $albSG = aws ec2 create-security-group `
        --group-name "ai-core-$Environment-alb-sg" `
        --description "Security group for Application Load Balancers" `
        --vpc-id $VpcId `
        --tag-specifications "ResourceType=security-group,Tags=[{Key=Name,Value=ai-core-$Environment-alb-sg},{Key=Environment,Value=$Environment}]" `
        --output json | ConvertFrom-Json
        
    $securityGroups["ALB"] = $albSG.GroupId
    
    # Allow HTTP and HTTPS from anywhere
    aws ec2 authorize-security-group-ingress `
        --group-id $albSG.GroupId `
        --ip-permissions "IpProtocol=tcp,FromPort=80,ToPort=80,IpRanges=[{CidrIp=0.0.0.0/0}]" `
        --output json | Out-Null
        
    aws ec2 authorize-security-group-ingress `
        --group-id $albSG.GroupId `
        --ip-permissions "IpProtocol=tcp,FromPort=443,ToPort=443,IpRanges=[{CidrIp=0.0.0.0/0}]" `
        --output json | Out-Null
        
    Write-Host "${GREEN}  ✓ ALB security group created: $($albSG.GroupId)${NC}"
    
    # ECS Security Group
    $ecsSG = aws ec2 create-security-group `
        --group-name "ai-core-$Environment-ecs-sg" `
        --description "Security group for ECS tasks" `
        --vpc-id $VpcId `
        --tag-specifications "ResourceType=security-group,Tags=[{Key=Name,Value=ai-core-$Environment-ecs-sg},{Key=Environment,Value=$Environment}]" `
        --output json | ConvertFrom-Json
        
    $securityGroups["ECS"] = $ecsSG.GroupId
    
    # Allow traffic from ALB
    aws ec2 authorize-security-group-ingress `
        --group-id $ecsSG.GroupId `
        --protocol tcp `
        --port 1-65535 `
        --source-group $albSG.GroupId `
        --output json | Out-Null
        
    Write-Host "${GREEN}  ✓ ECS security group created: $($ecsSG.GroupId)${NC}"
    
    # RDS Security Group
    $rdsSG = aws ec2 create-security-group `
        --group-name "ai-core-$Environment-rds-sg" `
        --description "Security group for RDS databases" `
        --vpc-id $VpcId `
        --tag-specifications "ResourceType=security-group,Tags=[{Key=Name,Value=ai-core-$Environment-rds-sg},{Key=Environment,Value=$Environment}]" `
        --output json | ConvertFrom-Json
        
    $securityGroups["RDS"] = $rdsSG.GroupId
    
    # Allow PostgreSQL from ECS
    aws ec2 authorize-security-group-ingress `
        --group-id $rdsSG.GroupId `
        --protocol tcp `
        --port 5432 `
        --source-group $ecsSG.GroupId `
        --output json | Out-Null
        
    Write-Host "${GREEN}  ✓ RDS security group created: $($rdsSG.GroupId)${NC}"
    
    # ElastiCache Security Group
    $cacheSG = aws ec2 create-security-group `
        --group-name "ai-core-$Environment-cache-sg" `
        --description "Security group for ElastiCache" `
        --vpc-id $VpcId `
        --tag-specifications "ResourceType=security-group,Tags=[{Key=Name,Value=ai-core-$Environment-cache-sg},{Key=Environment,Value=$Environment}]" `
        --output json | ConvertFrom-Json
        
    $securityGroups["Cache"] = $cacheSG.GroupId
    
    # Allow Redis from ECS
    aws ec2 authorize-security-group-ingress `
        --group-id $cacheSG.GroupId `
        --protocol tcp `
        --port 6379 `
        --source-group $ecsSG.GroupId `
        --output json | Out-Null
        
    Write-Host "${GREEN}  ✓ ElastiCache security group created: $($cacheSG.GroupId)${NC}"
    
    return $securityGroups
}

# Function to create VPC endpoints
function New-VPCEndpoints {
    param(
        [string]$VpcId,
        [array]$PrivateSubnetIds,
        [string]$SecurityGroupId
    )
    
    Write-Host "${YELLOW}Creating VPC endpoints...${NC}"
    
    if ($DryRun) {
        Write-Host "${YELLOW}[DRY RUN] Would create VPC endpoints${NC}"
        return
    }
    
    # Get route table IDs for the private subnets
    $routeTableIds = @()
    foreach ($subnetId in $PrivateSubnetIds) {
        $rtAssoc = aws ec2 describe-route-tables `
            --filters "Name=association.subnet-id,Values=$subnetId" `
            --query "RouteTables[0].RouteTableId" `
            --output text
        if ($rtAssoc -ne "None") {
            $routeTableIds += $rtAssoc
        }
    }
    $routeTableIds = $routeTableIds | Select-Object -Unique
    
    # S3 Gateway Endpoint
    $s3Endpoint = aws ec2 create-vpc-endpoint `
        --vpc-id $VpcId `
        --service-name "com.amazonaws.$Region.s3" `
        --route-table-ids $routeTableIds `
        --output json | ConvertFrom-Json
        
    Write-Host "${GREEN}  ✓ S3 VPC endpoint created: $($s3Endpoint.VpcEndpoint.VpcEndpointId)${NC}"
    
    # DynamoDB Gateway Endpoint
    $ddbEndpoint = aws ec2 create-vpc-endpoint `
        --vpc-id $VpcId `
        --service-name "com.amazonaws.$Region.dynamodb" `
        --route-table-ids $routeTableIds `
        --output json | ConvertFrom-Json
        
    Write-Host "${GREEN}  ✓ DynamoDB VPC endpoint created: $($ddbEndpoint.VpcEndpoint.VpcEndpointId)${NC}"
    
    # Create Interface Endpoints
    $interfaceEndpoints = @(
        "com.amazonaws.$Region.ecr.api",
        "com.amazonaws.$Region.ecr.dkr",
        "com.amazonaws.$Region.logs",
        "com.amazonaws.$Region.sts",
        "com.amazonaws.$Region.elasticloadbalancing",
        "com.amazonaws.$Region.autoscaling",
        "com.amazonaws.$Region.ecs",
        "com.amazonaws.$Region.ecs-agent",
        "com.amazonaws.$Region.ecs-telemetry"
    )
    
    foreach ($endpoint in $interfaceEndpoints) {
        try {
            $result = aws ec2 create-vpc-endpoint `
                --vpc-id $VpcId `
                --vpc-endpoint-type Interface `
                --service-name $endpoint `
                --subnet-ids $PrivateSubnetIds `
                --security-group-ids $SecurityGroupId `
                --output json 2>$null | ConvertFrom-Json
                
            Write-Host "${GREEN}  ✓ VPC endpoint created: $endpoint${NC}"
        }
        catch {
            Write-Host "${YELLOW}  ! Could not create endpoint: $endpoint (may not be available in this region)${NC}"
        }
    }
}

# Main execution
try {
    # Step 1: Create VPC
    $vpc = New-VPCInfrastructure
    $vpcId = $vpc.VpcId
    Write-Host ""
    
    # Step 2: Create Internet Gateway
    $igwId = New-InternetGateway -VpcId $vpcId
    Write-Host ""
    
    # Step 3: Create Subnets
    $subnetIds = @{
        PublicSubnets = @()
        PrivateSubnets = @()
        DatabaseSubnets = @()
    }
    
    $subnetIds.PublicSubnets = New-Subnets -VpcId $vpcId -SubnetList $subnetConfig.PublicSubnets -SubnetType "public"
    Write-Host ""
    
    $subnetIds.PrivateSubnets = New-Subnets -VpcId $vpcId -SubnetList $subnetConfig.PrivateSubnets -SubnetType "private"
    Write-Host ""
    
    $subnetIds.DatabaseSubnets = New-Subnets -VpcId $vpcId -SubnetList $subnetConfig.DatabaseSubnets -SubnetType "database"
    Write-Host ""
    
    # Step 4: Create NAT Gateways
    $natGatewayIds = New-NATGateways -PublicSubnetIds $subnetIds.PublicSubnets
    Write-Host ""
    
    # Step 5: Configure Route Tables
    New-RouteTables -VpcId $vpcId -InternetGatewayId $igwId -NatGatewayIds $natGatewayIds -SubnetIds $subnetIds
    Write-Host ""
    
    # Step 6: Create Security Groups
    $securityGroups = New-SecurityGroups -VpcId $vpcId
    Write-Host ""
    
    # Step 7: Create VPC Endpoints
    if (-not $DryRun) {
        New-VPCEndpoints -VpcId $vpcId -PrivateSubnetIds $subnetIds.PrivateSubnets -SecurityGroupId $securityGroups["ECS"]
        Write-Host ""
    }
    
    # Save configuration
    $vpcConfig = @{
        VpcId = $vpcId
        InternetGatewayId = $igwId
        NatGatewayIds = $natGatewayIds
        Subnets = $subnetIds
        SecurityGroups = $securityGroups
        Environment = $Environment
        Region = $Region
        CreatedDate = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    }
    
    $configPath = "vpc-config-$Environment.json"
    $vpcConfig | ConvertTo-Json -Depth 10 | Out-File -FilePath $configPath -Encoding UTF8
    
    Write-Host "${GREEN}=== VPC Infrastructure Setup Complete ===${NC}"
    Write-Host ""
    Write-Host "VPC ID: $vpcId"
    Write-Host "Configuration saved to: $configPath"
    Write-Host ""
    Write-Host "Next Steps:"
    Write-Host "1. Deploy EKS cluster in the VPC (TASK-003)"
    Write-Host "2. Create RDS Aurora cluster in database subnets (TASK-004)"
    Write-Host "3. Deploy ECS cluster for containerized services"
    Write-Host "4. Configure VPN or Direct Connect for secure access"
}
catch {
    Write-Host "${RED}Error: $_${NC}"
    Write-Host $_.Exception.Message
    exit 1
}
