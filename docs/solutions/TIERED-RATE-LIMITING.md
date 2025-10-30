# Tiered Rate Limiting Strategy
**Date**: January 29, 2025  
**Critical**: High Priority - UX Impact

---

## PROBLEM STATEMENT

**Issue**: Standard rate limiting (10 req/min/user) conflicts with gameplay:
- Intense dialogue: 6 exchanges = 6 requests
- Quest updates: 1 request
- Background generation: 3 requests
- **Total**: 10 requests in 30 seconds = Rate limit hit mid-conversation

**Impact**: Breaks immersion, frustrates players

---

## SOLUTION: TIERED RATE LIMITING

### Rate Limits by Request Type

| Request Type | Free Tier | Premium Tier | Whale Tier | Exemption Rule |
|--------------|-----------|--------------|------------|----------------|
| **Conversational AI** (NPC dialogue) | 20/min | 50/min | Unlimited | Critical gameplay path |
| **Background Generation** (terrain, content) | 5/min | 20/min | 100/min | Can queue/retry |
| **Orchestration** (complex scenarios) | 0/day | 5/day | Unlimited | Premium feature |
| **Settings/Config** | 10/min | 30/min | Unlimited | Non-AI, low cost |
| **Analytics/Telemetry** | Unlimited | Unlimited | Unlimited | No AI cost |

### Implementation

```python
class TieredRateLimiter:
    def __init__(self):
        self.redis = redis_cluster
        self.request_type_limits = {
            "conversation": {
                "free": {"limit": 20, "window": 60},
                "premium": {"limit": 50, "window": 60},
                "whale": {"limit": -1, "window": 60}
            },
            "background_generation": {
                "free": {"limit": 5, "window": 60},
                "premium": {"limit": 20, "window": 60},
                "whale": {"limit": 100, "window": 60}
            },
            "orchestration": {
                "free": {"limit": 0, "window": 86400},
                "premium": {"limit": 5, "window": 86400},
                "whale": {"limit": -1, "window": 86400}
            }
        }
    
    async def check_rate_limit(
        self,
        user_id: str,
        tier: str,
        request_type: str
    ) -> tuple[bool, Optional[str], Optional[int]]:
        """
        Returns: (allowed, error_message, retry_after_seconds)
        """
        limits = self.request_type_limits.get(request_type)
        if not limits:
            return True, None, None  # No limit for unknown types
        
        tier_limits = limits.get(tier)
        if not tier_limits:
            return False, f"Unknown tier: {tier}", None
        
        if tier_limits["limit"] == -1:  # Unlimited
            return True, None, None
        
        window = tier_limits["window"]
        limit = tier_limits["limit"]
        
        key = f"rate_limit:{user_id}:{request_type}:{tier}"
        
        # Check current count
        count = int(await self.redis.get(key) or 0)
        
        if count >= limit:
            # Calculate retry after
            ttl = await self.redis.ttl(key)
            if ttl > 0:
                retry_after = ttl
            else:
                retry_after = window
            
            return False, f"Rate limit exceeded for {request_type} ({limit}/{window}s)", retry_after
        
        # Increment counter
        if count == 0:
            await self.redis.setex(key, window, 1)
        else:
            await self.redis.incr(key)
        
        return True, None, None
```

### Graceful Degradation

```python
async def handle_rate_limit_exceeded(
    self,
    user_id: str,
    request: ContentRequest
) -> ContentResponse:
    """Graceful degradation when rate limit hit"""
    
    request_type = self.classify_request(request)
    
    if request_type == "conversation":
        # Critical path - use cached response or queue
        cached = await self.get_cached_dialogue(request)
        if cached:
            return cached
        
        # Queue for later processing (non-blocking)
        await self.queue_request(user_id, request, priority="high")
        return ContentResponse(
            message="Response queued - processing in background",
            status="queued",
            estimated_wait_seconds=30
        )
    
    elif request_type == "background_generation":
        # Non-critical - queue or return lightweight fallback
        await self.queue_request(user_id, request, priority="low")
        return ContentResponse(
            message="Generation queued",
            status="queued"
        )
```

### Priority Queue System

```python
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

class RequestPriority(Enum):
    CRITICAL = 1  # Conversational AI, real-time interactions
    HIGH = 2      # Quest updates, important game state
    MEDIUM = 3    # Background generation, pre-loading
    LOW = 4       # Analytics, telemetry

@dataclass
class QueuedRequest:
    user_id: str
    request: ContentRequest
    priority: RequestPriority
    queued_at: datetime
    estimated_process_time: int  # seconds

class RequestQueue:
    async def add_request(
        self,
        user_id: str,
        request: ContentRequest,
        priority: RequestPriority
    ):
        queued = QueuedRequest(
            user_id=user_id,
            request=request,
            priority=priority,
            queued_at=datetime.now(),
            estimated_process_time=self.estimate_time(request)
        )
        
        await self.redis.lpush(
            f"queue:{priority.value}",
            json.dumps(queued.__dict__)
        )
    
    async def process_queue(self):
        """Process queue by priority"""
        for priority in RequestPriority:
            while True:
                queued_str = await self.redis.rpop(f"queue:{priority.value}")
                if not queued_str:
                    break
                
                queued = QueuedRequest(**json.loads(queued_str))
                await self.process_request(queued)
```

---

## EXEMPTION RULES

### Critical Path Exemptions

```python
CRITICAL_PATHS = [
    "/api/v1/dialogue/active",  # Active NPC conversations
    "/api/v1/battle/coordinate",  # Active battles
    "/api/v1/player/state",  # State updates
]

async def is_critical_path(self, request_path: str) -> bool:
    """Check if request is on critical path"""
    return any(request_path.startswith(path) for path in CRITICAL_PATHS)

async def check_rate_limit_with_exemptions(
    self,
    user_id: str,
    tier: str,
    request_type: str,
    request_path: str
):
    # Critical paths get higher limits
    if self.is_critical_path(request_path):
        if request_type == "conversation":
            # Double the limit for critical paths
            tier_limits = self.request_type_limits[request_type][tier]
            tier_limits["limit"] *= 2
    
    return await self.check_rate_limit(user_id, tier, request_type)
```

---

## USER-FACING MESSAGES

### Rate Limit Exceeded Messages

```python
RATE_LIMIT_MESSAGES = {
    "conversation": "You're chatting too quickly! Please wait {retry_after}s before continuing.",
    "background_generation": "Content generation is queued. You'll be notified when ready.",
    "orchestration": "This feature requires Premium. Upgrade to unlock unlimited orchestration.",
}

async def handle_rate_limit_response(
    self,
    request_type: str,
    retry_after: int
) -> ContentResponse:
    message = RATE_LIMIT_MESSAGES.get(request_type, "Rate limit exceeded")
    
    return ContentResponse(
        message=message.format(retry_after=retry_after),
        status="rate_limited",
        retry_after=retry_after,
        suggested_action=self.get_suggested_action(request_type)
    )
```

---

**Status**: Complete tiered rate limiting system with graceful degradation

