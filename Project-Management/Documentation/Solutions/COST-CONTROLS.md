# Cost Controls & Rate Limiting
**Date**: January 29, 2025  
**Service**: Cross-Cutting Cost Management  
**Status**: Integrated into All Services

---

## OVERVIEW

Comprehensive cost control system to prevent budget overrun ($500k-2M/month risk) with per-tier rate limiting, budget caps, and real-time monitoring.

---

## RATE LIMITING PER TIER

### Tier Definitions

**Free Tier**:
- 5 Layer 3 calls/day
- 0 Layer 4 calls/day
- Basic NPC interactions only
- Cached responses preferred

**Premium Tier ($9.99/month)**:
- 50 Layer 3 calls/day
- 5 Layer 4 calls/day
- Enhanced NPC interactions
- Priority queue access

**Whale Tier (Custom Pricing)**:
- Unlimited with cost alerts
- Hard cap: $100/user/month
- Custom rate limits
- Highest priority queue

---

## IMPLEMENTATION

### Rate Limiter Service

```python
from datetime import datetime, timedelta
from typing import Optional
import redis
from redis.cluster import RedisCluster

class RateLimiter:
    def __init__(self, redis_cluster: RedisCluster):
        self.redis = redis_cluster
        self.tier_limits = {
            "free": {
                "layer3_daily": 5,
                "layer3_hourly": 1,
                "layer4_daily": 0
            },
            "premium": {
                "layer3_daily": 50,
                "layer3_hourly": 10,
                "layer4_daily": 5
            },
            "whale": {
                "layer3_daily": -1,  # Unlimited
                "layer3_hourly": -1,
                "layer4_daily": -1
            }
        }
    
    async def check_limit(
        self,
        user_id: str,
        tier: str,
        layer: int
    ) -> tuple[bool, Optional[str]]:
        """
        Check if user can make request
        Returns: (allowed, error_message)
        """
        limits = self.tier_limits.get(tier)
        if not limits:
            return False, f"Unknown tier: {tier}"
        
        if tier == "whale":
            # Check cost budget instead
            return await self.check_cost_budget(user_id)
        
        # Layer 3 limits
        if layer == 3:
            daily_key = f"rate_limit:{user_id}:layer3:daily"
            hourly_key = f"rate_limit:{user_id}:layer3:hourly"
            
            daily_count = int(await self.redis.get(daily_key) or 0)
            hourly_count = int(await self.redis.get(hourly_key) or 0)
            
            if limits["layer3_daily"] != -1 and daily_count >= limits["layer3_daily"]:
                return False, f"Daily Layer 3 limit exceeded ({limits['layer3_daily']})"
            
            if limits["layer3_hourly"] != -1 and hourly_count >= limits["layer3_hourly"]:
                return False, f"Hourly Layer 3 limit exceeded ({limits['layer3_hourly']})"
        
        # Layer 4 limits
        elif layer == 4:
            daily_key = f"rate_limit:{user_id}:layer4:daily"
            daily_count = int(await self.redis.get(daily_key) or 0)
            
            if limits["layer4_daily"] != -1 and daily_count >= limits["layer4_daily"]:
                return False, f"Daily Layer 4 limit exceeded ({limits['layer4_daily']})"
        
        return True, None
    
    async def increment_counter(self, user_id: str, layer: int):
        """Increment rate limit counters"""
        if layer == 3:
            daily_key = f"rate_limit:{user_id}:layer3:daily"
            hourly_key = f"rate_limit:{user_id}:layer3:hourly"
            
            await self.redis.incr(daily_key)
            await self.redis.expire(daily_key, 86400)  # 24 hours
            
            await self.redis.incr(hourly_key)
            await self.redis.expire(hourly_key, 3600)   # 1 hour
        
        elif layer == 4:
            daily_key = f"rate_limit:{user_id}:layer4:daily"
            await self.redis.incr(daily_key)
            await self.redis.expire(daily_key, 86400)
    
    async def check_cost_budget(self, user_id: str) -> tuple[bool, Optional[str]]:
        """Check if whale user has exceeded cost budget"""
        daily_cost_key = f"cost:{user_id}:daily"
        monthly_cost_key = f"cost:{user_id}:monthly"
        
        daily_cost = float(await self.redis.get(daily_cost_key) or 0)
        monthly_cost = float(await self.redis.get(monthly_cost_key) or 0)
        
        # Daily limit: $3.33 (derived from $100/month)
        if daily_cost > 3.33:
            return False, f"Daily cost budget exceeded: ${daily_cost:.2f}"
        
        # Monthly limit: $100
        if monthly_cost > 100.0:
            return False, f"Monthly cost budget exceeded: ${monthly_cost:.2f}"
        
        return True, None
```

### FastAPI Integration

```python
from fastapi import FastAPI, Depends, HTTPException, Header
from services.auth import get_current_user
from services.settings import get_user_tier

app = FastAPI()
rate_limiter = RateLimiter(redis_cluster)

@app.post("/api/v1/orchestration/generate")
async def generate_content(
    request: ContentRequest,
    authorization: str = Header(...),
    user: dict = Depends(get_current_user)
):
    user_id = user["user_id"]
    tier = await get_user_tier(user_id)
    
    # Check rate limits before processing
    allowed, error = await rate_limiter.check_limit(
        user_id=user_id,
        tier=tier,
        layer=request.layer
    )
    
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=error or "Rate limit exceeded"
        )
    
    # Process request
    result = await orchestration_service.generate_content(request, user_id)
    
    # Increment counter
    await rate_limiter.increment_counter(user_id, request.layer)
    
    return result
```

---

## COST MONITORING

### Real-Time Cost Tracking

```python
from prometheus_client import Gauge, Counter, Histogram
import asyncio

# Metrics
cost_per_request = Gauge(
    'cost_per_request_usd',
    'Cost per request in USD',
    ['service', 'layer', 'model']
)

daily_cost = Gauge(
    'daily_cost_usd',
    'Daily cost in USD',
    ['user_id', 'tier']
)

request_count = Counter(
    'llm_requests_total',
    'Total LLM requests',
    ['layer', 'tier', 'status']
)

class CostTracker:
    MODEL_COSTS = {
        "claude-4.5": 0.003,      # $0.003 per 1K tokens
        "gpt-5": 0.005,
        "gpt-4": 0.003,
        "gemini-2.5-pro": 0.002,
        "deepseek-v3.1": 0.0002   # Much cheaper
    }
    
    def __init__(self, redis_cluster: RedisCluster):
        self.redis = redis_cluster
    
    async def track_cost(
        self,
        user_id: str,
        layer: int,
        model: str,
        tokens: int,
        tier: str
    ):
        """Track cost for a single request"""
        cost_per_1k = self.MODEL_COSTS.get(model, 0.001)
        cost = (tokens / 1000) * cost_per_1k
        
        # Record Prometheus metrics
        cost_per_request.labels(
            service="orchestration",
            layer=layer,
            model=model
        ).set(cost)
        
        # Track per user in Redis
        daily_key = f"cost:{user_id}:daily"
        monthly_key = f"cost:{user_id}:monthly"
        
        await self.redis.incrbyfloat(daily_key, cost)
        await self.redis.expire(daily_key, 86400)
        
        await self.redis.incrbyfloat(monthly_key, cost)
        await self.redis.expire(monthly_key, 2592000)  # 30 days
        
        # Update Prometheus daily cost
        daily_total = float(await self.redis.get(daily_key) or 0)
        daily_cost.labels(user_id=user_id, tier=tier).set(daily_total)
        
        return cost
```

### Cost Dashboard Queries

```python
# Query Prometheus for cost analytics
from prometheus_api_client import PrometheusConnect

prom = PrometheusConnect(url="http://prometheus:9090")

def get_daily_cost(service: str = None):
    """Get daily cost for service or total"""
    query = 'sum(cost_per_request_usd)'
    if service:
        query += f'{{service="{service}"}}'
    
    result = prom.custom_query(query=query)
    return result

def get_user_cost(user_id: str):
    """Get cost for specific user"""
    query = f'daily_cost_usd{{user_id="{user_id}"}}'
    result = prom.custom_query(query=query)
    return result

def get_top_spenders(limit: int = 10):
    """Get top N users by cost"""
    query = 'topk(10, daily_cost_usd)'
    result = prom.custom_query(query=query)
    return result
```

---

## BUDGET ALERTS

### Automated Alerting

```python
from slack_sdk import WebClient
from pagerduty import EventsAPIClient
import asyncio

class CostAlertManager:
    def __init__(self):
        self.slack = WebClient(token=os.getenv("SLACK_TOKEN"))
        self.pagerduty = EventsAPIClient(integration_key=os.getenv("PAGERDUTY_KEY"))
        self.alert_thresholds = {
            "daily_budget_dev": 100.0,      # $100/day for dev
            "daily_budget_prod": 10000.0,    # $10k/day for prod
            "user_daily_limit": 3.33,        # $100/month = $3.33/day
            "projection_threshold": 0.8      # Alert at 80% of budget
        }
    
    async def check_budgets(self):
        """Periodic budget check (every hour)"""
        while True:
            await asyncio.sleep(3600)  # 1 hour
            
            # Check environment budgets
            daily_cost_total = await get_daily_cost()
            
            env = os.getenv("ENVIRONMENT", "dev")
            budget = self.alert_thresholds[f"daily_budget_{env}"]
            
            if daily_cost_total >= budget * self.alert_thresholds["projection_threshold"]:
                await self.send_budget_alert(env, daily_cost_total, budget)
            
            # Check individual user budgets (whale tier)
            top_spenders = await get_top_spenders(50)
            for user in top_spenders:
                if user["cost"] > self.alert_thresholds["user_daily_limit"]:
                    await self.send_user_alert(user["user_id"], user["cost"])
    
    async def send_budget_alert(self, env: str, current: float, budget: float):
        """Send budget alert to Slack/PagerDuty"""
        percentage = (current / budget) * 100
        message = f"⚠️ Budget Alert - {env.upper()}\n"
        message += f"Current: ${current:.2f} ({percentage:.1f}% of ${budget:.2f} budget)\n"
        message += f"Projection: ${current * 24:.2f} for full day"
        
        # Slack alert
        self.slack.chat_postMessage(
            channel="#alerts",
            text=message
        )
        
        # PagerDuty for critical (>=90%)
        if percentage >= 90:
            self.pagerduty.send_event({
                "routing_key": self.pagerduty.integration_key,
                "event_action": "trigger",
                "payload": {
                    "summary": f"Budget critical: {env} at {percentage:.1f}%",
                    "severity": "critical",
                    "source": "cost-monitor"
                }
            })
```

---

## COST PROJECTION MODEL

```python
def project_monthly_cost(daily_cost: float, days_in_month: int = 30) -> float:
    """Project monthly cost from daily average"""
    return daily_cost * days_in_month

def project_annual_cost(monthly_cost: float) -> float:
    """Project annual cost"""
    return monthly_cost * 12

async def get_cost_projection(user_id: str = None) -> dict:
    """Get cost projections"""
    if user_id:
        daily = float(await redis_cluster.get(f"cost:{user_id}:daily") or 0)
    else:
        daily = await get_daily_cost_total()
    
    monthly = project_monthly_cost(daily)
    annual = project_annual_cost(monthly)
    
    return {
        "daily": daily,
        "monthly_projection": monthly,
        "annual_projection": annual,
        "timestamp": datetime.now().isoformat()
    }
```

---

## FALLBACK STRATEGIES

### When Rate Limit Hit

```python
async def handle_rate_limit_exceeded(
    user_id: str,
    tier: str,
    request: ContentRequest
) -> ContentResponse:
    """Graceful degradation when rate limit exceeded"""
    
    if tier == "free":
        # Return cached responses only
        cached = await get_cached_response(request)
        if cached:
            return cached
        
        # Use Layer 1-2 only (no expensive calls)
        foundation = await layer1.generate_base(request)
        customized = await layer2.customize(foundation)
        
        return ContentResponse(
            foundation=foundation,
            customized=customized,
            interactions=None,
            orchestration=None
        )
    
    # Premium/Whale: Queue request for later processing
    await queue_request(user_id, request, priority=tier)
    return ContentResponse(
        message="Request queued - will process when limit resets",
        status="queued"
    )
```

---

## INTEGRATION POINTS

1. **Orchestration Service**: Checks tier before Layer 3/4 calls
2. **Payment Service**: Validates subscription status
3. **Settings Service**: Provides user tier information
4. **AI Inference Service**: Tracks cost per request
5. **Monitoring**: Real-time cost dashboards

---

**Status**: Complete cost control system integrated across all services

