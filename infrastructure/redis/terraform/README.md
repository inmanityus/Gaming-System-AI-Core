# Redis Cluster Terraform Configuration

## Purpose

Deploys Amazon ElastiCache for Redis in cluster mode for the Gaming System AI Core. Provides distributed caching with sub-1ms latency for:

- Game state caching
- AI model weights and tokenizers
- LLM response caching
- NPC state and behavior caching

## Architecture

- **Mode**: Cluster mode enabled
- **Shards**: 3 (configurable)
- **Replicas**: 1 per shard (configurable)
- **Node Type**: cache.r7g.large (13.07 GiB memory)
- **Availability**: Multi-AZ with automatic failover
- **Encryption**: At-rest (KMS) + in-transit (TLS 1.2/1.3)
- **Authentication**: AUTH token (stored in Secrets Manager)

## Expected Performance

- **Latency**: <1ms p50, <2ms p99
- **Throughput**: 100K+ ops/sec per shard
- **Memory**: ~13 GiB per node × 3 shards = ~39 GiB total
- **Availability**: 99.99% (Multi-AZ)

## Prerequisites

- AWS VPC with private subnets (gaming-system-vpc)
- ECS tasks security group (gaming-system-ecs-tasks-sg)
- AWS credentials configured
- Terraform >= 1.0

## Deployment

```bash
cd infrastructure/redis/terraform

# Initialize Terraform
terraform init

# Review plan
terraform plan

# Deploy cluster
terraform apply

# Get outputs
terraform output redis_configuration_endpoint
terraform output redis_auth_token_secret_arn
```

## Configuration

### Node Types

| Type | vCPU | Memory | Network | Use Case |
|------|------|--------|---------|----------|
| cache.r7g.large | 2 | 13.07 GiB | Up to 10 Gbps | Default |
| cache.r7g.xlarge | 4 | 26.32 GiB | Up to 12 Gbps | High memory |
| cache.r7g.2xlarge | 8 | 52.82 GiB | Up to 15 Gbps | Very high memory |

### Sharding Strategy

- **3 shards (default)**: Balanced performance and cost
- **5+ shards**: For >200K ops/sec total throughput
- **1 shard**: Dev/test only (no horizontal scaling)

## Connection

### From ECS Services

```python
import redis.asyncio as redis
from aws_secretsmanager import get_secret

# Get auth token from Secrets Manager
secret = get_secret("gaming-system/redis-auth-token")
auth_token = secret["auth_token"]
endpoint = secret["endpoint"]

# Connect to cluster
client = redis.RedisCluster(
    host=endpoint,
    port=6379,
    ssl=True,
    password=auth_token,
    decode_responses=True,
    max_connections=50
)
```

## Monitoring

### CloudWatch Alarms

- **CPU > 75%**: Scale up or add shards
- **Memory > 85%**: Scale up or tune maxmemory-policy
- **Evictions > 100/5min**: Increase memory or tune TTLs

### Metrics to Monitor

- `CPUUtilization`: Target <75%
- `DatabaseMemoryUsagePercentage`: Target <85%
- `CacheHitRate`: Target >90%
- `NetworkBytesIn/Out`: Monitor for saturation
- `Evictions`: Should be near zero

## Cost

**Estimated Monthly Cost** (us-east-1):
- 3 shards × 2 nodes (1 primary + 1 replica) × cache.r7g.large
- ~$0.294/hour × 6 nodes × 730 hours = **~$1,288/month**

## Scaling

### Vertical (Node Size)

```bash
terraform apply -var="node_type=cache.r7g.xlarge"
```

### Horizontal (Shards)

```bash
terraform apply -var="num_shards=5"
```

## Security

- **Encryption at rest**: KMS CMK with automatic rotation
- **Encryption in transit**: TLS 1.2/1.3 required
- **Authentication**: AUTH token (32 chars, stored in Secrets Manager)
- **Network**: Private subnets only, ECS tasks SG whitelist
- **Logging**: Slow log + engine log → CloudWatch

## Backup & Recovery

- **Snapshots**: Daily at 02:00-03:00 UTC
- **Retention**: 5 days
- **Restore**: Create new cluster from snapshot

## Maintenance

- **Window**: Sunday 03:00-04:00 UTC
- **Auto minor upgrades**: Enabled
- **Patching**: Automatic during window

## Integration with NATS Migration

Redis cluster provides Layer 2 caching for NATS-based microservices:

1. **Layer 1**: In-process LRU (25-100ms TTL)
2. **Layer 2**: Redis Cluster (0.5-1ms latency)
3. **Layer 3**: PostgreSQL (persistent storage)

### Cache Patterns

```python
# World state cache
key = f"world:{world_id}:snapshot"
ttl = 5  # seconds

# NPC state cache
key = f"npc:{npc_id}:state"
ttl = 1  # seconds

# Model tokenizer cache
key = f"model:{model_id}:tokenizer"
ttl = 3600  # 1 hour
```

## Troubleshooting

### High Latency

1. Check CPU/memory usage
2. Review slow log for expensive commands
3. Verify network connectivity
4. Check for large keys (>1MB)

### Cache Misses

1. Review cache hit rate metric
2. Check TTLs
3. Verify key patterns
4. Monitor evictions

### Connection Issues

1. Verify security group rules
2. Check AUTH token
3. Verify TLS configuration
4. Review VPC/subnet configuration

## References

- [ElastiCache Redis Documentation](https://docs.aws.amazon.com/AmazonElastiCache/latest/red-ug/)
- [Redis Cluster Specification](https://redis.io/docs/reference/cluster-spec/)
- [NATS Binary Messaging Requirements](../../docs/architecture/BINARY-MESSAGING-REQUIREMENTS.md)

