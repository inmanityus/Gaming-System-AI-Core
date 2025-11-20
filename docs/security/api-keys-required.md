# Required API Keys and Services

This document lists all API keys and external services required for the Gaming System AI Core.

## Essential API Keys

### 1. OpenAI API Key
- **Service**: OpenAI Direct API
- **Purpose**: GPT model access for AI services
- **Endpoint**: `https://api.openai.com/v1/`
- **Required For**: 
  - AI Integration Service
  - NPC Behavior Engine
  - Story Teller Service
- **Format**: `sk-proj-...` (48+ characters)
- **Get Key**: https://platform.openai.com/api-keys

### 2. OpenRouter API Key
- **Service**: OpenRouter AI Model Routing
- **Purpose**: Access to multiple AI models through single API
- **Endpoint**: `https://openrouter.ai/api/v1/`
- **Required For**: 
  - Model Management Service
  - Multi-tier AI routing
- **Format**: `sk-or-v1-...`
- **Get Key**: https://openrouter.ai/keys

### 3. Perplexity API Key
- **Service**: Perplexity AI Search
- **Purpose**: Real-time web search and information retrieval
- **Endpoint**: MCP service
- **Required For**: 
  - Knowledge Base Service
  - Real-time information queries
- **Format**: `pplx-...`
- **Get Key**: https://www.perplexity.ai/settings/api

### 4. Apify API Key
- **Service**: Web Scraping and Automation
- **Purpose**: Web scraping for knowledge updates
- **Required For**: 
  - Knowledge Base updates
  - Content monitoring
- **Format**: `apify_api_...`
- **Get Key**: https://console.apify.com/account/integrations

### 5. Exa API Key
- **Service**: Semantic Web Search
- **Purpose**: Advanced web search capabilities
- **Required For**: 
  - Knowledge Base Service
  - Code context search
- **Format**: Standard API key
- **Get Key**: https://exa.ai/

## AWS Service Credentials

### Required IAM Permissions
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecs:*",
        "ecr:*",
        "logs:*",
        "cloudwatch:*",
        "rds:Describe*",
        "elasticache:Describe*",
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "*"
    }
  ]
}
```

### Service-Specific AWS Resources

| Service | AWS Resource | Purpose |
|---------|--------------|---------|
| All Services | ECR Repository | Docker image storage |
| All Services | ECS Fargate | Container hosting |
| All Services | CloudWatch Logs | Logging |
| State Manager | RDS Aurora | PostgreSQL database |
| State Manager | ElastiCache | Redis cache |
| All Services | Secrets Manager | Credential storage |

## Environment Variables Mapping

```bash
# Core AI Services
OPENAI_API_KEY=<openai-key>
OPENROUTER_API_KEY=<openrouter-key>

# MCP Services
MCP_APIFY_API_KEY=<apify-key>
MCP_EXA_API_KEY=<exa-key>
MCP_PERPLEXITY_API_KEY=<perplexity-key>

# AWS Configuration
AWS_REGION=us-east-1
AWS_ACCOUNT_ID=695353648052

# Database Connections (from Secrets Manager)
DATABASE_URL=<from-secrets-manager>
REDIS_URL=<from-secrets-manager>

# Service Discovery
NATS_URL=nats://nats-server:4222
SERVICE_DISCOVERY_ENABLED=true

# Monitoring
CLOUDWATCH_NAMESPACE=Gaming/System/Services
ENABLE_XRAY_TRACING=true
```

## Service Dependencies

### Knowledge Base Service
- OpenAI API Key (for embeddings)
- Exa API Key (for search)
- PostgreSQL (for vector storage)

### AI Integration Service
- OpenAI API Key (primary)
- OpenRouter API Key (fallback)
- Redis (for caching)

### Language System Service
- OpenAI API Key (for NLU)
- Azure Speech Services (optional, for TTS)
- Google Cloud TTS (optional)

### NPC Behavior Service
- OpenAI API Key (for decision making)
- PostgreSQL (for state storage)
- Redis (for real-time state)

### Story Teller Service
- OpenAI API Key (for narrative generation)
- PostgreSQL (for story graphs)

### Orchestration Service
- All service API endpoints
- NATS messaging system
- Redis (for coordination)

## Security Best Practices

1. **Rotate Keys Quarterly**
   - Set calendar reminders
   - Update in AWS Secrets Manager
   - Redeploy services

2. **Use Separate Keys per Environment**
   - Development: Limited quotas
   - Staging: Production-like
   - Production: High quotas, monitoring

3. **Monitor Usage**
   - Set up billing alerts
   - Monitor API quotas
   - Track unusual patterns

4. **Access Control**
   - Limit who can access production keys
   - Use AWS IAM for service accounts
   - Enable MFA for key management

## Troubleshooting

### Missing API Key Errors
```bash
# Check if key is set
echo $OPENAI_API_KEY

# Test API connection
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### AWS Credential Errors
```bash
# Verify AWS credentials
aws sts get-caller-identity

# Test service access
aws ecs list-services --cluster gaming-system-cluster
```

### Service Connection Issues
- Check environment variables are loaded
- Verify network connectivity
- Confirm API quotas not exceeded
- Check CloudWatch logs for details
