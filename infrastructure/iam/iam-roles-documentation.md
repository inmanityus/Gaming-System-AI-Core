# AI Core IAM Roles Documentation

Generated: 2025-11-19 12:05:35

## Roles Created

### LambdaExecutionRole
- **Name**: `AICore-Lambda-ExecutionRole`
- **ARN**: `arn:aws:iam::695353648052:role/AICore-Lambda-ExecutionRole`
- **Purpose**: Role for Lambda functions in AI Core

### GlueJobRole
- **Name**: `AICore-Glue-JobRole`
- **ARN**: `arn:aws:iam::695353648052:role/AICore-Glue-JobRole`
- **Purpose**: Role for AWS Glue ETL jobs

### ECSTaskRole
- **Name**: `AICore-ECS-TaskRole`
- **ARN**: `arn:aws:iam::695353648052:role/AICore-ECS-TaskRole`
- **Purpose**: Role for ECS tasks to access AWS services

### SageMakerExecutionRole
- **Name**: `AICore-SageMaker-ExecutionRole`
- **ARN**: `arn:aws:iam::695353648052:role/AICore-SageMaker-ExecutionRole`
- **Purpose**: Role for SageMaker training and inference

### ECSTaskExecutionRole
- **Name**: `AICore-ECS-TaskExecutionRole`
- **ARN**: `arn:aws:iam::695353648052:role/AICore-ECS-TaskExecutionRole`
- **Purpose**: Role for ECS tasks to pull images and write logs

### DataEngineerRole
- **Name**: `AICore-DataEngineer-Role`
- **ARN**: `arn:aws:iam::695353648052:role/AICore-DataEngineer-Role`
- **Purpose**: Role for data engineers to manage ETL pipelines

### DataScientistRole
- **Name**: `AICore-DataScientist-Role`
- **ARN**: `arn:aws:iam::695353648052:role/AICore-DataScientist-Role`
- **Purpose**: Role for data scientists to analyze data

## Usage Examples

### ECS Task Definition
`json
{
  "family": "ai-core-service",
  "taskRoleArn": "arn:aws:iam::695353648052:role/AICore-ECS-TaskRole",
  "executionRoleArn": "arn:aws:iam::695353648052:role/AICore-ECS-TaskExecutionRole",
  "containerDefinitions": [...]
}
`

### Lambda Function
`ash
aws lambda create-function \
  --function-name ai-core-processor \
  --role "arn:aws:iam::695353648052:role/AICore-Lambda-ExecutionRole" \
  --runtime python3.9 \
  --handler index.handler
`

### SageMaker Training Job
`python
import sagemaker
from sagemaker.estimator import Estimator

estimator = Estimator(
    image_uri='your-ecr-uri',
    role='arn:aws:iam::695353648052:role/AICore-SageMaker-ExecutionRole',
    instance_count=1,
    instance_type='ml.m5.xlarge'
)
`

## Security Best Practices

1. **Least Privilege**: Each role has minimal required permissions
2. **Service Isolation**: Roles are service-specific
3. **No Wildcards**: Resources are explicitly defined where possible
4. **Regular Review**: Audit role usage monthly
5. **MFA Enforcement**: Require MFA for assumable roles

## Role Assumption

For human-assumable roles (DataScientist, DataEngineer), configure with:

`ash
aws sts assume-role \
  --role-arn <role-arn> \
  --role-session-name <your-session-name> \
  --duration-seconds 3600
`

## Compliance

- All roles tagged with Project, Environment, ManagedBy
- CloudTrail logs all role assumptions
- Regular access reviews required
- Roles follow naming convention: AICore-<Service>-<Type>

