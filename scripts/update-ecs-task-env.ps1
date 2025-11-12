# Update ECS Task Definitions with Database Environment Variables

param(
    [string[]]$Services,
    [string]$SecretId = "gaming-system/bodybroker-db-credentials",
    [string]$Region = "us-east-1"
)

$ErrorActionPreference = "Stop"

# Get DB credentials
$secretJson = aws secretsmanager get-secret-value --secret-id $SecretId --region $Region --query SecretString --output text
$creds = $secretJson | ConvertFrom-Json

foreach ($svc in $Services) {
    Write-Host "Updating $svc..." -ForegroundColor White
    
    # Get current task definition
    $currentSvc = aws ecs describe-services --cluster gaming-system-cluster --service $svc --region $Region | ConvertFrom-Json
    $taskDefArn = $currentSvc.services[0].taskDefinition
    
    # Get task definition details
    $taskDef = aws ecs describe-task-definition --task-definition $taskDefArn --region $Region | ConvertFrom-Json
    $td = $taskDef.taskDefinition
    
    # Prepare environment variables
    $envVars = @(
        @{name="DB_HOST"; value=$creds.host},
        @{name="DB_PORT"; value="5432"},
        @{name="DB_USER"; value=$creds.username},
        @{name="DB_PASSWORD"; value=$creds.password},
        @{name="DB_NAME"; value="postgres"},
        @{name="PGHOST"; value=$creds.host},
        @{name="PGPORT"; value="5432"},
        @{name="PGUSER"; value=$creds.username},
        @{name="PGPASSWORD"; value=$creds.password},
        @{name="PGDATABASE"; value="postgres"}
    )
    
    $container = $td.containerDefinitions[0].PSObject.Copy()
    $container.environment = $envVars
    
    # Build registration object
    $registerObj = @{
        family = $td.family
        containerDefinitions = @($container)
        requiresCompatibilities = $td.requiresCompatibilities
        networkMode = $td.networkMode
        cpu = $td.cpu
        memory = $td.memory
        executionRoleArn = $td.executionRoleArn
    }
    
    # Only add taskRoleArn if it exists
    if ($td.taskRoleArn) {
        $registerObj.taskRoleArn = $td.taskRoleArn
    }
    
    $jsonFile = "task-def-temp.json"
    $registerObj | ConvertTo-Json -Depth 10 | Out-File $jsonFile -Encoding utf8
    
    # Register new task definition
    aws ecs register-task-definition --cli-input-json file://$jsonFile --region $Region --no-cli-pager | Out-Null
    
    if ($LASTEXITCODE -eq 0) {
        # Update service to use new task definition
        aws ecs update-service --cluster gaming-system-cluster --service $svc --force-new-deployment --region $Region --no-cli-pager | Out-Null
        Write-Host "  ✓ $svc updated and redeploying" -ForegroundColor Green
    } else {
        Write-Host "  ✗ $svc failed" -ForegroundColor Red
    }
    
    Remove-Item $jsonFile -ErrorAction SilentlyContinue
}

