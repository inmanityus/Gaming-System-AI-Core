# Operational Stack - Monitoring, Security, Disaster Recovery
**Date**: January 29, 2025  
**Service**: Cross-Cutting Operational Concerns  
**Status**: Integrated into Solution

---

## OVERVIEW

Complete operational infrastructure for monitoring, security, and disaster recovery across all 8 services.

---

## OBSERVABILITY STACK

### Distributed Tracing

**Stack**: OpenTelemetry → Jaeger/Tempo

**Implementation**:
```python
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# Initialize tracing
trace.set_tracer_provider(TracerProvider())
jaeger_exporter = JaegerExporter(
    agent_host_name="jaeger",
    agent_port=6831,
)
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(jaeger_exporter)
)

# Auto-instrument FastAPI
FastAPIInstrumentor.instrument_app(app)
```

**What We Track**:
- Request flow: Game Client → AI Inference → Orchestration → State Management
- Latency per service (p50, p95, p99)
- Error propagation across services
- Cache hit/miss rates
- Cost per request type

**Correlation IDs**: Every request gets unique trace ID for end-to-end tracking

---

### Metrics Collection

**Stack**: Prometheus → Grafana Dashboards

**Implementation**:
```python
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi import FastAPI, Response

# Define metrics
request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_latency = Histogram(
    'http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint'],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)

ai_latency = Histogram(
    'ai_inference_latency_seconds',
    'AI inference latency by layer',
    ['layer', 'model'],
    buckets=[0.1, 0.2, 0.5, 1.0, 2.0, 5.0]
)

cost_per_request = Gauge(
    'cost_per_request_usd',
    'Cost per request in USD',
    ['service', 'request_type']
)

active_connections = Gauge(
    'active_connections',
    'Active connections per service',
    ['service']
)

# FastAPI endpoint for metrics
@app.get("/metrics")
async def metrics():
    return Response(content=generate_latest(), media_type="text/plain")
```

**Key Metrics**:
- Request rate (requests/sec)
- Latency percentiles (p50, p95, p99)
- Error rate (% of failed requests)
- Cache hit rate (%)
- Cost per request (USD)
- Active connections per service
- Database query latency
- LLM inference latency by layer

**Grafana Dashboards**:
- Service health overview
- Latency breakdown by service
- Cost tracking and projections
- Cache performance
- Database performance
- Error rate trends

---

### Centralized Logging

**Stack**: Fluent Bit → Elasticsearch → Kibana

**Implementation**:
```python
import logging
import json
from pythonjsonlogger import jsonlogger

# Configure structured JSON logging
log_handler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter(
    '%(timestamp)s %(level)s %(name)s %(message)s'
)
log_handler.setFormatter(formatter)

logger = logging.getLogger()
logger.addHandler(log_handler)
logger.setLevel(logging.INFO)

# Log with structured data
logger.info("AI inference started", extra={
    "layer": "layer3",
    "model": "claude-4.5",
    "request_id": request_id,
    "user_id": user_id,
    "tier": user_tier
})
```

**Log Retention**:
- Application logs: 30 days
- Access logs: 90 days
- Security logs: 1 year
- Audit logs: 7 years (compliance)

**Log Aggregation**:
- All services write to stdout/stderr
- Fluent Bit collects and forwards to Elasticsearch
- Kibana provides search and visualization

---

### Alerting

**Stack**: Alertmanager → PagerDuty/Slack

**Critical Alerts**:
- P99 latency > threshold (400ms for Layer 3, 1500ms for Layer 4)
- Error rate > 1%
- Cost per hour > budget threshold
- Service down (health check failures)
- Database connection pool exhaustion
- Cache hit rate < 80%
- Disk space > 80%

**Alert Routing**:
- Critical → PagerDuty (on-call engineer)
- Warning → Slack (#alerts channel)
- Info → Slack (#monitoring channel)

---

## SECURITY ARCHITECTURE

### Web Application Firewall (WAF)

**Protection For**:
- All HTTP endpoints (Game Client, Admin UI, Public APIs)
- DDoS protection
- Rate limiting per IP
- SQL injection prevention
- XSS prevention

**Implementation**: AWS WAF or Cloudflare WAF in front of API Gateway

**Rules**:
- Rate limit: 100 requests/min per IP
- Block suspicious patterns
- Geo-blocking (if needed)
- IP allowlist for internal services

---

### Authentication & Authorization

**User Authentication**:
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt

security = HTTPBearer()

async def verify_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=["HS256"]
        )
        user_id = payload.get("sub")
        tier = payload.get("tier")
        return {"user_id": user_id, "tier": tier}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

@app.get("/api/v1/dialogue")
async def get_dialogue(
    user: dict = Depends(verify_token)
):
    # Check tier for rate limiting
    if user["tier"] == "free" and exceeds_rate_limit(user["user_id"]):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )
    # Process request
```

**Service-to-Service Authentication**:
```python
import grpc
import ssl

# mTLS for gRPC
credentials = grpc.ssl_channel_credentials(
    root_certificates=open('ca-cert.pem', 'rb').read(),
    private_key=open('client-key.pem', 'rb').read(),
    certificate_chain=open('client-cert.pem', 'rb').read()
)

channel = grpc.secure_channel(
    'service:50051',
    credentials
)
```

---

### Input Sanitization

**Pre-LLM Call Validation**:
```python
import re
from typing import List

def sanitize_input(user_input: str, max_length: int = 1000) -> str:
    # Remove control characters
    cleaned = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', user_input)
    
    # Limit length
    cleaned = cleaned[:max_length]
    
    # Check for prompt injection patterns
    injection_patterns = [
        r'ignore\s+previous\s+instructions',
        r'system\s*:\s*',
        r'<\s*script',
        # Add more patterns
    ]
    
    for pattern in injection_patterns:
        if re.search(pattern, cleaned, re.IGNORECASE):
            raise ValueError("Potential prompt injection detected")
    
    return cleaned.strip()

# Usage before LLM call
sanitized = sanitize_input(user_prompt)
response = await llm.generate(sanitized)
```

---

### Output Validation

**Post-LLM Response Validation**:
```python
def validate_llm_response(response: str, max_length: int = 5000) -> bool:
    # Length check
    if len(response) > max_length:
        return False
    
    # Check for malicious content
    malicious_patterns = [
        r'<script',
        r'javascript:',
        r'eval\(',
        # Add more patterns
    ]
    
    for pattern in malicious_patterns:
        if re.search(pattern, response, re.IGNORECASE):
            return False
    
    return True

# Usage after LLM call
if not validate_llm_response(llm_response):
    llm_response = get_safe_fallback_response()
```

---

## DISASTER RECOVERY

### Tiered Recovery Strategy ⭐ **UPDATED - RTO/RPO Specified**

**Tier 1: Player Data (Critical)** - 🔴 **P0 Priority**
- **RPO (Recovery Point Objective)**: **5 minutes**
  - Maximum acceptable data loss: 5 minutes of player progress
  - Continuous WAL replication to standby
  - Transaction log shipping every 30 seconds
- **RTO (Recovery Time Objective)**: **15 minutes (automated), 1 hour (manual)**
  - Automated failover: PostgreSQL streaming replication → 15 minutes
  - Manual intervention: Database recovery from backup → 1 hour
  - **Failover Trigger**: Primary failure detected via health check (30s interval)
  - **Who Authorizes**: Automated system, on-call engineer for manual
- **Backup**: Continuous replication to standby PostgreSQL
- **Restore**: Point-in-time recovery from WAL logs

**Tier 2: AI Models** - 🟡 **P1 Priority**
- **RPO**: **1 hour**
  - Maximum acceptable model state loss: 1 hour
  - Model Registry syncs every hour
- **RTO**: **2 hours**
  - Time to restore model inference capability
  - Automated: Model Registry → SageMaker Endpoint deployment
- **Backup**: Daily snapshots to S3, versioned in Model Registry
- **Restore**: Deploy from registry, verify with automated tests
- **Retention**: 7 days of model versions in S3, 30 days in Model Registry

**Tier 3: Analytics** - 🟢 **P2 Priority**
- **RPO**: **24 hours**
  - Maximum acceptable analytics data loss: 24 hours
- **RTO**: **8 hours**
  - Time to restore analytics dashboards
- **Backup**: Daily exports to S3
- **Restore**: Re-import from S3 backups
- **Retention**: 90 days in S3, 365 days in data warehouse

### Failover Procedures ⭐ **NEW**

```python
class DisasterRecoveryManager:
    def __init__(self):
        self.primary_region = "us-east-1"
        self.standby_regions = ["us-west-2", "eu-central-1"]
        self.failover_authority = "automated"  # or "manual"
    
    async def detect_failure(self):
        """Detect primary region failure"""
        health_checks = await self.check_region_health(self.primary_region)
        
        failure_criteria = {
            "latency": health_checks.latency > 2000,  # 2s latency
            "error_rate": health_checks.error_rate > 0.01,  # 1% errors
            "health_status": health_checks.status != "healthy"
        }
        
        if any(failure_criteria.values()):
            await self.initiate_failover(reason="health_check_failure")
    
    async def initiate_failover(self, reason: str):
        """Initiate failover to standby region"""
        # 1. Verify standby is healthy
        standby = self.select_best_standby()
        if not await self.verify_standby_health(standby):
            send_alert("Standby region unhealthy, cannot failover", severity="critical")
            return
        
        # 2. Promote standby to primary
        await self.promote_standby(standby)
        
        # 3. Update DNS/routing
        await self.update_routing(standby)
        
        # 4. Verify traffic routes to new primary
        await self.verify_failover_success(standby)
        
        # 5. Log failover event
        await self.log_failover_event({
            "from": self.primary_region,
            "to": standby,
            "reason": reason,
            "timestamp": datetime.now()
        })
```

### Backup Retention Policy

| Data Type | Backup Frequency | Retention Period | Restoration Method |
|-----------|-----------------|------------------|-------------------|
| **PostgreSQL** | Continuous WAL + Hourly Full | 7 days hourly, 30 days daily | Point-in-time recovery |
| **Redis** | Every 5 minutes (AOF) | 7 days | AOF replay |
| **Vector DB** | Daily snapshots | 30 days | Snapshot restore |
| **AI Models** | On version release | 90 days | Model Registry restore |
| **Event Logs** | Real-time streaming | 90 days hot, 1 year cold | Kinesis replay |
| **Analytics** | Daily exports | 365 days | S3 restore |

---

## FAILOVER RUNBOOK

### Automated Failover (RTO: 15 minutes)

**Trigger Conditions**:
1. Primary region health check fails 3 consecutive times (90 seconds)
2. Latency > 2s for 5 minutes
3. Error rate > 1% for 5 minutes

**Procedure**:
```bash
# 1. Verify standby health
aws health describe-health-checks --region us-west-2

# 2. Promote standby PostgreSQL
pg_ctl promote -D /var/lib/postgresql/standby

# 3. Update Route53 DNS
aws route53 change-resource-record-sets \
  --hosted-zone-id Z123456789 \
  --change-batch file://failover-dns.json

# 4. Update load balancer targets
aws elbv2 modify-target-group \
  --target-group-arn arn:aws:... \
  --health-check-enabled true

# 5. Verify services healthy
curl https://api.bodybroker.com/health
```

### Manual Failover (RTO: 1 hour)

**When to Use**:
- Data corruption requiring point-in-time recovery
- Planned maintenance
- Regional disaster

**Procedure**:
1. Notify on-call engineer
2. Freeze writes (read-only mode)
3. Create point-in-time backup
4. Verify backup integrity
5. Restore to standby region
6. Perform integrity checks
7. Resume writes
8. Monitor for 1 hour

---

**Status**: Complete RTO/RPO documentation and failover procedures


---

### Backup Implementation

**PostgreSQL Backup**:
```python
import subprocess
import boto3
from datetime import datetime

def backup_postgresql():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"/backups/postgresql_{timestamp}.dump"
    
    # pg_dump
    subprocess.run([
        'pg_dump',
        '-h', 'postgres-primary',
        '-U', 'postgres',
        '-F', 'c',  # Custom format
        '-f', backup_file,
        'body_broker_db'
    ])
    
    # Upload to S3
    s3 = boto3.client('s3')
    s3.upload_file(
        backup_file,
        'body-broker-backups',
        f'postgresql/{timestamp}.dump'
    )
    
    return backup_file
```

**Redis Persistence**:
```redis
# redis.conf
save 900 1      # Save after 900 sec if at least 1 key changed
save 300 10     # Save after 300 sec if at least 10 keys changed
save 60 10000   # Save after 60 sec if at least 10000 keys changed

appendonly yes
appendfsync everysec
```

**Vector DB Backup**:
- Pinecone: Automated snapshots via API
- Weaviate: Export to S3 using backup API

---

### Failover Procedures

**Database Failover**:
1. Detect primary failure (health check)
2. Promote read replica to primary
3. Update connection strings
4. Verify data consistency
5. Restore read replica from new primary

**Service Failover**:
1. Health check detects failure
2. Load balancer removes failed instance
3. Auto-scaling launches replacement
4. New instance joins cluster
5. Traffic routes to new instance

---

## COST MONITORING & ALERTS

### Real-Time Cost Tracking

```python
from prometheus_client import Gauge
import boto3

cost_gauge = Gauge('cost_per_request_usd', 'Cost per request', ['service', 'request_type'])

def track_llm_cost(layer: str, model: str, tokens: int):
    # Cost calculation based on provider pricing
    cost_per_1k = {
        'claude-4.5': 0.003,  # $0.003 per 1K tokens
        'gpt-5': 0.005,
        # Add more models
    }
    
    cost = (tokens / 1000) * cost_per_1k.get(model, 0.001)
    cost_gauge.labels(
        service='orchestration',
        request_type=f'{layer}_{model}'
    ).set(cost)

def check_budget_limit():
    # Query Prometheus for daily cost
    daily_cost = query_prometheus('sum(cost_per_request_usd)')
    
    if daily_cost > DAILY_BUDGET:
        send_alert(
            channel='#alerts',
            message=f'Daily budget exceeded: ${daily_cost:.2f} / ${DAILY_BUDGET}'
        )
```

---

## OPERATIONAL RUNBOOKS

### Service Health Checks

**Health Check Endpoint**:
```python
@app.get("/health")
async def health_check():
    checks = {
        'redis': check_redis_connection(),
        'postgres': check_postgres_connection(),
        'vector_db': check_vector_db_connection(),
        'ai_inference': check_inference_service(),
    }
    
    healthy = all(checks.values())
    return {
        'status': 'healthy' if healthy else 'unhealthy',
        'checks': checks
    }
```

**Kubernetes Liveness/Readiness**:
```yaml
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
```

---

**Status**: Complete operational stack integrated into all services

