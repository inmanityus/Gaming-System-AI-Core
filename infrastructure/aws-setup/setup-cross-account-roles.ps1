#!/usr/bin/env pwsh
# Cross-Account Role Setup Script
# Part of TASK-001: AWS Account Setup
# Creates IAM roles for cross-account access in the multi-account structure

param(
    [Parameter(Mandatory=$false)]
    [string]$ConfigFile = "infrastructure/aws-setup/organization-config.json",
    
    [Parameter(Mandatory=$false)]
    [string]$RootAccountId,
    
    [Parameter(Mandatory=$false)]
    [switch]$DryRun = $false
)

$ErrorActionPreference = "Stop"

# Colors for output
$GREEN = "`e[32m"
$YELLOW = "`e[33m"
$RED = "`e[31m"
$NC = "`e[0m"

Write-Host "${GREEN}=== Cross-Account Role Setup ===${NC}"
Write-Host ""

# Load organization config
if (Test-Path $ConfigFile) {
    Write-Host "Loading organization config from: $ConfigFile"
    $orgConfig = Get-Content $ConfigFile -Raw | ConvertFrom-Json
    if (-not $RootAccountId) {
        $RootAccountId = $orgConfig.RootAccountId
    }
    Write-Host "${GREEN}✓ Config loaded${NC}"
}
else {
    if (-not $RootAccountId) {
        Write-Host "${RED}✗ No config file found and no root account ID provided${NC}"
        exit 1
    }
}

Write-Host "Root Account ID: $RootAccountId"
Write-Host ""

# Define roles to create
$roles = @(
    @{
        Name = "OrganizationAccountAccessRole"
        Description = "Role for organization root account to access member accounts"
        MaxDuration = 14400  # 4 hours
        Policies = @(
            "arn:aws:iam::aws:policy/AdministratorAccess"
        )
    },
    @{
        Name = "AICoreDeveloperRole"
        Description = "Role for developers to access development resources"
        MaxDuration = 28800  # 8 hours
        Policies = @(
            "arn:aws:iam::aws:policy/PowerUserAccess"
        )
        CustomPolicy = @{
            Version = "2012-10-17"
            Statement = @(
                @{
                    Effect = "Deny"
                    Action = @(
                        "iam:CreateAccessKey",
                        "iam:DeleteAccessKey",
                        "organizations:*",
                        "account:*"
                    )
                    Resource = "*"
                }
            )
        }
    },
    @{
        Name = "AICoreReadOnlyRole"
        Description = "Role for read-only access to resources"
        MaxDuration = 43200  # 12 hours
        Policies = @(
            "arn:aws:iam::aws:policy/ReadOnlyAccess"
        )
    },
    @{
        Name = "AICoreMLOpsRole"
        Description = "Role for ML operations and model deployment"
        MaxDuration = 14400  # 4 hours
        Policies = @()
        CustomPolicy = @{
            Version = "2012-10-17"
            Statement = @(
                @{
                    Effect = "Allow"
                    Action = @(
                        "sagemaker:*",
                        "ecr:*",
                        "s3:*",
                        "cloudwatch:*",
                        "logs:*",
                        "ec2:Describe*",
                        "ec2:CreateTags",
                        "iam:PassRole"
                    )
                    Resource = "*"
                },
                @{
                    Effect = "Allow"
                    Action = @(
                        "eks:*"
                    )
                    Resource = "*"
                    Condition = @{
                        StringLike = @{
                            "eks:cluster-name" = "ai-core-*"
                        }
                    }
                }
            )
        }
    },
    @{
        Name = "AICoreSecurityAuditorRole"
        Description = "Role for security auditing and compliance"
        MaxDuration = 14400  # 4 hours
        Policies = @(
            "arn:aws:iam::aws:policy/SecurityAudit"
        )
        CustomPolicy = @{
            Version = "2012-10-17"
            Statement = @(
                @{
                    Effect = "Allow"
                    Action = @(
                        "cloudtrail:LookupEvents",
                        "guardduty:Get*",
                        "guardduty:List*",
                        "securityhub:Get*",
                        "securityhub:List*",
                        "config:Get*",
                        "config:List*",
                        "config:Describe*",
                        "access-analyzer:*"
                    )
                    Resource = "*"
                }
            )
        }
    }
)

# Function to create trust policy
function Get-TrustPolicy {
    param(
        [string]$TrustedAccountId,
        [string]$ExternalId = $null
    )
    
    $trustPolicy = @{
        Version = "2012-10-17"
        Statement = @(
            @{
                Effect = "Allow"
                Principal = @{
                    AWS = "arn:aws:iam::${TrustedAccountId}:root"
                }
                Action = "sts:AssumeRole"
            }
        )
    }
    
    if ($ExternalId) {
        $trustPolicy.Statement[0].Condition = @{
            StringEquals = @{
                "sts:ExternalId" = $ExternalId
            }
        }
    }
    
    return $trustPolicy | ConvertTo-Json -Depth 10
}

# Function to create role
function Create-CrossAccountRole {
    param(
        [hashtable]$RoleConfig,
        [string]$TrustedAccountId
    )
    
    Write-Host "  Creating role: $($RoleConfig.Name)"
    
    # Check if role exists
    try {
        $existingRole = aws iam get-role --role-name $RoleConfig.Name --output json 2>$null | ConvertFrom-Json
        if ($existingRole) {
            Write-Host "${GREEN}    ✓ Role already exists${NC}"
            return
        }
    }
    catch {
        # Role doesn't exist, proceed to create
    }
    
    if ($DryRun) {
        Write-Host "${YELLOW}    [DRY RUN] Would create role${NC}"
        return
    }
    
    # Generate external ID for additional security
    $externalId = [System.Guid]::NewGuid().ToString()
    
    # Create trust policy
    $trustPolicy = Get-TrustPolicy -TrustedAccountId $TrustedAccountId -ExternalId $externalId
    
    # Create the role
    $role = aws iam create-role `
        --role-name $RoleConfig.Name `
        --assume-role-policy-document $trustPolicy `
        --description $RoleConfig.Description `
        --max-session-duration $RoleConfig.MaxDuration `
        --output json | ConvertFrom-Json
        
    Write-Host "${GREEN}    ✓ Role created${NC}"
    
    # Attach managed policies
    foreach ($policyArn in $RoleConfig.Policies) {
        Write-Host "    Attaching policy: $policyArn"
        aws iam attach-role-policy `
            --role-name $RoleConfig.Name `
            --policy-arn $policyArn `
            --output json | Out-Null
    }
    
    # Create and attach custom policy if defined
    if ($RoleConfig.CustomPolicy) {
        $policyName = "$($RoleConfig.Name)Policy"
        Write-Host "    Creating custom policy: $policyName"
        
        $policyDoc = $RoleConfig.CustomPolicy | ConvertTo-Json -Depth 10
        
        $policy = aws iam create-policy `
            --policy-name $policyName `
            --policy-document $policyDoc `
            --description "Custom policy for $($RoleConfig.Name)" `
            --output json | ConvertFrom-Json
            
        aws iam attach-role-policy `
            --role-name $RoleConfig.Name `
            --policy-arn $policy.Policy.Arn `
            --output json | Out-Null
            
        Write-Host "${GREEN}    ✓ Custom policy attached${NC}"
    }
    
    # Save role configuration
    $roleInfo = @{
        RoleName = $RoleConfig.Name
        RoleArn = $role.Role.Arn
        ExternalId = $externalId
        TrustedAccount = $TrustedAccountId
        CreatedDate = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    }
    
    return $roleInfo
}

# Function to create IAM users in root account for assuming roles
function Create-AssumeRoleUsers {
    Write-Host "${YELLOW}Creating IAM users in root account...${NC}"
    
    $users = @(
        @{
            UserName = "ai-core-admin"
            Groups = @("Administrators")
            Roles = @("OrganizationAccountAccessRole")
        },
        @{
            UserName = "ai-core-developer"
            Groups = @("Developers")
            Roles = @("AICoreDeveloperRole", "AICoreReadOnlyRole")
        },
        @{
            UserName = "ai-core-mlops"
            Groups = @("MLOps")
            Roles = @("AICoreMLOpsRole", "AICoreReadOnlyRole")
        },
        @{
            UserName = "ai-core-auditor"
            Groups = @("SecurityAuditors")
            Roles = @("AICoreSecurityAuditorRole", "AICoreReadOnlyRole")
        }
    )
    
    foreach ($user in $users) {
        Write-Host "  Creating user: $($user.UserName)"
        
        # Check if user exists
        try {
            $existingUser = aws iam get-user --user-name $user.UserName --output json 2>$null | ConvertFrom-Json
            if ($existingUser) {
                Write-Host "${GREEN}    ✓ User already exists${NC}"
                continue
            }
        }
        catch {
            # User doesn't exist, create it
        }
        
        if ($DryRun) {
            Write-Host "${YELLOW}    [DRY RUN] Would create user${NC}"
            continue
        }
        
        # Create user
        aws iam create-user `
            --user-name $user.UserName `
            --tags "Key=Purpose,Value=AI-Core" `
            --output json | Out-Null
            
        Write-Host "${GREEN}    ✓ User created${NC}"
        
        # Create groups if they don't exist
        foreach ($groupName in $user.Groups) {
            try {
                aws iam get-group --group-name $groupName --output json 2>$null | Out-Null
            }
            catch {
                Write-Host "    Creating group: $groupName"
                aws iam create-group --group-name $groupName --output json | Out-Null
            }
            
            # Add user to group
            aws iam add-user-to-group `
                --user-name $user.UserName `
                --group-name $groupName `
                --output json | Out-Null
        }
    }
}

# Function to create assume role policy for users
function Create-AssumeRolePolicy {
    param([array]$AccountIds)
    
    Write-Host "${YELLOW}Creating assume role policies...${NC}"
    
    if ($DryRun) {
        Write-Host "${YELLOW}[DRY RUN] Would create assume role policies${NC}"
        return
    }
    
    # Create policy for each role type
    $rolePolicies = @{
        "AssumeAdminRolePolicy" = @{
            Roles = @("OrganizationAccountAccessRole")
            Groups = @("Administrators")
        }
        "AssumeDeveloperRolePolicy" = @{
            Roles = @("AICoreDeveloperRole", "AICoreReadOnlyRole")
            Groups = @("Developers")
        }
        "AssumeMLOpsRolePolicy" = @{
            Roles = @("AICoreMLOpsRole", "AICoreReadOnlyRole")
            Groups = @("MLOps")
        }
        "AssumeAuditorRolePolicy" = @{
            Roles = @("AICoreSecurityAuditorRole", "AICoreReadOnlyRole")
            Groups = @("SecurityAuditors")
        }
    }
    
    foreach ($policyName in $rolePolicies.Keys) {
        $policyInfo = $rolePolicies[$policyName]
        
        Write-Host "  Creating policy: $policyName"
        
        # Build resource list
        $resources = @()
        foreach ($accountId in $AccountIds) {
            foreach ($roleName in $policyInfo.Roles) {
                $resources += "arn:aws:iam::${accountId}:role/$roleName"
            }
        }
        
        $policyDoc = @{
            Version = "2012-10-17"
            Statement = @(
                @{
                    Effect = "Allow"
                    Action = "sts:AssumeRole"
                    Resource = $resources
                }
            )
        } | ConvertTo-Json -Depth 10
        
        # Check if policy exists
        try {
            $existingPolicy = aws iam get-policy `
                --policy-arn "arn:aws:iam::${RootAccountId}:policy/$policyName" `
                --output json 2>$null | ConvertFrom-Json
                
            if ($existingPolicy) {
                Write-Host "${GREEN}    ✓ Policy already exists${NC}"
                $policyArn = $existingPolicy.Policy.Arn
            }
        }
        catch {
            # Create policy
            $policy = aws iam create-policy `
                --policy-name $policyName `
                --policy-document $policyDoc `
                --description "Allow assuming roles in member accounts" `
                --output json | ConvertFrom-Json
                
            $policyArn = $policy.Policy.Arn
            Write-Host "${GREEN}    ✓ Policy created${NC}"
        }
        
        # Attach to groups
        foreach ($groupName in $policyInfo.Groups) {
            try {
                aws iam attach-group-policy `
                    --group-name $groupName `
                    --policy-arn $policyArn `
                    --output json | Out-Null
                    
                Write-Host "${GREEN}    ✓ Policy attached to group: $groupName${NC}"
            }
            catch {
                Write-Host "${YELLOW}    Policy already attached to group: $groupName${NC}"
            }
        }
    }
}

# Main execution
try {
    # Get current account ID
    $currentAccount = aws sts get-caller-identity --output json | ConvertFrom-Json
    $currentAccountId = $currentAccount.Account
    
    Write-Host "Current Account: $currentAccountId"
    
    # Determine if we're in the root account
    if ($currentAccountId -eq $RootAccountId) {
        Write-Host "${GREEN}✓ Running in root account${NC}"
        Write-Host ""
        
        # Create IAM users and groups
        Create-AssumeRoleUsers
        Write-Host ""
        
        # Get list of member accounts
        Write-Host "${YELLOW}Getting member accounts...${NC}"
        $accounts = aws organizations list-accounts --output json | ConvertFrom-Json
        $memberAccounts = $accounts.Accounts | Where-Object { $_.Id -ne $RootAccountId -and $_.Status -eq "ACTIVE" }
        
        Write-Host "Found $($memberAccounts.Count) member accounts"
        Write-Host ""
        
        # Create assume role policies
        $accountIds = $memberAccounts | ForEach-Object { $_.Id }
        Create-AssumeRolePolicy -AccountIds $accountIds
        Write-Host ""
        
        # Save role switching configuration
        Write-Host "${YELLOW}Generating role switching configuration...${NC}"
        
        $roleSwitchConfig = @()
        foreach ($account in $memberAccounts) {
            foreach ($role in $roles) {
                $config = @"
[profile $($account.Name)-$($role.Name)]
role_arn = arn:aws:iam::$($account.Id):role/$($role.Name)
source_profile = default
role_session_name = ai-core-session
"@
                $roleSwitchConfig += $config
            }
        }
        
        $configPath = "infrastructure/aws-setup/aws-config-profiles"
        New-Item -Path (Split-Path $configPath -Parent) -ItemType Directory -Force | Out-Null
        $roleSwitchConfig -join "`n`n" | Out-File -FilePath $configPath -Encoding UTF8
        
        Write-Host "${GREEN}✓ AWS CLI profiles saved to: $configPath${NC}"
        Write-Host "  Add to ~/.aws/config to use role switching"
        Write-Host ""
    }
    else {
        # Running in a member account
        Write-Host "${YELLOW}Running in member account${NC}"
        Write-Host "Creating cross-account roles..."
        Write-Host ""
        
        $roleConfigs = @()
        foreach ($role in $roles) {
            $roleInfo = Create-CrossAccountRole -RoleConfig $role -TrustedAccountId $RootAccountId
            if ($roleInfo) {
                $roleConfigs += $roleInfo
            }
        }
        
        # Save role configuration
        if ($roleConfigs.Count -gt 0) {
            $configPath = "infrastructure/aws-setup/cross-account-roles-$currentAccountId.json"
            $roleConfigs | ConvertTo-Json -Depth 10 | Out-File -FilePath $configPath -Encoding UTF8
            
            Write-Host ""
            Write-Host "${GREEN}Role configuration saved to: $configPath${NC}"
        }
    }
    
    Write-Host ""
    Write-Host "${GREEN}=== Cross-Account Role Setup Complete ===${NC}"
    Write-Host ""
    Write-Host "Next Steps:"
    if ($currentAccountId -eq $RootAccountId) {
        Write-Host "1. Run this script in each member account to create roles"
        Write-Host "2. Distribute AWS CLI profile configuration to users"
        Write-Host "3. Create access keys for IAM users (if using CLI)"
        Write-Host "4. Configure AWS SSO for browser-based access"
    }
    else {
        Write-Host "1. Share role External IDs with root account administrators"
        Write-Host "2. Test role assumption from root account"
        Write-Host "3. Configure additional role permissions as needed"
    }
}
catch {
    Write-Host "${RED}Error: $_${NC}"
    Write-Host $_.Exception.Message
    exit 1
}
