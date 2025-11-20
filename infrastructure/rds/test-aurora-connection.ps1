param(
    [string]$SecretName = "rds/ai-core-aurora-cluster/master-credentials"
)

# Get credentials from Secrets Manager
$secret = aws secretsmanager get-secret-value --secret-id $SecretName --query SecretString --output text | ConvertFrom-Json

# Test connection using psql
$env:PGPASSWORD = $secret.password
psql -h $secret.host -U $secret.username -d $secret.database -c "SELECT version();"
psql -h $secret.readerHost -U $secret.username -d $secret.database -c "SELECT pg_is_in_recovery();"
