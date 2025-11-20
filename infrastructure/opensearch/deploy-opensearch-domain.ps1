param(
    [string]$DomainName = "ai-core-opensearch",
    [string]$InstanceType = "t3.medium.search",
    [int]$InstanceCount = 3,
    [int]$VolumeSize = 100,
    [string]$VolumeType = "gp3"
)

Write-Host "=== Deploying OpenSearch Domain: $DomainName ===" -ForegroundColor Cyan

# Get existing VPC configuration
$vpcConfig = Get-Content -Path "../network/existing-vpc-config.json" | ConvertFrom-Json
$vpcId = $vpcConfig.vpc.id
Write-Host "Using VPC: $vpcId" -ForegroundColor Yellow

# Get subnet configuration - use actual database subnets
$subnets = @("subnet-087eeda0bae6cb2e5", "subnet-0b36e3376d508d01f", "subnet-0523f5b7a55c382f5")
Write-Host "Using subnets: $($subnets -join ', ')" -ForegroundColor Yellow

# Create security group for OpenSearch
Write-Host "`nCreating security group for OpenSearch..." -ForegroundColor Yellow
$sgName = "$DomainName-sg"
$existingSg = aws ec2 describe-security-groups `
    --filters "Name=group-name,Values=$sgName" "Name=vpc-id,Values=$vpcId" `
    --query "SecurityGroups[0].GroupId" `
    --output text 2>$null

if ($existingSg -eq "None" -or $null -eq $existingSg) {
    $sgCreated = aws ec2 create-security-group `
        --group-name $sgName `
        --description "Security group for OpenSearch domain $DomainName" `
        --vpc-id $vpcId `
        --output json | ConvertFrom-Json
    
    $sgId = $sgCreated.GroupId
    Write-Host "✓ Created security group: $sgId" -ForegroundColor Green
    
    # Add ingress rules
    Write-Host "Adding ingress rules..." -ForegroundColor Yellow
    
    # HTTPS access from within VPC
    aws ec2 authorize-security-group-ingress `
        --group-id $sgId `
        --protocol tcp `
        --port 443 `
        --cidr "10.0.0.0/16" `
        --output json | Out-Null
    
    # OpenSearch API port from within VPC
    aws ec2 authorize-security-group-ingress `
        --group-id $sgId `
        --protocol tcp `
        --port 9200 `
        --cidr "10.0.0.0/16" `
        --output json | Out-Null
    
    # OpenSearch transport port for cluster communication
    aws ec2 authorize-security-group-ingress `
        --group-id $sgId `
        --protocol tcp `
        --port 9300 `
        --source-group $sgId `
        --output json | Out-Null
    
    Write-Host "✓ Ingress rules added" -ForegroundColor Green
} else {
    $sgId = $existingSg
    Write-Host "✓ Using existing security group: $sgId" -ForegroundColor Yellow
}

# Create master user password in Secrets Manager
Write-Host "`nCreating master user credentials in Secrets Manager..." -ForegroundColor Yellow
$secretName = "$DomainName-master-credentials"

# Check if secret already exists
$existingSecret = aws secretsmanager describe-secret --secret-id $secretName 2>$null

if ($LASTEXITCODE -ne 0) {
    # Generate random password
    $chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()"
    $masterPassword = -join ((1..24) | ForEach-Object { $chars[(Get-Random -Minimum 0 -Maximum $chars.Length)] })
    
    $secretValue = @{
        username = "opensearch_admin"
        password = $masterPassword
    } | ConvertTo-Json -Compress
    
    aws secretsmanager create-secret `
        --name $secretName `
        --description "Master user credentials for OpenSearch domain $DomainName" `
        --secret-string $secretValue `
        --output json | Out-Null
    
    Write-Host "✓ Master user credentials created" -ForegroundColor Green
} else {
    Write-Host "✓ Using existing master user credentials" -ForegroundColor Yellow
    $secretJson = aws secretsmanager get-secret-value --secret-id $secretName --query SecretString --output text
    $secretValue = $secretJson | ConvertFrom-Json
    $masterPassword = $secretValue.password
    Write-Host "  Username: $($secretValue.username)" -ForegroundColor Gray
}

# Create IAM service-linked role for OpenSearch (if not exists)
Write-Host "`nChecking for OpenSearch service-linked role..." -ForegroundColor Yellow
$serviceRole = aws iam get-role --role-name AWSServiceRoleForAmazonOpenSearchService 2>$null

if ($LASTEXITCODE -ne 0) {
    Write-Host "Creating OpenSearch service-linked role..." -ForegroundColor Yellow
    aws iam create-service-linked-role --aws-service-name opensearchservice.amazonaws.com --output json | Out-Null
    Write-Host "✓ Service-linked role created" -ForegroundColor Green
    
    # Wait for role to be available
    Start-Sleep -Seconds 10
} else {
    Write-Host "✓ Service-linked role exists" -ForegroundColor Yellow
}

# Create domain configuration
$clusterConfig = @{
    InstanceType = $InstanceType
    InstanceCount = $InstanceCount
    DedicatedMasterEnabled = ($InstanceCount -ge 3)
    ZoneAwarenessEnabled = ($InstanceCount -ge 2)
}

if ($InstanceCount -ge 3) {
    $clusterConfig.DedicatedMasterType = "t3.small.search"
    $clusterConfig.DedicatedMasterCount = 3
}

if ($InstanceCount -ge 2) {
    $clusterConfig.ZoneAwarenessConfig = @{ AvailabilityZoneCount = [Math]::Min($InstanceCount, 3) }
}

$ebsOptions = @{
    EBSEnabled = $true
    VolumeType = $VolumeType
    VolumeSize = $VolumeSize
}

if ($VolumeType -eq "gp3") {
    $ebsOptions.Iops = 3000
    $ebsOptions.Throughput = 125
}

$domainConfig = @{
    DomainName = $DomainName
    EngineVersion = "OpenSearch_2.11"
    ClusterConfig = $clusterConfig
    EBSOptions = $ebsOptions
    NodeToNodeEncryptionOptions = @{
        Enabled = $true
    }
    EncryptionAtRestOptions = @{
        Enabled = $true
    }
    AdvancedSecurityOptions = @{
        Enabled = $true
        InternalUserDatabaseEnabled = $true
        MasterUserOptions = @{
            MasterUserName = "opensearch_admin"
            MasterUserPassword = $masterPassword
        }
    }
    VPCOptions = @{
        SubnetIds = $subnets[0..([Math]::Min($InstanceCount, 3) - 1)]
        SecurityGroupIds = @($sgId)
    }
    DomainEndpointOptions = @{
        EnforceHTTPS = $true
        TLSSecurityPolicy = "Policy-Min-TLS-1-2-2019-07"
    }
    AdvancedOptions = @{
        "rest.action.multi.allow_explicit_index" = "true"
        "indices.query.bool.max_clause_count" = "10000"
        "override_main_response_version" = "false"
    }
} | ConvertTo-Json -Depth 10

# Save configuration
$domainConfig | Out-File -FilePath "opensearch-domain-config.json" -Encoding UTF8
Write-Host "`nDomain configuration saved to opensearch-domain-config.json" -ForegroundColor Green

# Check if domain already exists
$existingDomain = aws opensearch describe-domain --domain-name $DomainName 2>$null

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n[WARNING] Domain $DomainName already exists!" -ForegroundColor Yellow
    $response = Read-Host "Do you want to update the existing domain? (yes/no)"
    
    if ($response -eq "yes") {
        Write-Host "`nUpdating existing domain..." -ForegroundColor Yellow
        # Update domain would go here, but it's complex due to API differences
        Write-Host "[INFO] Domain updates are limited. Delete and recreate for major changes." -ForegroundColor Cyan
    }
} else {
    # Create the domain
    Write-Host "`nCreating OpenSearch domain: $DomainName" -ForegroundColor Yellow
    Write-Host "This will take 15-20 minutes..." -ForegroundColor Yellow
    
    $createResult = aws opensearch create-domain --cli-input-json file://opensearch-domain-config.json --output json 2>&1
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Domain creation initiated" -ForegroundColor Green
        
        # Extract domain details
        $domainDetails = $createResult | ConvertFrom-Json
        $domainArn = $domainDetails.DomainStatus.ARN
        
        Write-Host "`nDomain ARN: $domainArn" -ForegroundColor Cyan
        
        # Wait for domain to be active
        Write-Host "`nWaiting for domain to become active..." -ForegroundColor Yellow
        $startTime = Get-Date
        $timeout = 30 # minutes
        
        while ($true) {
            $status = aws opensearch describe-domain `
                --domain-name $DomainName `
                --query "DomainStatus.Processing" `
                --output text
            
            if ($status -eq "False") {
                Write-Host "✓ Domain is active!" -ForegroundColor Green
                break
            }
            
            $elapsed = ((Get-Date) - $startTime).TotalMinutes
            if ($elapsed -gt $timeout) {
                Write-Host "[WARNING] Domain creation is taking longer than expected" -ForegroundColor Yellow
                break
            }
            
            Write-Host -NoNewline "`rProcessing... (${elapsed} minutes)" -ForegroundColor Yellow
            Start-Sleep -Seconds 30
        }
        
        # Get final domain details
        $finalDomain = aws opensearch describe-domain --domain-name $DomainName --output json | ConvertFrom-Json
        $endpoint = $finalDomain.DomainStatus.Endpoint
        $dashboardEndpoint = $finalDomain.DomainStatus.DashboardEndpoint
        
        Write-Host "`n=== OpenSearch Domain Created Successfully ===" -ForegroundColor Green
        Write-Host "Domain Name: $DomainName" -ForegroundColor White
        Write-Host "Endpoint: https://$endpoint" -ForegroundColor White
        Write-Host "Dashboard: https://$dashboardEndpoint" -ForegroundColor White
        Write-Host "Master User: opensearch_admin" -ForegroundColor White
        Write-Host "Password: Stored in Secrets Manager ($secretName)" -ForegroundColor White
        
        # Save endpoint configuration
        $endpointConfig = @{
            DomainName = $DomainName
            Endpoint = "https://$endpoint"
            DashboardEndpoint = "https://$dashboardEndpoint"
            SecurityGroupId = $sgId
            SubnetIds = $subnets[0..([Math]::Min($InstanceCount, 3) - 1)]
            SecretName = $secretName
            CreatedAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        } | ConvertTo-Json -Depth 5
        
        $endpointConfig | Out-File -FilePath "opensearch-endpoints.json" -Encoding UTF8
        Write-Host "`nEndpoint configuration saved to opensearch-endpoints.json" -ForegroundColor Green
        
    } else {
        Write-Host "[ERROR] Failed to create domain:" -ForegroundColor Red
        Write-Host $createResult
        exit 1
    }
}

# Create index patterns and initial configuration
Write-Host "`n=== Next Steps ===" -ForegroundColor Cyan
Write-Host "1. Configure index patterns in OpenSearch Dashboard"
Write-Host "2. Set up Index State Management (ISM) policies"
Write-Host "3. Create index templates for your data"
Write-Host "4. Configure alerting and anomaly detection"
Write-Host "5. Set up cross-cluster search if needed"
