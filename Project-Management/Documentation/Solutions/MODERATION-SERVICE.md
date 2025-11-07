# Moderation Service Solution
**Service**: Content Safety & Guardrails  
**Date**: January 29, 2025  
**Status**: ⭐ **UPDATED** - Real-time integration path added

---

## SERVICE OVERVIEW

Implements multi-layer content moderation, rating enforcement, and safety guardrails.

---

## ARCHITECTURE

### Technology Stack
- **Input Filtering**: LLM-based content detection
- **Output Filtering**: Constitutional AI models
- **Human Review**: Queue system
- **Reporting**: Player reporting UI

### Integration with AI Inference ⭐ **NEW**

**Real-Time Content Filtering Path**:
```
AI Inference generates response → Moderation check (50-100ms) → Game Client
```

**Implementation** (FastAPI Middleware Pattern):
```python
from fastapi import FastAPI, Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
import asyncio

class ModerationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # For AI inference responses, check content
        if request.url.path.startswith("/v1/dialogue"):
            # Get response from AI Inference
            response = await call_next(request)
            
            # Read response body
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk
            
            # Moderate content (async, non-blocking)
            moderation_task = asyncio.create_task(
                self.moderate_content(response_body.decode())
            )
            
            # Return response immediately (provisional)
            # Moderation continues in background
            if moderation_task.done() and await moderation_task:
                # Content flagged - return safe fallback
                return Response(
                    content=get_safe_fallback(),
                    status_code=200,
                    media_type="application/json"
                )
            
            return Response(
                content=response_body,
                status_code=response.status_code,
                headers=dict(response.headers)
            )
        
        # For other requests, pass through
        return await call_next(request)
    
    async def moderate_content(self, content: str) -> bool:
        # Fast keyword filter (10ms)
        if self.fast_keyword_check(content):
            return True
        
        # Async ML toxicity detection (200ms)
        toxicity_score = await self.ml_toxicity_check(content)
        return toxicity_score > THRESHOLD

# Apply middleware
app.add_middleware(ModerationMiddleware)
```

**Latency Budget**:
- Fast keyword filter: 10ms (synchronous)
- ML toxicity check: 200ms (async, non-blocking)
- Total overhead: 50-100ms (optimized)

**Fallback Strategy**:
- Timeout: 100ms max moderation time
- If timeout: Allow provisional content, check in background
- If flagged post-delivery: Replace with cached safe response

### Multi-Layer Approach

```python
class ModerationService:
    def __init__(self):
        self.input_filter = ContentFilter(tier='input')
        self.output_filter = ContentFilter(tier='output')
        self.human_review_queue = ReviewQueue()
        self.fast_keyword_filter = KeywordFilter()  # ⭐ NEW: Fast path
        self.ml_toxicity_model = ToxicityModel()    # ⭐ NEW: ML path
    
    async def moderate_input(self, user_input, rating='M'):
        # Layer 1: Input filtering
        input_check = await self.input_filter.check(
            text=user_input,
            rating=rating
        )
        
        if input_check.flagged:
            return ModerationResult(
                allowed=False,
                reason=input_check.reason,
                needs_review=True
            )
        
        return ModerationResult(allowed=True)
    
    async def moderate_output(self, ai_response, rating='M'):
        # Layer 2: Output filtering
        output_check = await self.output_filter.check(
            text=ai_response,
            rating=rating
        )
        
        if output_check.flagged:
            # Send to human review
            await self.human_review_queue.add(
                content=ai_response,
                reason=output_check.reason
            )
            
            # Use fallback response
            return ModerationResult(
                allowed=False,
                fallback_response=get_safe_fallback(),
                needs_review=True
            )
        
        return ModerationResult(allowed=True)
```

### Rating Enforcement

```python
RATING_RULES = {
    'M': {
        'allowed_themes': ['violence', 'horror', 'mature'],
        'forbidden_themes': ['suicide_promotion', 'real_killing_encouragement']
    }
}

def enforce_rating(content, target_rating):
    violations = []
    
    for forbidden in RATING_RULES[target_rating]['forbidden_themes']:
        if detect_theme(content, forbidden):
            violations.append(forbidden)
    
    return len(violations) == 0, violations
```

### Player Reporting

```python
@app.post("/api/report-content")
async def report_content(report: ContentReport):
    # Log report
    await db.log_report(
        user_id=report.user_id,
        content_id=report.content_id,
        reason=report.reason
    )
    
    # Check if threshold exceeded
    report_count = await db.get_report_count(report.content_id)
    
    if report_count > 5:  # Threshold
        # Auto-flag for review
        await moderation_service.flag_for_review(report.content_id)
    
    return {"status": "reported"}
```

---

## SUMMARY

All 8 service solutions created. Ready for Phase 3: Task Breakdown.

**Solutions Created**:
1. Game Engine Service
2. AI Inference Service
3. Orchestration Service
4. Payment Service
5. State Management Service
6. Learning/Feedback Service
7. Moderation Service
8. Settings/Config Service (covered in Game Engine)

See `SOLUTION-OVERVIEW.md` for integration summary.

