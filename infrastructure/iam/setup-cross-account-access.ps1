param(
    [string]$TrustedAccountId = "",  # Account ID that will assume roles
    [string]$ExternalId = (New-Guid).Guid,  # Random external ID for additional security
    [switch]$ReadOnly = $false
)

if (-not $TrustedAccountId) {
    Write-Host "[ERROR] TrustedAccountId is required" -ForegroundColor Red
    Write-Host "Usage: .\setup-cross-account-access.ps1 -TrustedAccountId <ACCOUNT_ID> [-ReadOnly]" -ForegroundColor Yellow
    exit 1
}

Write-Host "=== Setting up Cross-Account Access ===" -ForegroundColor Cyan
Write-Host "Trusted Account: $TrustedAccountId" -ForegroundColor Yellow
Write-Host "External ID: $ExternalId" -ForegroundColor Yellow
Write-Host "Access Level: $(if ($ReadOnly) { 'Read-Only' } else { 'Full Access' })" -ForegroundColor Yellow

$currentAccountId = aws sts get-caller-identity --query Account --output text

# Define cross-account roles
$crossAccountRoles = @{
    "ReadOnlyAccess" = @{
        name = "AICore-CrossAccount-ReadOnly"
        description = "Read-only access for cross-account monitoring and auditing"
        policies = @(
            "arn:aws:iam::aws:policy/ReadOnlyAccess",
            "arn:aws:iam::aws:policy/CloudWatchReadOnlyAccess",
            "arn:aws:iam::aws:policy/CloudWatchLogsReadOnlyAccess"
        )
    }
    "SecurityAudit" = @{
        name = "AICore-CrossAccount-SecurityAudit"
        description = "Security audit access for compliance scanning"
        policies = @(
            "arn:aws:iam::aws:policy/SecurityAudit"
        )
    }
    "DevOpsAccess" = @{
        name = "AICore-CrossAccount-DevOps"
        description = "DevOps access for deployment and management"
        policies = @()  # Will use inline policy
        inline_policy = @{
            Version = "2012-10-17"
            Statement = @(
                @{
                    Effect = "Allow"
                    Action = @(
                        "ecs:*",
                        "eks:*",
                        "lambda:*",
                        "s3:*",
                        "rds:Describe*",
                        "elasticache:Describe*",
                        "cloudformation:*",
                        "cloudwatch:*",
                        "logs:*",
                        "iam:GetRole",
                        "iam:GetRolePolicy",
                        "iam:ListRolePolicies",
                        "iam:ListAttachedRolePolicies"
                    )
                    Resource = "*"
                },
                @{
                    Effect = "Deny"
                    Action = @(
                        "iam:CreateAccessKey",
                        "iam:DeleteAccessKey",
                        "iam:UpdateAccessKey",
                        "iam:CreateUser",
                        "iam:DeleteUser",
                        "iam:CreateRole",
                        "iam:DeleteRole",
                        "iam:AttachUserPolicy",
                        "iam:DetachUserPolicy",
                        "iam:PutUserPolicy",
                        "iam:DeleteUserPolicy"
                    )
                    Resource = "*"
                }
            )
        }
    }
}

# Create trust policy for cross-account access
$trustPolicy = @{
    Version = "2012-10-17"
    Statement = @(
        @{
            Effect = "Allow"
            Principal = @{
                AWS = "arn:aws:iam::${TrustedAccountId}:root"
            }
            Action = "sts:AssumeRole"
            Condition = @{
                StringEquals = @{
                    "sts:ExternalId" = $ExternalId
                }
            }
        }
    )
} | ConvertTo-Json -Depth 10

$trustPolicy | Out-File -FilePath "cross-account-trust-policy.json" -Encoding UTF8

# Array to store created role information
$createdCrossAccountRoles = @()

# Create roles based on access level
$rolesToCreate = if ($ReadOnly) { 
    @("ReadOnlyAccess", "SecurityAudit") 
} else { 
    @("ReadOnlyAccess", "SecurityAudit", "DevOpsAccess") 
}

foreach ($roleType in $rolesToCreate) {
    $roleConfig = $crossAccountRoles[$roleType]
    Write-Host "`nCreating role: $($roleConfig.name)" -ForegroundColor Yellow
    Write-Host "  Purpose: $($roleConfig.description)" -ForegroundColor Gray
    
    # Check if role already exists
    $existingRole = aws iam get-role --role-name $roleConfig.name 2>$null
    
    if ($LASTEXITCODE -ne 0) {
        # Create the role
        $roleResult = aws iam create-role `
            --role-name $roleConfig.name `
            --assume-role-policy-document file://cross-account-trust-policy.json `
            --description $roleConfig.description `
            --output json | ConvertFrom-Json
        
        $roleArn = $roleResult.Role.Arn
        Write-Host "✓ Created role: $roleArn" -ForegroundColor Green
        
        # Attach managed policies
        foreach ($policyArn in $roleConfig.policies) {
            aws iam attach-role-policy `
                --role-name $roleConfig.name `
                --policy-arn $policyArn | Out-Null
            Write-Host "  ✓ Attached policy: $policyArn" -ForegroundColor Green
        }
        
        # Create inline policy if specified
        if ($roleConfig.inline_policy) {
            $inlinePolicyJson = $roleConfig.inline_policy | ConvertTo-Json -Depth 10
            $inlinePolicyJson | Out-File -FilePath "inline-policy-$roleType.json" -Encoding UTF8
            
            aws iam put-role-policy `
                --role-name $roleConfig.name `
                --policy-name "${roleType}Policy" `
                --policy-document file://inline-policy-$roleType.json | Out-Null
            
            Write-Host "  ✓ Created inline policy" -ForegroundColor Green
            
            Remove-Item "inline-policy-$roleType.json"
        }
        
        # Tag the role
        $tags = @(
            @{ Key = "Project"; Value = "AI-Core" },
            @{ Key = "Purpose"; Value = "CrossAccountAccess" },
            @{ Key = "TrustedAccount"; Value = $TrustedAccountId },
            @{ Key = "ManagedBy"; Value = "PowerShell" }
        ) | ConvertTo-Json -Compress
        
        aws iam tag-role --role-name $roleConfig.name --tags $tags | Out-Null
        
        $createdCrossAccountRoles += @{
            type = $roleType
            name = $roleConfig.name
            arn = $roleArn
            description = $roleConfig.description
        }
        
    } else {
        Write-Host "✓ Role already exists (updating trust policy)" -ForegroundColor Yellow
        
        # Update trust policy
        aws iam update-assume-role-policy `
            --role-name $roleConfig.name `
            --policy-document file://cross-account-trust-policy.json | Out-Null
        
        $roleInfo = $existingRole | ConvertFrom-Json
        
        $createdCrossAccountRoles += @{
            type = $roleType
            name = $roleConfig.name
            arn = $roleInfo.Role.Arn
            description = $roleConfig.description
        }
    }
}

Remove-Item "cross-account-trust-policy.json"

# Create documentation for the trusted account
$trustedAccountDoc = @"
# Cross-Account Access Configuration

## Account Information
- **This Account ID**: $currentAccountId
- **External ID**: $ExternalId
- **Roles Created**: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

## How to Assume Roles

From the trusted account ($TrustedAccountId), use these commands:

### Read-Only Access
```bash
aws sts assume-role \
  --role-arn "arn:aws:iam::${currentAccountId}:role/AICore-CrossAccount-ReadOnly" \
  --role-session-name "ReadOnlySession" \
  --external-id "$ExternalId"
```

### Security Audit Access
```bash
aws sts assume-role \
  --role-arn "arn:aws:iam::${currentAccountId}:role/AICore-CrossAccount-SecurityAudit" \
  --role-session-name "SecurityAuditSession" \
  --external-id "$ExternalId"
```

"@

if (-not $ReadOnly) {
    $trustedAccountDoc += @"
### DevOps Access
```bash
aws sts assume-role \
  --role-arn "arn:aws:iam::${currentAccountId}:role/AICore-CrossAccount-DevOps" \
  --role-session-name "DevOpsSession" \
  --external-id "$ExternalId"
```

"@
}

$trustedAccountDoc += @"

## Using Assumed Role Credentials

After assuming a role, export the temporary credentials:

```bash
# Example output from assume-role command
export AWS_ACCESS_KEY_ID=<AssumedRoleAccessKeyId>
export AWS_SECRET_ACCESS_KEY=<AssumedRoleSecretAccessKey>
export AWS_SESSION_TOKEN=<AssumedRoleSessionToken>
```

Or use AWS CLI profiles:

```ini
# ~/.aws/config
[profile ai-core-readonly]
role_arn = arn:aws:iam::${currentAccountId}:role/AICore-CrossAccount-ReadOnly
source_profile = default
external_id = $ExternalId

[profile ai-core-audit]
role_arn = arn:aws:iam::${currentAccountId}:role/AICore-CrossAccount-SecurityAudit
source_profile = default
external_id = $ExternalId
```

Then use: `aws s3 ls --profile ai-core-readonly`

## Security Notes

1. **External ID Required**: The external ID ($ExternalId) must be provided when assuming roles
2. **Session Duration**: Default is 1 hour, maximum is 12 hours
3. **MFA**: Consider requiring MFA for sensitive operations
4. **Audit**: All role assumptions are logged in CloudTrail

## Permissions Summary

"@

foreach ($role in $createdCrossAccountRoles) {
    $trustedAccountDoc += @"

### $($role.name)
- **Type**: $($role.type)
- **ARN**: $($role.arn)
- **Purpose**: $($role.description)

"@
}

$trustedAccountDoc | Out-File -FilePath "cross-account-access-guide-${TrustedAccountId}.md" -Encoding UTF8

# Save configuration
$crossAccountConfig = @{
    trusted_account_id = $TrustedAccountId
    this_account_id = $currentAccountId
    external_id = $ExternalId
    roles = $createdCrossAccountRoles
    read_only = $ReadOnly
    created_at = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
} | ConvertTo-Json -Depth 5

$crossAccountConfig | Out-File -FilePath "cross-account-config-${TrustedAccountId}.json" -Encoding UTF8

Write-Host "`n=== Cross-Account Access Setup Complete ===" -ForegroundColor Green
Write-Host "`nRoles created:" -ForegroundColor Cyan
foreach ($role in $createdCrossAccountRoles) {
    Write-Host "  - $($role.name)" -ForegroundColor White
}

Write-Host "`n=== Important Information ===" -ForegroundColor Cyan
Write-Host "External ID: $ExternalId" -ForegroundColor Yellow -BackgroundColor DarkRed
Write-Host "`nThis External ID is REQUIRED to assume the roles!" -ForegroundColor Yellow
Write-Host "Save this ID securely - it cannot be retrieved later" -ForegroundColor Yellow

Write-Host "`n=== Next Steps ===" -ForegroundColor Cyan
Write-Host "1. Share 'cross-account-access-guide-${TrustedAccountId}.md' with the trusted account owner"
Write-Host "2. Test role assumption from the trusted account"
Write-Host "3. Set up CloudWatch alerts for role usage"
Write-Host "4. Configure AWS Config rules for compliance monitoring"
Write-Host "5. Review and audit cross-account access quarterly"
