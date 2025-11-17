# Deploy a single service to AWS ECS
param(
    [Parameter(Mandatory=$true)]
    [string]$ServiceName,
    
    [Parameter(Mandatory=$true)]
    [string]$TaskDefinitionFile
)

Write-Host "Deploying $ServiceName..." -ForegroundColor Cyan

$region = "us-east-1"
$cluster = "language-system-cluster"

# Register task definition
Write-Host "Registering task definition..." -ForegroundColor Yellow
$taskDefArn = aws ecs register-task-definition `
    --cli-input-json file://$TaskDefinitionFile `
    --region $region `
    --query "taskDefinition.taskDefinitionArn" `
    --output text

if ($LASTEXITCODE -eq 0) {
    Write-Host "Task definition registered: $taskDefArn" -ForegroundColor Green
    
    # Create or update service
    $serviceName = "$ServiceName-fargate"
    
    # Check if service exists
    $existingService = aws ecs describe-services `
        --cluster $cluster `
        --services $serviceName `
        --region $region `
        --query "services[?status=='ACTIVE'].serviceName" `
        --output text 2>$null
        
    if ($existingService) {
        # Update existing service
        Write-Host "Updating existing service..." -ForegroundColor Yellow
        aws ecs update-service `
            --cluster $cluster `
            --service $serviceName `
            --task-definition $taskDefArn `
            --force-new-deployment `
            --region $region | Out-Null
            
        Write-Host "Service updated: $serviceName" -ForegroundColor Green
    } else {
        # Create new service
        Write-Host "Creating new service..." -ForegroundColor Yellow
        
        aws ecs create-service `
            --cluster $cluster `
            --service-name $serviceName `
            --task-definition $taskDefArn `
            --desired-count 1 `
            --launch-type FARGATE `
            --network-configuration "awsvpcConfiguration={subnets=[subnet-0b8ba7ffd0610b34f],securityGroups=[sg-0e1949ead49a08f97],assignPublicIp=ENABLED}" `
            --region $region | Out-Null
            
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Service created: $serviceName" -ForegroundColor Green
        } else {
            Write-Warning "Failed to create service. Check AWS console for details."
        }
    }
} else {
    Write-Error "Failed to register task definition"
    exit 1
}

Write-Host "Deployment complete for $ServiceName" -ForegroundColor Green

