# AI Core KMS Key Usage Guide

Generated: 2025-11-19 11:59:31

## Customer-Managed KMS Keys

### STORAGE Key
- **Alias**: `alias/ai-core-storage`
- **Key ID**: `3a42cd0a-b4e8-4845-a38b-1faa7b2d3ae7`
- **ARN**: `arn:aws:kms:us-east-1:695353648052:key/3a42cd0a-b4e8-4845-a38b-1faa7b2d3ae7`
- **Purpose**: KMS key for general S3 storage encryption

### EKS Key
- **Alias**: `alias/ai-core-eks`
- **Key ID**: `16bf11fc-66b8-4aeb-a56c-1c1586dc0c03`
- **ARN**: `arn:aws:kms:us-east-1:695353648052:key/16bf11fc-66b8-4aeb-a56c-1c1586dc0c03`
- **Purpose**: KMS key for EKS secrets encryption

### LOGS Key
- **Alias**: `alias/ai-core-logs`
- **Key ID**: `8db63b0c-c5fa-4bf0-a0e8-22dc489369b2`
- **ARN**: `arn:aws:kms:us-east-1:695353648052:key/8db63b0c-c5fa-4bf0-a0e8-22dc489369b2`
- **Purpose**: KMS key for CloudWatch Logs and CloudTrail encryption

### APPLICATION Key
- **Alias**: `alias/ai-core-application`
- **Key ID**: `f03810f0-4dfe-46e7-b2b6-35af5878886e`
- **ARN**: `arn:aws:kms:us-east-1:695353648052:key/f03810f0-4dfe-46e7-b2b6-35af5878886e`
- **Purpose**: KMS key for application secrets and configuration

### OPENSEARCH Key
- **Alias**: `alias/ai-core-opensearch`
- **Key ID**: `b9b71d60-2f0d-4ac5-b1fb-ea4d96a6564e`
- **ARN**: `arn:aws:kms:us-east-1:695353648052:key/b9b71d60-2f0d-4ac5-b1fb-ea4d96a6564e`
- **Purpose**: KMS key for OpenSearch domain encryption

### BACKUP Key
- **Alias**: `alias/ai-core-backup`
- **Key ID**: `c282f1ca-5281-4137-95f6-47356e000481`
- **ARN**: `arn:aws:kms:us-east-1:695353648052:key/c282f1ca-5281-4137-95f6-47356e000481`
- **Purpose**: KMS key for AWS Backup encryption

### DATABASE Key
- **Alias**: `alias/ai-core-database`
- **Key ID**: `4ade26b4-5401-45db-af90-197ff4eb9634`
- **ARN**: `arn:aws:kms:us-east-1:695353648052:key/4ade26b4-5401-45db-af90-197ff4eb9634`
- **Purpose**: KMS key for RDS Aurora and Redis encryption

## Service Configuration Examples

### RDS Aurora
`ash
aws rds modify-db-cluster \
    --db-cluster-identifier ai-core-aurora-cluster \
    --kms-key-id alias/ai-core-database \
    --apply-immediately
`

### ElastiCache Redis
`ash
aws elasticache modify-replication-group \
    --replication-group-id ai-core-redis-cluster \
    --kms-key-id arn:aws:kms:us-east-1:695353648052:key/4ade26b4-5401-45db-af90-197ff4eb9634 \
    --apply-immediately
`

### S3 Bucket
`ash
aws s3api put-bucket-encryption \
    --bucket my-bucket \
    --server-side-encryption-configuration '{
        "Rules": [{
            "ApplyServerSideEncryptionByDefault": {
                "SSEAlgorithm": "aws:kms",
                "KMSMasterKeyID": "alias/ai-core-storage"
            }
        }]
    }'
`

### Secrets Manager
`ash
aws secretsmanager update-secret \
    --secret-id my-secret \
    --kms-key-id alias/ai-core-application
`

### CloudWatch Logs
`ash
aws logs associate-kms-key \
    --log-group-name /aws/lambda/my-function \
    --kms-key-id arn:aws:kms:us-east-1:695353648052:key/8db63b0c-c5fa-4bf0-a0e8-22dc489369b2
`

## Best Practices

1. **Key Rotation**: All keys have automatic rotation enabled (annually)
2. **Key Policies**: Follow principle of least privilege
3. **Monitoring**: Set up CloudWatch alarms for key usage
4. **Backup**: Keys are backed up automatically by AWS
5. **Access**: Use IAM policies to control who can use keys

## Compliance

- All keys use AES-256 encryption
- FIPS 140-2 Level 2 validated
- Automatic rotation ensures key material freshness
- CloudTrail logging enabled for all key usage

