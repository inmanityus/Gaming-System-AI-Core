# Authentication System Requirements

**Priority**: HIGH (Issues #4, #14, #18)  
**Effort**: 8-12 hours  
**Status**: Design phase  
**Blocker**: Must implement before production

## Issues To Solve
- #4: Hardcoded player_001 everywhere
- #14: No auth middleware on any service
- #18: Checkout accepts any user_id

## Design
- JWT-based authentication
- FastAPI dependency for all protected endpoints
- User session management
- Role-based access (user, admin)

## Implementation Plan
1. Create auth service (2 hours)
2. JWT token generation/validation (2 hours)
3. FastAPI middleware (2 hours)
4. Integrate across 15+ services (4-6 hours)
5. Testing (2 hours)

## Template (from knowledge_base)
```python
async def verify_api_key(x_api_key: str = Header(None)):
    if not x_api_key or x_api_key not in API_KEYS:
        raise HTTPException(401, "Invalid API key")
    return True

@router.post("/endpoint", dependencies=[Depends(verify_api_key)])
```

Defer to next session - foundation audit takes priority.

