# Network Infrastructure

This directory contains the infrastructure code for the AI Core network foundation (TASK-002).

## Architecture Overview

The network infrastructure provides:

### VPC Design
- **CIDR**: 10.0.0.0/16 (65,536 IP addresses)
- **Availability Zones**: 3 (us-east-1a, us-east-1b, us-east-1c)
- **Subnet Types**:
  - Public Subnets: For load balancers and NAT gateways
  - Private Subnets: For application workloads (ECS, EKS)
  - Database Subnets: For RDS and ElastiCache

### Network Components
1. **Internet Gateway**: For public internet access
2. **NAT Gateways**: One per AZ for high availability
3. **Route Tables**: Separate for public and private subnets
4. **VPC Endpoints**: For AWS service access without internet traffic
5. **Security Groups**: Least-privilege network access control
6. **VPC Flow Logs**: For network traffic monitoring

### Security Groups
- **ALB**: Allows HTTP/HTTPS from internet
- **ECS**: Allows traffic from ALB and inter-task communication
- **RDS**: Allows PostgreSQL from ECS/EKS
- **ElastiCache**: Allows Redis from ECS/EKS
- **NATS**: Allows NATS protocols from ECS
- **Bastion**: Allows SSH from specified IP ranges

## Deployment

### Using PowerShell Script
```powershell
# Deploy VPC infrastructure
.\create-vpc-infrastructure.ps1 -Environment dev -Region us-east-1

# Deploy to production
.\create-vpc-infrastructure.ps1 -Environment prod -Region us-east-1
```

### Using Terraform
```bash
cd terraform

# Initialize Terraform
terraform init

# Review planned changes
terraform plan

# Apply configuration
terraform apply

# For production
terraform workspace new prod
terraform plan -var="environment=prod"
terraform apply -var="environment=prod"
```

## Configuration

### PowerShell Script Parameters
- `-Environment`: Environment name (dev, staging, prod)
- `-Region`: AWS region (default: us-east-1)
- `-VpcCidr`: VPC CIDR block (default: 10.0.0.0/16)
- `-DryRun`: Preview changes without creating resources

### Terraform Variables
Edit `terraform/terraform.tfvars`:
```hcl
project               = "ai-core"
environment          = "dev"
region               = "us-east-1"
vpc_cidr             = "10.0.0.0/16"
enable_nat_gateway   = true
enable_flow_logs     = true
bastion_allowed_cidrs = ["YOUR_IP/32"]
```

## Outputs

The infrastructure creates:
- VPC ID and CIDR block
- Subnet IDs for each tier
- Security group IDs
- VPC endpoint IDs
- Route table IDs

These outputs are saved to:
- PowerShell: `vpc-config-{environment}.json`
- Terraform: Use `terraform output` command

## Cost Optimization

### NAT Gateway Costs
- NAT Gateways: ~$45/month per gateway (3 gateways = ~$135/month)
- Data processing: $0.045 per GB

### Cost Saving Options
1. **Development**: Use single NAT Gateway
2. **Staging**: Use NAT instances instead of NAT Gateways
3. **Production**: Keep 3 NAT Gateways for HA

To reduce costs in non-production:
```bash
# Use single NAT Gateway
terraform apply -var="single_nat_gateway=true"
```

## Monitoring

### VPC Flow Logs
- Stored in CloudWatch Logs
- Retention: 30 days
- Path: `/aws/vpc/flowlogs/ai-core-{environment}`

### Metrics
- NAT Gateway metrics in CloudWatch
- VPC endpoint metrics
- Network traffic patterns

## Security Considerations

1. **Network Isolation**: Private subnets have no direct internet access
2. **Least Privilege**: Security groups allow only required ports
3. **VPC Endpoints**: Reduce data transfer costs and improve security
4. **Flow Logs**: Enable network traffic analysis
5. **Encryption**: All VPC endpoints use TLS

## Next Steps

After VPC creation:
1. **TASK-003**: Deploy EKS cluster in private subnets
2. **TASK-004**: Create RDS Aurora cluster in database subnets
3. **TASK-005**: Set up ElastiCache in private subnets
4. Configure VPN or Direct Connect for secure access

## Troubleshooting

### Common Issues
1. **Subnet exhaustion**: Ensure CIDR blocks are large enough
2. **Route conflicts**: Check route table priorities
3. **Security group rules**: Verify source/destination rules
4. **VPC endpoint connectivity**: Ensure DNS resolution is enabled

### Debug Commands
```bash
# List VPCs
aws ec2 describe-vpcs --filters "Name=tag:Project,Values=AI-Core"

# Check NAT Gateway status
aws ec2 describe-nat-gateways --filter "Name=state,Values=available"

# View route tables
aws ec2 describe-route-tables --filters "Name=vpc-id,Values=vpc-xxx"

# Check security groups
aws ec2 describe-security-groups --filters "Name=vpc-id,Values=vpc-xxx"
```

## Compliance

This infrastructure follows AWS Well-Architected Framework:
- **Security**: Network isolation, encryption in transit
- **Reliability**: Multi-AZ deployment, high availability
- **Performance**: VPC endpoints for low latency
- **Cost Optimization**: Right-sized subnets, flow log retention
- **Operational Excellence**: Infrastructure as Code, monitoring

---

For questions or issues, refer to the main project documentation or contact the Platform Engineering team.
