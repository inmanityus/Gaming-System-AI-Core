#!/usr/bin/env pwsh
# Update HTTP-NATS Gateway service to use ALB

param(
    [Parameter(Mandatory=$false)]
    [string]$Environment = "production"
)

$ErrorActionPreference = "Stop"

# Colors
$GREEN = "`e[32m"
$YELLOW = "`e[33m"
$RED = "`e[31m"
$NC = "`e[0m"

Write-Host "${GREEN}=== Updating Gateway Service with ALB ===${NC}"

# Get target group ARN from terraform output
$targetGroupArn = "arn:aws:elasticloadbalancing:us-east-1:695353648052:targetgroup/gateway-production/9325be4ef4e702b0"

# Get current service configuration
Write-Host "${YELLOW}Getting current service configuration...${NC}"
$service = aws ecs describe-services `
    --cluster gaming-system-cluster `
    --services http-nats-gateway `
    --query 'services[0]' `
    --output json | ConvertFrom-Json

Write-Host "Current task count: $($service.runningCount)"

# Update service with ALB target group
Write-Host "${YELLOW}Updating service with ALB target group...${NC}"

$loadBalancer = @{
    targetGroupArn = $targetGroupArn
    containerName = "http-nats-gateway"
    containerPort = 8000
} | ConvertTo-Json -Compress

$result = aws ecs update-service `
    --cluster gaming-system-cluster `
    --service http-nats-gateway `
    --load-balancers $loadBalancer `
    --health-check-grace-period-seconds 60 `
    --output json | ConvertFrom-Json

if ($LASTEXITCODE -ne 0) {
    Write-Host "${RED}ERROR: Failed to update service${NC}"
    exit 1
}

Write-Host "${GREEN}✓ Service updated successfully${NC}"

# Wait for service to stabilize
Write-Host "${YELLOW}Waiting for service to stabilize...${NC}"

$maxWait = 300  # 5 minutes
$checkInterval = 15
$elapsed = 0

while ($elapsed -lt $maxWait) {
    Start-Sleep -Seconds $checkInterval
    $elapsed += $checkInterval
    
    $service = aws ecs describe-services `
        --cluster gaming-system-cluster `
        --services http-nats-gateway `
        --query 'services[0]' `
        --output json | ConvertFrom-Json
    
    $deploymentCount = ($service.deployments | Measure-Object).Count
    $runningCount = $service.runningCount
    $desiredCount = $service.desiredCount
    
    Write-Host "Status: $runningCount/$desiredCount tasks running, $deploymentCount deployment(s)"
    
    # Service is stable when there's only 1 deployment and running = desired
    if ($deploymentCount -eq 1 -and $runningCount -eq $desiredCount) {
        Write-Host "${GREEN}✓ Service is stable${NC}"
        break
    }
}

if ($elapsed -ge $maxWait) {
    Write-Host "${YELLOW}Service is still stabilizing, but continuing...${NC}"
}

# Get ALB DNS name
Write-Host ""
Write-Host "${GREEN}=== Gateway ALB Details ===${NC}"
$albDns = "gateway-production-2098455312.us-east-1.elb.amazonaws.com"
Write-Host "ALB DNS: $albDns"
Write-Host "Gateway URL: http://$albDns"

# Test health endpoint
Write-Host ""
Write-Host "${YELLOW}Testing health endpoint...${NC}"
$healthUrl = "http://$albDns/health"

try {
    $response = Invoke-WebRequest -Uri $healthUrl -Method GET -TimeoutSec 10
    if ($response.StatusCode -eq 200) {
        Write-Host "${GREEN}✓ Health check passed${NC}"
        Write-Host "Response: $($response.Content)"
    }
    else {
        Write-Host "${YELLOW}Health check returned status: $($response.StatusCode)${NC}"
    }
}
catch {
    Write-Host "${RED}Health check failed: $_${NC}"
    Write-Host "This is expected if the service is still starting up"
}

Write-Host ""
Write-Host "${GREEN}=== Next Steps ===${NC}"
Write-Host "1. Wait a few minutes for all health checks to pass"
Write-Host "2. Test the gateway at: http://$albDns"
Write-Host "3. Update SDK configurations to use the public endpoint"
Write-Host "4. Run end-to-end tests"
