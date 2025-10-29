# AWS Direct CLI Usage Rule

## Overview
When working with AWS infrastructure, use the AWS CLI directly via PowerShell/Bash commands instead of MCP servers. This provides better control, transparency, and reliability.

## Rationale
- **Transparency**: Direct CLI commands show exactly what's happening
- **Debugging**: Easier to troubleshoot issues with verbose output
- **Flexibility**: Full access to all AWS CLI features and options
- **Reliability**: No dependency on MCP server availability or compatibility
- **Version Control**: Commands can be captured in scripts and documentation

## Implementation

### Always Use Direct AWS CLI Commands

**✅ CORRECT - Direct CLI:**
```powershell
# PowerShell
aws ec2 describe-instances --instance-ids i-01807b5e7a32986c5 --region us-east-1

# Bash
aws ec2 describe-instances --instance-ids i-01807b5e7a32986c5 --region us-east-1
```

**❌ AVOID - MCP Server:**
```
Using mcp_aws_* tools (less control, potential compatibility issues)
```

## AWS CLI Setup Verification

Before using AWS CLI, verify installation and credentials:

```powershell
# Check AWS CLI is installed
aws --version

# Verify credentials are configured
aws sts get-caller-identity

# Set region if needed
$env:AWS_DEFAULT_REGION = "us-east-1"
```

## Common AWS Operations

### EC2 Instance Management

```powershell
# Launch instance
aws ec2 run-instances `
  --image-id ami-XXXXXXXX `
  --instance-type t3a.medium `
  --key-name my-key-pair `
  --security-group-ids sg-XXXXXXXX `
  --subnet-id subnet-XXXXXXXX `
  --region us-east-1

# Describe instances
aws ec2 describe-instances `
  --instance-ids i-XXXXXXXX `
  --region us-east-1

# Stop instance
aws ec2 stop-instances --instance-ids i-XXXXXXXX --region us-east-1

# Start instance
aws ec2 start-instances --instance-ids i-XXXXXXXX --region us-east-1

# Terminate instance
aws ec2 terminate-instances --instance-ids i-XXXXXXXX --region us-east-1
```

### Security Groups

```powershell
# Create security group
aws ec2 create-security-group `
  --group-name my-sg `
  --description "My security group" `
  --vpc-id vpc-XXXXXXXX `
  --region us-east-1

# Add ingress rule
aws ec2 authorize-security-group-ingress `
  --group-id sg-XXXXXXXX `
  --protocol tcp `
  --port 22 `
  --cidr 1.2.3.4/32 `
  --region us-east-1
```

### SSH Key Pairs

```powershell
# Create key pair
aws ec2 create-key-pair `
  --key-name my-key `
  --region us-east-1 `
  --query 'KeyMaterial' `
  --output text | Out-File -FilePath "my-key.pem" -Encoding ASCII

# Fix permissions (Windows)
icacls "my-key.pem" /inheritance:r
icacls "my-key.pem" /grant:r "$env:USERNAME:(R)"

# Fix permissions (Unix)
chmod 400 my-key.pem
```

### Debugging and Troubleshooting

```powershell
# Get console output
aws ec2 get-console-output `
  --instance-id i-XXXXXXXX `
  --region us-east-1 `
  --latest

# Check instance status
aws ec2 describe-instance-status `
  --instance-ids i-XXXXXXXX `
  --region us-east-1

# Get instance details with specific fields
aws ec2 describe-instances `
  --instance-ids i-XXXXXXXX `
  --region us-east-1 `
  --query 'Reservations[0].Instances[0].{State:State.Name,IP:PublicIpAddress,Type:InstanceType}'
```

## Error Handling

Always check for errors and provide meaningful output:

```powershell
# PowerShell example with error handling
try {
    $result = aws ec2 describe-instances --instance-ids $instanceId --region $region 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "AWS CLI command failed: $result"
    }
    Write-Host "✅ Command succeeded" -ForegroundColor Green
    return $result
} catch {
    Write-Host "❌ Error: $_" -ForegroundColor Red
    exit 1
}
```

## Scripting Best Practices

1. **Always specify region**: Use `--region` flag or `$env:AWS_DEFAULT_REGION`
2. **Use output formats**: `--output json|text|table` as appropriate
3. **Save important IDs**: Store instance IDs, security group IDs in files
4. **Log all commands**: Keep a record of infrastructure changes
5. **Use query parameter**: Filter output with `--query` for specific data

## Integration with Project

- Store AWS-related scripts in `.aws-deployment/` folder
- Save infrastructure IDs in `.aws-deployment/*.txt` files
- Keep deployment logs in `Project-Management/AWS-Deployment/`
- Add `.aws-deployment/` to `.gitignore` (except scripts)

## Related Files

- See `Global-Scripts/aws-helpers.ps1` for reusable AWS CLI wrapper functions
- See project's `.aws-deployment/` folder for deployment-specific scripts

---

**Version**: 1.0  
**Last Updated**: October 2025  
**Applies To**: All projects using AWS infrastructure


