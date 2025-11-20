#!/usr/bin/env pwsh
# AWS SSO Setup Script
# Part of TASK-001: AWS Account Setup
# Configures AWS SSO for centralized user access management

param(
    [Parameter(Mandatory=$false)]
    [string]$IdentityStoreRegion = "us-east-1",
    
    [Parameter(Mandatory=$false)]
    [string]$ConfigFile = "infrastructure/aws-setup/organization-config.json",
    
    [Parameter(Mandatory=$false)]
    [switch]$DryRun = $false
)

$ErrorActionPreference = "Stop"

# Colors for output
$GREEN = "`e[32m"
$YELLOW = "`e[33m"
$RED = "`e[31m"
$NC = "`e[0m"

Write-Host "${GREEN}=== AWS SSO Setup ===${NC}"
Write-Host "Identity Store Region: $IdentityStoreRegion"
Write-Host ""

# Load organization config
if (Test-Path $ConfigFile) {
    Write-Host "Loading organization config from: $ConfigFile"
    $orgConfig = Get-Content $ConfigFile -Raw | ConvertFrom-Json
    Write-Host "${GREEN}✓ Config loaded${NC}"
}
else {
    Write-Host "${RED}✗ No config file found${NC}"
    Write-Host "Please run setup-aws-organizations.ps1 first"
    exit 1
}

# Define permission sets
$permissionSets = @(
    @{
        Name = "AdministratorAccess"
        Description = "Full administrative access to AWS services"
        SessionDuration = "PT4H"
        ManagedPolicies = @("arn:aws:iam::aws:policy/AdministratorAccess")
    },
    @{
        Name = "PowerUserAccess"
        Description = "Full access except IAM and Organizations"
        SessionDuration = "PT8H"
        ManagedPolicies = @("arn:aws:iam::aws:policy/PowerUserAccess")
    },
    @{
        Name = "DeveloperAccess"
        Description = "Developer access for AI Core development"
        SessionDuration = "PT8H"
        ManagedPolicies = @(
            "arn:aws:iam::aws:policy/AmazonEC2FullAccess",
            "arn:aws:iam::aws:policy/AmazonS3FullAccess",
            "arn:aws:iam::aws:policy/AmazonECS_FullAccess",
            "arn:aws:iam::aws:policy/AWSLambda_FullAccess"
        )
        InlinePolicy = @{
            Version = "2012-10-17"
            Statement = @(
                @{
                    Effect = "Allow"
                    Action = @(
                        "eks:*",
                        "ecr:*",
                        "cloudwatch:*",
                        "logs:*",
                        "dynamodb:*",
                        "rds:*",
                        "elasticache:*"
                    )
                    Resource = "*"
                }
            )
        }
    },
    @{
        Name = "MLOpsAccess"
        Description = "ML operations and model deployment access"
        SessionDuration = "PT4H"
        ManagedPolicies = @(
            "arn:aws:iam::aws:policy/AmazonSageMakerFullAccess"
        )
        InlinePolicy = @{
            Version = "2012-10-17"
            Statement = @(
                @{
                    Effect = "Allow"
                    Action = @(
                        "ecr:*",
                        "s3:*",
                        "cloudwatch:*",
                        "logs:*",
                        "iam:PassRole",
                        "ec2:Describe*",
                        "ec2:CreateTags"
                    )
                    Resource = "*"
                }
            )
        }
    },
    @{
        Name = "ReadOnlyAccess"
        Description = "Read-only access to all AWS services"
        SessionDuration = "PT12H"
        ManagedPolicies = @("arn:aws:iam::aws:policy/ReadOnlyAccess")
    },
    @{
        Name = "SecurityAuditAccess"
        Description = "Security auditing and compliance access"
        SessionDuration = "PT4H"
        ManagedPolicies = @(
            "arn:aws:iam::aws:policy/SecurityAudit"
        )
        InlinePolicy = @{
            Version = "2012-10-17"
            Statement = @(
                @{
                    Effect = "Allow"
                    Action = @(
                        "guardduty:*",
                        "securityhub:*",
                        "access-analyzer:*",
                        "cloudtrail:LookupEvents",
                        "config:*"
                    )
                    Resource = "*"
                }
            )
        }
    },
    @{
        Name = "BillingAccess"
        Description = "Billing and cost management access"
        SessionDuration = "PT2H"
        ManagedPolicies = @(
            "arn:aws:iam::aws:policy/job-function/Billing"
        )
    }
)

# Define user groups
$userGroups = @(
    @{
        Name = "Administrators"
        Description = "AI Core system administrators"
        PermissionSets = @("AdministratorAccess")
        Accounts = @("ALL")
    },
    @{
        Name = "PlatformEngineers"
        Description = "Platform and infrastructure engineers"
        PermissionSets = @("PowerUserAccess", "ReadOnlyAccess")
        Accounts = @("ai-core-dev", "ai-core-staging", "ai-core-prod")
    },
    @{
        Name = "Developers"
        Description = "AI Core developers"
        PermissionSets = @("DeveloperAccess", "ReadOnlyAccess")
        Accounts = @("ai-core-dev", "ai-core-staging")
    },
    @{
        Name = "MLOpsEngineers"
        Description = "Machine learning operations engineers"
        PermissionSets = @("MLOpsAccess", "DeveloperAccess", "ReadOnlyAccess")
        Accounts = @("ai-core-dev", "ai-core-staging", "ai-core-prod")
    },
    @{
        Name = "SecurityAuditors"
        Description = "Security and compliance auditors"
        PermissionSets = @("SecurityAuditAccess", "ReadOnlyAccess")
        Accounts = @("ALL")
    },
    @{
        Name = "FinanceTeam"
        Description = "Finance and billing team"
        PermissionSets = @("BillingAccess", "ReadOnlyAccess")
        Accounts = @("ai-core-billing")
    }
)

# Function to check if SSO is enabled
function Test-SSOEnabled {
    try {
        $ssoInstances = aws sso-admin list-instances --output json 2>$null | ConvertFrom-Json
        if ($ssoInstances.Instances.Count -gt 0) {
            return $ssoInstances.Instances[0]
        }
        return $null
    }
    catch {
        return $null
    }
}

# Function to enable SSO
function Enable-SSO {
    Write-Host "${YELLOW}Checking AWS SSO status...${NC}"
    
    $ssoInstance = Test-SSOEnabled
    if ($ssoInstance) {
        Write-Host "${GREEN}✓ AWS SSO is already enabled${NC}"
        Write-Host "  Instance ARN: $($ssoInstance.InstanceArn)"
        Write-Host "  Identity Store ID: $($ssoInstance.IdentityStoreId)"
        return $ssoInstance
    }
    
    Write-Host "${YELLOW}AWS SSO needs to be enabled manually${NC}"
    Write-Host ""
    Write-Host "To enable AWS SSO:"
    Write-Host "1. Go to AWS SSO Console: https://console.aws.amazon.com/singlesignon"
    Write-Host "2. Click 'Enable AWS SSO'"
    Write-Host "3. Choose identity source (AWS SSO / Active Directory / External IdP)"
    Write-Host "4. Run this script again after enabling"
    Write-Host ""
    
    if (-not $DryRun) {
        exit 1
    }
    
    return @{
        InstanceArn = "arn:aws:sso:::instance/ssoins-dryrun"
        IdentityStoreId = "d-dryrun123"
    }
}

# Function to create permission set
function Create-PermissionSet {
    param(
        [hashtable]$PermissionSet,
        [string]$InstanceArn
    )
    
    Write-Host "  Creating permission set: $($PermissionSet.Name)"
    
    # Check if permission set exists
    $existingSets = aws sso-admin list-permission-sets `
        --instance-arn $InstanceArn `
        --output json | ConvertFrom-Json
        
    # Get details of each permission set to find by name
    $found = $false
    foreach ($psArn in $existingSets.PermissionSets) {
        $psDetails = aws sso-admin describe-permission-set `
            --instance-arn $InstanceArn `
            --permission-set-arn $psArn `
            --output json 2>$null | ConvertFrom-Json
            
        if ($psDetails.PermissionSet.Name -eq $PermissionSet.Name) {
            Write-Host "${GREEN}    ✓ Permission set already exists${NC}"
            $found = $true
            $permissionSetArn = $psArn
            break
        }
    }
    
    if (-not $found) {
        if ($DryRun) {
            Write-Host "${YELLOW}    [DRY RUN] Would create permission set${NC}"
            return "arn:aws:sso:::permissionSet/ssoins-dryrun/ps-dryrun"
        }
        
        # Create permission set
        $ps = aws sso-admin create-permission-set `
            --instance-arn $InstanceArn `
            --name $PermissionSet.Name `
            --description $PermissionSet.Description `
            --session-duration $PermissionSet.SessionDuration `
            --output json | ConvertFrom-Json
            
        $permissionSetArn = $ps.PermissionSet.PermissionSetArn
        Write-Host "${GREEN}    ✓ Permission set created${NC}"
        
        # Attach managed policies
        foreach ($policyArn in $PermissionSet.ManagedPolicies) {
            Write-Host "    Attaching policy: $policyArn"
            
            aws sso-admin attach-managed-policy-to-permission-set `
                --instance-arn $InstanceArn `
                --permission-set-arn $permissionSetArn `
                --managed-policy-arn $policyArn `
                --output json | Out-Null
        }
        
        # Add inline policy if defined
        if ($PermissionSet.InlinePolicy) {
            Write-Host "    Adding inline policy"
            
            $policyDoc = $PermissionSet.InlinePolicy | ConvertTo-Json -Depth 10 -Compress
            
            aws sso-admin put-inline-policy-to-permission-set `
                --instance-arn $InstanceArn `
                --permission-set-arn $permissionSetArn `
                --inline-policy $policyDoc `
                --output json | Out-Null
        }
        
        Write-Host "${GREEN}    ✓ Permission set configured${NC}"
    }
    
    return $permissionSetArn
}

# Function to create user group
function Create-UserGroup {
    param(
        [hashtable]$Group,
        [string]$IdentityStoreId
    )
    
    Write-Host "  Creating group: $($Group.Name)"
    
    # Check if group exists
    $existingGroups = aws identitystore list-groups `
        --identity-store-id $IdentityStoreId `
        --filters "AttributePath=DisplayName,AttributeValue=$($Group.Name)" `
        --output json 2>$null | ConvertFrom-Json
        
    if ($existingGroups.Groups.Count -gt 0) {
        Write-Host "${GREEN}    ✓ Group already exists${NC}"
        return $existingGroups.Groups[0].GroupId
    }
    
    if ($DryRun) {
        Write-Host "${YELLOW}    [DRY RUN] Would create group${NC}"
        return "group-dryrun-123"
    }
    
    # Create group
    $group = aws identitystore create-group `
        --identity-store-id $IdentityStoreId `
        --display-name $Group.Name `
        --description $Group.Description `
        --output json | ConvertFrom-Json
        
    Write-Host "${GREEN}    ✓ Group created: $($group.GroupId)${NC}"
    return $group.GroupId
}

# Function to create account assignments
function Create-AccountAssignments {
    param(
        [string]$InstanceArn,
        [string]$GroupId,
        [array]$PermissionSetArns,
        [array]$AccountIds
    )
    
    Write-Host "    Creating account assignments..."
    
    foreach ($accountId in $AccountIds) {
        foreach ($psArn in $PermissionSetArns) {
            if ($DryRun) {
                Write-Host "${YELLOW}      [DRY RUN] Would assign to account $accountId${NC}"
                continue
            }
            
            try {
                aws sso-admin create-account-assignment `
                    --instance-arn $InstanceArn `
                    --target-id $accountId `
                    --target-type AWS_ACCOUNT `
                    --permission-set-arn $psArn `
                    --principal-type GROUP `
                    --principal-id $GroupId `
                    --output json | Out-Null
                    
                Write-Host "${GREEN}      ✓ Assigned to account $accountId${NC}"
            }
            catch {
                # Assignment might already exist
                Write-Host "${YELLOW}      Assignment already exists for account $accountId${NC}"
            }
        }
    }
}

# Main execution
try {
    # Check if running in organization root account
    $identity = aws sts get-caller-identity --output json | ConvertFrom-Json
    if ($identity.Account -ne $orgConfig.RootAccountId) {
        Write-Host "${RED}✗ This script must be run from the organization root account${NC}"
        Write-Host "Current account: $($identity.Account)"
        Write-Host "Root account: $($orgConfig.RootAccountId)"
        exit 1
    }
    
    # Enable or verify SSO
    $ssoInstance = Enable-SSO
    $instanceArn = $ssoInstance.InstanceArn
    $identityStoreId = $ssoInstance.IdentityStoreId
    
    Write-Host ""
    
    # Create permission sets
    Write-Host "${YELLOW}Creating permission sets...${NC}"
    $permissionSetMapping = @{}
    
    foreach ($ps in $permissionSets) {
        $psArn = Create-PermissionSet -PermissionSet $ps -InstanceArn $instanceArn
        $permissionSetMapping[$ps.Name] = $psArn
    }
    
    Write-Host ""
    
    # Get account list
    Write-Host "${YELLOW}Getting AWS accounts...${NC}"
    $accounts = aws organizations list-accounts --output json | ConvertFrom-Json
    $accountMapping = @{}
    
    foreach ($account in $accounts.Accounts) {
        if ($account.Status -eq "ACTIVE") {
            $accountMapping[$account.Name] = $account.Id
            Write-Host "  $($account.Name): $($account.Id)"
        }
    }
    
    Write-Host ""
    
    # Create groups and assignments
    Write-Host "${YELLOW}Creating user groups and assignments...${NC}"
    
    foreach ($group in $userGroups) {
        # Create group
        $groupId = Create-UserGroup -Group $group -IdentityStoreId $identityStoreId
        
        # Get permission set ARNs
        $psArns = @()
        foreach ($psName in $group.PermissionSets) {
            if ($permissionSetMapping.ContainsKey($psName)) {
                $psArns += $permissionSetMapping[$psName]
            }
        }
        
        # Get account IDs
        $accountIds = @()
        foreach ($accountRef in $group.Accounts) {
            if ($accountRef -eq "ALL") {
                $accountIds = $accountMapping.Values
            }
            elseif ($accountMapping.ContainsKey($accountRef)) {
                $accountIds += $accountMapping[$accountRef]
            }
        }
        
        # Create assignments
        if ($psArns.Count -gt 0 -and $accountIds.Count -gt 0) {
            Create-AccountAssignments `
                -InstanceArn $instanceArn `
                -GroupId $groupId `
                -PermissionSetArns $psArns `
                -AccountIds $accountIds
        }
    }
    
    Write-Host ""
    
    # Save SSO configuration
    $ssoConfig = @{
        InstanceArn = $instanceArn
        IdentityStoreId = $identityStoreId
        IdentityStoreRegion = $IdentityStoreRegion
        PermissionSets = $permissionSetMapping
        Groups = $userGroups
        CreatedDate = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    }
    
    $configPath = "infrastructure/aws-setup/sso-config.json"
    $ssoConfig | ConvertTo-Json -Depth 10 | Out-File -FilePath $configPath -Encoding UTF8
    
    Write-Host "${GREEN}SSO configuration saved to: $configPath${NC}"
    Write-Host ""
    
    # Generate SSO portal URL
    $ssoPortal = aws sso-admin describe-instance `
        --instance-arn $instanceArn `
        --query 'PortalUrl' `
        --output text
        
    Write-Host "${GREEN}=== AWS SSO Setup Complete ===${NC}"
    Write-Host ""
    Write-Host "SSO Portal URL: $ssoPortal"
    Write-Host ""
    Write-Host "Next Steps:"
    Write-Host "1. Add users to the identity store (SSO console or external IdP)"
    Write-Host "2. Add users to appropriate groups"
    Write-Host "3. Share SSO portal URL with users"
    Write-Host "4. Users can access assigned accounts via SSO portal"
    Write-Host ""
    Write-Host "To add a user to a group:"
    Write-Host "  aws identitystore create-group-membership \"
    Write-Host "    --identity-store-id $identityStoreId \"
    Write-Host "    --group-id <GROUP_ID> \"
    Write-Host "    --member-id UserId=<USER_ID>"
}
catch {
    Write-Host "${RED}Error: $_${NC}"
    Write-Host $_.Exception.Message
    exit 1
}
