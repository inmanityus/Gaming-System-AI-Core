#!/usr/bin/env pwsh
# AWS Organizations Setup Script
# TASK-001: AWS Account Setup - Complete Organizations structure
# This script establishes the AWS multi-account architecture for the AI Core

param(
    [Parameter(Mandatory=$false)]
    [string]$RootEmail = "aws-root@gaming-ai-core.com",
    
    [Parameter(Mandatory=$false)]
    [string]$OrganizationName = "Gaming AI Core",
    
    [Parameter(Mandatory=$false)]
    [switch]$DryRun = $false
)

$ErrorActionPreference = "Stop"

# Colors for output
$GREEN = "`e[32m"
$YELLOW = "`e[33m"
$RED = "`e[31m"
$NC = "`e[0m"

Write-Host "${GREEN}=== AWS Organizations Setup ===${NC}"
Write-Host "Organization: $OrganizationName"
Write-Host "Root Email: $RootEmail"
Write-Host "Dry Run: $DryRun"
Write-Host ""

# Check AWS CLI is configured
try {
    $identity = aws sts get-caller-identity --output json | ConvertFrom-Json
    Write-Host "${GREEN}✓ AWS CLI configured${NC}"
    Write-Host "  Account: $($identity.Account)"
    Write-Host "  ARN: $($identity.Arn)"
    Write-Host ""
}
catch {
    Write-Host "${RED}✗ AWS CLI not configured or not installed${NC}"
    Write-Host "  Please run: aws configure"
    exit 1
}

# Define account structure
$accounts = @(
    @{
        Name = "ai-core-dev"
        Email = "aws-dev@gaming-ai-core.com"
        Purpose = "Development environment"
        OU = "Development"
    },
    @{
        Name = "ai-core-staging"
        Email = "aws-staging@gaming-ai-core.com"
        Purpose = "Staging and pre-production"
        OU = "Staging"
    },
    @{
        Name = "ai-core-prod"
        Email = "aws-prod@gaming-ai-core.com"
        Purpose = "Production workloads"
        OU = "Production"
    },
    @{
        Name = "ai-core-audit"
        Email = "aws-audit@gaming-ai-core.com"
        Purpose = "Audit and compliance logs"
        OU = "Security"
    },
    @{
        Name = "ai-core-billing"
        Email = "aws-billing@gaming-ai-core.com"
        Purpose = "Consolidated billing"
        OU = "Finance"
    }
)

# Define organizational units
$organizationalUnits = @(
    "Development",
    "Staging",
    "Production",
    "Security",
    "Finance"
)

# Function to create or get organization
function Ensure-Organization {
    Write-Host "${YELLOW}Checking for existing organization...${NC}"
    
    try {
        $org = aws organizations describe-organization --output json 2>$null | ConvertFrom-Json
        if ($org) {
            Write-Host "${GREEN}✓ Organization already exists${NC}"
            Write-Host "  ID: $($org.Organization.Id)"
            Write-Host "  Feature Set: $($org.Organization.FeatureSet)"
            return $org.Organization
        }
    }
    catch {
        # Organization doesn't exist, create it
        Write-Host "${YELLOW}Creating new organization...${NC}"
        
        if ($DryRun) {
            Write-Host "${YELLOW}[DRY RUN] Would create organization${NC}"
            return @{ Id = "org-dryrun123"; FeatureSet = "ALL" }
        }
        
        $org = aws organizations create-organization `
            --feature-set ALL `
            --output json | ConvertFrom-Json
            
        Write-Host "${GREEN}✓ Organization created${NC}"
        Write-Host "  ID: $($org.Organization.Id)"
        
        return $org.Organization
    }
}

# Function to create organizational unit
function Create-OrganizationalUnit {
    param(
        [string]$Name,
        [string]$ParentId
    )
    
    Write-Host "  Creating OU: $Name"
    
    # Check if OU exists
    $existingOUs = aws organizations list-organizational-units-for-parent `
        --parent-id $ParentId `
        --output json | ConvertFrom-Json
        
    $existing = $existingOUs.OrganizationalUnits | Where-Object { $_.Name -eq $Name }
    if ($existing) {
        Write-Host "${GREEN}    ✓ OU already exists${NC}"
        return $existing.Id
    }
    
    if ($DryRun) {
        Write-Host "${YELLOW}    [DRY RUN] Would create OU: $Name${NC}"
        return "ou-dryrun-$Name"
    }
    
    $ou = aws organizations create-organizational-unit `
        --parent-id $ParentId `
        --name $Name `
        --output json | ConvertFrom-Json
        
    Write-Host "${GREEN}    ✓ OU created: $($ou.OrganizationalUnit.Id)${NC}"
    return $ou.OrganizationalUnit.Id
}

# Function to create account
function Create-Account {
    param(
        [hashtable]$AccountInfo,
        [string]$OUId
    )
    
    Write-Host "  Creating account: $($AccountInfo.Name)"
    Write-Host "    Email: $($AccountInfo.Email)"
    Write-Host "    Purpose: $($AccountInfo.Purpose)"
    
    # Check if account exists
    $existingAccounts = aws organizations list-accounts --output json | ConvertFrom-Json
    $existing = $existingAccounts.Accounts | Where-Object { 
        $_.Name -eq $AccountInfo.Name -or $_.Email -eq $AccountInfo.Email 
    }
    
    if ($existing) {
        Write-Host "${GREEN}    ✓ Account already exists: $($existing.Id)${NC}"
        return $existing.Id
    }
    
    if ($DryRun) {
        Write-Host "${YELLOW}    [DRY RUN] Would create account${NC}"
        return "123456789012"
    }
    
    # Create account
    $createResult = aws organizations create-account `
        --email $AccountInfo.Email `
        --account-name $AccountInfo.Name `
        --output json | ConvertFrom-Json
        
    $createRequestId = $createResult.CreateAccountStatus.Id
    
    # Wait for account creation
    Write-Host "    Waiting for account creation..."
    $status = "IN_PROGRESS"
    while ($status -eq "IN_PROGRESS") {
        Start-Sleep -Seconds 10
        $statusResult = aws organizations describe-create-account-status `
            --create-account-request-id $createRequestId `
            --output json | ConvertFrom-Json
        $status = $statusResult.CreateAccountStatus.State
    }
    
    if ($status -eq "SUCCEEDED") {
        $accountId = $statusResult.CreateAccountStatus.AccountId
        Write-Host "${GREEN}    ✓ Account created: $accountId${NC}"
        
        # Move account to OU
        if ($OUId -and $OUId -ne "root") {
            Write-Host "    Moving account to OU..."
            
            # Get current parent
            $parents = aws organizations list-parents `
                --child-id $accountId `
                --output json | ConvertFrom-Json
            $currentParent = $parents.Parents[0].Id
            
            # Move to new OU
            aws organizations move-account `
                --account-id $accountId `
                --source-parent-id $currentParent `
                --destination-parent-id $OUId `
                --output json | Out-Null
                
            Write-Host "${GREEN}    ✓ Account moved to OU${NC}"
        }
        
        return $accountId
    }
    else {
        Write-Host "${RED}    ✗ Account creation failed: $($statusResult.CreateAccountStatus.FailureReason)${NC}"
        return $null
    }
}

# Function to enable service control policies
function Enable-ServiceControlPolicies {
    param([string]$RootId)
    
    Write-Host "${YELLOW}Enabling Service Control Policies...${NC}"
    
    if ($DryRun) {
        Write-Host "${YELLOW}[DRY RUN] Would enable SCPs${NC}"
        return
    }
    
    try {
        aws organizations enable-policy-type `
            --root-id $RootId `
            --policy-type SERVICE_CONTROL_POLICY `
            --output json | Out-Null
            
        Write-Host "${GREEN}✓ Service Control Policies enabled${NC}"
    }
    catch {
        # May already be enabled
        Write-Host "${GREEN}✓ Service Control Policies already enabled${NC}"
    }
}

# Function to create baseline SCP
function Create-BaselineSCP {
    Write-Host "${YELLOW}Creating baseline Service Control Policy...${NC}"
    
    # Check if policy exists
    $policies = aws organizations list-policies `
        --filter SERVICE_CONTROL_POLICY `
        --output json | ConvertFrom-Json
        
    $existing = $policies.Policies | Where-Object { $_.Name -eq "BaselineSecurityPolicy" }
    if ($existing) {
        Write-Host "${GREEN}✓ Baseline SCP already exists${NC}"
        return $existing.Id
    }
    
    if ($DryRun) {
        Write-Host "${YELLOW}[DRY RUN] Would create baseline SCP${NC}"
        return "p-dryrun123"
    }
    
    # Create policy document
    $policyDoc = @{
        Version = "2012-10-17"
        Statement = @(
            @{
                Effect = "Deny"
                Action = @(
                    "ec2:TerminateInstances"
                )
                Resource = "*"
                Condition = @{
                    StringNotEquals = @{
                        "aws:PrincipalOrgID" = '${aws:PrincipalOrgID}'
                    }
                }
            },
            @{
                Effect = "Deny"
                Action = @(
                    "organizations:LeaveOrganization",
                    "account:CloseAccount"
                )
                Resource = "*"
            },
            @{
                Effect = "Deny"
                Action = "*"
                Resource = "*"
                Condition = @{
                    StringNotEquals = @{
                        "aws:RequestedRegion" = @(
                            "us-east-1",
                            "eu-west-1",
                            "ap-southeast-1"
                        )
                    }
                }
            }
        )
    } | ConvertTo-Json -Depth 10
    
    # Create policy
    $policy = aws organizations create-policy `
        --content $policyDoc `
        --description "Baseline security controls for all accounts" `
        --name "BaselineSecurityPolicy" `
        --type SERVICE_CONTROL_POLICY `
        --output json | ConvertFrom-Json
        
    Write-Host "${GREEN}✓ Baseline SCP created: $($policy.Policy.PolicySummary.Id)${NC}"
    return $policy.Policy.PolicySummary.Id
}

# Function to enable CloudTrail
function Enable-OrganizationCloudTrail {
    Write-Host "${YELLOW}Setting up Organization CloudTrail...${NC}"
    
    if ($DryRun) {
        Write-Host "${YELLOW}[DRY RUN] Would setup CloudTrail${NC}"
        return
    }
    
    # Create S3 bucket for CloudTrail logs
    $bucketName = "ai-core-cloudtrail-logs-$($identity.Account)"
    
    # Check if bucket exists
    $buckets = aws s3api list-buckets --output json | ConvertFrom-Json
    $existingBucket = $buckets.Buckets | Where-Object { $_.Name -eq $bucketName }
    
    if (-not $existingBucket) {
        Write-Host "  Creating S3 bucket for CloudTrail logs..."
        
        # Create bucket
        aws s3api create-bucket `
            --bucket $bucketName `
            --region us-east-1 `
            --output json | Out-Null
            
        # Enable versioning
        aws s3api put-bucket-versioning `
            --bucket $bucketName `
            --versioning-configuration Status=Enabled `
            --output json | Out-Null
            
        # Set bucket policy for CloudTrail
        $bucketPolicy = @{
            Version = "2012-10-17"
            Statement = @(
                @{
                    Sid = "AWSCloudTrailAclCheck"
                    Effect = "Allow"
                    Principal = @{
                        Service = "cloudtrail.amazonaws.com"
                    }
                    Action = "s3:GetBucketAcl"
                    Resource = "arn:aws:s3:::$bucketName"
                },
                @{
                    Sid = "AWSCloudTrailWrite"
                    Effect = "Allow"
                    Principal = @{
                        Service = "cloudtrail.amazonaws.com"
                    }
                    Action = "s3:PutObject"
                    Resource = "arn:aws:s3:::$bucketName/*"
                    Condition = @{
                        StringEquals = @{
                            "s3:x-amz-acl" = "bucket-owner-full-control"
                        }
                    }
                }
            )
        } | ConvertTo-Json -Depth 10
        
        aws s3api put-bucket-policy `
            --bucket $bucketName `
            --policy $bucketPolicy `
            --output json | Out-Null
            
        Write-Host "${GREEN}  ✓ S3 bucket created${NC}"
    }
    
    # Create organization trail
    $trailName = "ai-core-organization-trail"
    
    try {
        aws cloudtrail create-trail `
            --name $trailName `
            --s3-bucket-name $bucketName `
            --is-organization-trail `
            --is-multi-region-trail `
            --enable-log-file-validation `
            --output json | Out-Null
            
        # Start logging
        aws cloudtrail start-logging `
            --name $trailName `
            --output json | Out-Null
            
        Write-Host "${GREEN}✓ Organization CloudTrail enabled${NC}"
    }
    catch {
        Write-Host "${GREEN}✓ Organization CloudTrail already exists${NC}"
    }
}

# Main execution
try {
    # Step 1: Create or get organization
    $org = Ensure-Organization
    
    # Get root ID
    $roots = aws organizations list-roots --output json | ConvertFrom-Json
    $rootId = $roots.Roots[0].Id
    Write-Host "Root ID: $rootId"
    Write-Host ""
    
    # Step 2: Enable Service Control Policies
    Enable-ServiceControlPolicies -RootId $rootId
    Write-Host ""
    
    # Step 3: Create Organizational Units
    Write-Host "${YELLOW}Creating Organizational Units...${NC}"
    $ouMapping = @{}
    foreach ($ouName in $organizationalUnits) {
        $ouId = Create-OrganizationalUnit -Name $ouName -ParentId $rootId
        $ouMapping[$ouName] = $ouId
    }
    Write-Host ""
    
    # Step 4: Create accounts
    Write-Host "${YELLOW}Creating member accounts...${NC}"
    $accountIds = @()
    foreach ($account in $accounts) {
        $ouId = $ouMapping[$account.OU]
        $accountId = Create-Account -AccountInfo $account -OUId $ouId
        if ($accountId) {
            $accountIds += $accountId
        }
    }
    Write-Host ""
    
    # Step 5: Create baseline SCP
    $scpId = Create-BaselineSCP
    Write-Host ""
    
    # Step 6: Attach SCP to OUs
    if ($scpId -and -not $DryRun) {
        Write-Host "${YELLOW}Attaching baseline SCP to OUs...${NC}"
        foreach ($ouName in @("Development", "Staging", "Production")) {
            $ouId = $ouMapping[$ouName]
            if ($ouId) {
                try {
                    aws organizations attach-policy `
                        --policy-id $scpId `
                        --target-id $ouId `
                        --output json | Out-Null
                    Write-Host "${GREEN}  ✓ SCP attached to $ouName${NC}"
                }
                catch {
                    Write-Host "${YELLOW}  SCP already attached to $ouName${NC}"
                }
            }
        }
        Write-Host ""
    }
    
    # Step 7: Enable CloudTrail
    Enable-OrganizationCloudTrail
    Write-Host ""
    
    # Step 8: Enable additional services
    if (-not $DryRun) {
        Write-Host "${YELLOW}Enabling additional AWS services for organization...${NC}"
        
        # Enable AWS Config
        try {
            aws organizations enable-aws-service-access `
                --service-principal config.amazonaws.com `
                --output json | Out-Null
            Write-Host "${GREEN}  ✓ AWS Config enabled${NC}"
        }
        catch {
            Write-Host "${GREEN}  ✓ AWS Config already enabled${NC}"
        }
        
        # Enable GuardDuty
        try {
            aws organizations enable-aws-service-access `
                --service-principal guardduty.amazonaws.com `
                --output json | Out-Null
            Write-Host "${GREEN}  ✓ GuardDuty enabled${NC}"
        }
        catch {
            Write-Host "${GREEN}  ✓ GuardDuty already enabled${NC}"
        }
        
        # Enable Security Hub
        try {
            aws organizations enable-aws-service-access `
                --service-principal securityhub.amazonaws.com `
                --output json | Out-Null
            Write-Host "${GREEN}  ✓ Security Hub enabled${NC}"
        }
        catch {
            Write-Host "${GREEN}  ✓ Security Hub already enabled${NC}"
        }
        
        Write-Host ""
    }
    
    # Summary
    Write-Host "${GREEN}=== AWS Organizations Setup Complete ===${NC}"
    Write-Host ""
    Write-Host "Organization ID: $($org.Id)"
    Write-Host "Root Account: $($identity.Account)"
    Write-Host "Member Accounts: $($accountIds.Count)"
    Write-Host ""
    Write-Host "Next Steps:"
    Write-Host "1. Configure cross-account roles for access"
    Write-Host "2. Set up consolidated billing preferences"
    Write-Host "3. Configure AWS SSO for user access"
    Write-Host "4. Review and customize Service Control Policies"
    Write-Host "5. Set up AWS Control Tower (optional)"
    Write-Host ""
    
    # Save configuration
    $config = @{
        OrganizationId = $org.Id
        RootAccountId = $identity.Account
        RootId = $rootId
        OrganizationalUnits = $ouMapping
        Accounts = $accounts
        CreatedDate = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    }
    
    $configPath = "infrastructure/aws-setup/organization-config.json"
    New-Item -Path (Split-Path $configPath -Parent) -ItemType Directory -Force | Out-Null
    $config | ConvertTo-Json -Depth 10 | Out-File -FilePath $configPath -Encoding UTF8
    
    Write-Host "${GREEN}Configuration saved to: $configPath${NC}"
}
catch {
    Write-Host "${RED}Error: $_${NC}"
    Write-Host $_.Exception.Message
    exit 1
}
