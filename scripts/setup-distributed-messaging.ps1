# Setup Distributed Messaging Infrastructure (SNS/SQS)
# Creates SNS topics and SQS queues for microservice event-driven architecture

param(
    [string]$Region = "us-east-1",
    [string]$Project = "gaming-system"
)

$ErrorActionPreference = "Stop"

Write-Host "=== Setting Up Distributed Messaging Infrastructure ===" -ForegroundColor Cyan
Write-Host "Region: $Region" -ForegroundColor White
Write-Host "Project: $Project" -ForegroundColor White
Write-Host ""

# Step 1: Create SNS Topic
Write-Host "[1/5] Creating SNS topic for weather events..." -ForegroundColor Yellow
$topicArn = aws sns create-topic `
    --name "$Project-weather-events" `
    --region $Region `
    --tags Key=Project,Value=GamingSystemAICore Key=Service,Value=weather-manager `
    --query "TopicArn" `
    --output text 2>&1

if ($LASTEXITCODE -ne 0) {
    if ($topicArn -like "*already exists*") {
        Write-Host "  ℹ Topic already exists, fetching ARN..." -ForegroundColor Yellow
        $topicArn = aws sns list-topics --region $Region --query "Topics[?contains(TopicArn, '$Project-weather-events')].TopicArn | [0]" --output text
    } else {
        Write-Host "  ✗ Failed to create SNS topic: $topicArn" -ForegroundColor Red
        exit 1
    }
}

Write-Host "  ✓ SNS Topic ARN: $topicArn" -ForegroundColor Green
Write-Host ""

# Step 2: Create SQS Queue for weather-manager
Write-Host "[2/5] Creating SQS queue for weather-manager..." -ForegroundColor Yellow
$queueUrl = aws sqs create-queue `
    --queue-name "$Project-weather-manager-events" `
    --region $Region `
    --attributes "VisibilityTimeout=300,MessageRetentionPeriod=1209600,ReceiveMessageWaitTimeSeconds=20" `
    --tags Project=GamingSystemAICore,Service=weather-manager `
    --query "QueueUrl" `
    --output text 2>&1

if ($LASTEXITCODE -ne 0) {
    if ($queueUrl -like "*already exists*") {
        Write-Host "  ℹ Queue already exists, fetching URL..." -ForegroundColor Yellow
        $queueUrl = aws sqs get-queue-url --queue-name "$Project-weather-manager-events" --region $Region --query "QueueUrl" --output text
    } else {
        Write-Host "  ✗ Failed to create SQS queue: $queueUrl" -ForegroundColor Red
        exit 1
    }
}

Write-Host "  ✓ SQS Queue URL: $queueUrl" -ForegroundColor Green
Write-Host ""

# Get queue ARN
$queueArn = aws sqs get-queue-attributes `
    --queue-url $queueUrl `
    --region $Region `
    --attribute-names QueueArn `
    --query "Attributes.QueueArn" `
    --output text

Write-Host "  ✓ SQS Queue ARN: $queueArn" -ForegroundColor Green
Write-Host ""

# Step 3: Grant SNS permission to send messages to SQS
Write-Host "[3/5] Configuring queue policy to allow SNS..." -ForegroundColor Yellow

$queuePolicy = @"
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {
      "Service": "sns.amazonaws.com"
    },
    "Action": "sqs:SendMessage",
    "Resource": "$queueArn",
    "Condition": {
      "ArnEquals": {
        "aws:SourceArn": "$topicArn"
      }
    }
  }]
}
"@ -replace "`r`n", "`n"

$queuePolicy | Out-File -FilePath ".cursor/aws/queue-policy.json" -Encoding UTF8 -NoNewline

aws sqs set-queue-attributes `
    --queue-url $queueUrl `
    --region $Region `
    --attributes "Policy=$($queuePolicy -replace '"', '\"')" 2>&1 | Out-Null

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Queue policy configured" -ForegroundColor Green
} else {
    Write-Host "  ✗ Failed to set queue policy" -ForegroundColor Red
}
Write-Host ""

# Step 4: Subscribe SQS queue to SNS topic
Write-Host "[4/5] Subscribing queue to SNS topic..." -ForegroundColor Yellow
$subscriptionArn = aws sns subscribe `
    --topic-arn $topicArn `
    --protocol sqs `
    --notification-endpoint $queueArn `
    --region $Region `
    --query "SubscriptionArn" `
    --output text 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "  ✓ Subscription ARN: $subscriptionArn" -ForegroundColor Green
} else {
    if ($subscriptionArn -like "*already exists*") {
        Write-Host "  ℹ Subscription already exists" -ForegroundColor Yellow
    } else {
        Write-Host "  ✗ Failed to subscribe: $subscriptionArn" -ForegroundColor Red
    }
}
Write-Host ""

# Step 5: Create/Update IAM policy for ECS tasks
Write-Host "[5/5] Creating IAM policy for ECS tasks..." -ForegroundColor Yellow

$accountId = aws sts get-caller-identity --query "Account" --output text

$iamPolicy = @"
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sns:Publish"
      ],
      "Resource": "$topicArn"
    },
    {
      "Effect": "Allow",
      "Action": [
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes",
        "sqs:GetQueueUrl"
      ],
      "Resource": "$queueArn"
    }
  ]
}
"@

$iamPolicy | Out-File -FilePath ".cursor/aws/distributed-messaging-policy.json" -Encoding UTF8

$policyArn = "arn:aws:iam::${accountId}:policy/GamingSystemDistributedMessaging"

# Check if policy exists
$policyExists = aws iam get-policy --policy-arn $policyArn 2>&1
if ($LASTEXITCODE -ne 0) {
    # Create new policy
    $policyArn = aws iam create-policy `
        --policy-name "GamingSystemDistributedMessaging" `
        --policy-document "file://.cursor/aws/distributed-messaging-policy.json" `
        --description "Allows ECS tasks to publish/subscribe to distributed messaging" `
        --tags Key=Project,Value=GamingSystemAICore `
        --query "Policy.Arn" `
        --output text

    Write-Host "  ✓ Created IAM policy: $policyArn" -ForegroundColor Green
} else {
    # Update existing policy
    $versions = aws iam list-policy-versions --policy-arn $policyArn --query "Versions[?IsDefaultVersion==``false``].VersionId" --output text
    foreach ($version in $versions -split "`t") {
        aws iam delete-policy-version --policy-arn $policyArn --version-id $version 2>&1 | Out-Null
    }
    
    aws iam create-policy-version `
        --policy-arn $policyArn `
        --policy-document "file://.cursor/aws/distributed-messaging-policy.json" `
        --set-as-default 2>&1 | Out-Null
    
    Write-Host "  ✓ Updated IAM policy: $policyArn" -ForegroundColor Green
}
Write-Host ""

# Summary
Write-Host "=== ✅ Infrastructure Setup Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "📋 Resource Details:" -ForegroundColor Cyan
Write-Host "  SNS Topic ARN:" -ForegroundColor White
Write-Host "    $topicArn" -ForegroundColor Gray
Write-Host ""
Write-Host "  SQS Queue URL:" -ForegroundColor White
Write-Host "    $queueUrl" -ForegroundColor Gray
Write-Host ""
Write-Host "  IAM Policy ARN:" -ForegroundColor White
Write-Host "    $policyArn" -ForegroundColor Gray
Write-Host ""

# Generate environment variables for ECS
Write-Host "📝 Environment Variables for ECS Task Definition:" -ForegroundColor Cyan
Write-Host @"
{
  "name": "WEATHER_EVENTS_TOPIC_ARN",
  "value": "$topicArn"
},
{
  "name": "WEATHER_MANAGER_QUEUE_URL",
  "value": "$queueUrl"
},
{
  "name": "AWS_REGION",
  "value": "$Region"
}
"@ -ForegroundColor Yellow
Write-Host ""

# Generate IAM role attachment command
Write-Host "🔐 To attach policy to ECS task role:" -ForegroundColor Cyan
Write-Host "aws iam attach-role-policy ``" -ForegroundColor Yellow
Write-Host "  --role-name ecsTaskExecutionRole ``" -ForegroundColor Yellow
Write-Host "  --policy-arn $policyArn" -ForegroundColor Yellow
Write-Host ""

Write-Host "✅ Setup complete! Update your ECS task definition with the environment variables above." -ForegroundColor Green

