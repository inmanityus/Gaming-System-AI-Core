# Microservices Refactoring Plan
**Project**: Gaming System AI Core (Body Broker)  
**Start Date**: 2025-11-12  
**Estimated Duration**: 2-4 weeks  
**Status**: Phase 1 - Architecture Design

## Architecture Decision (Peer Reviewed by GPT-4o)

### Selected Approach
- **Communication**: HTTP/REST for simplicity and debugging
- **Service Discovery**: DNS-based (service names resolve in ECS/Docker)
- **Shared Code**: HTTP client library only
- **Database**: Database-per-service (state-manager has centralized DB for game state)
- **Events**: Event-bus service for pub/sub patterns
- **Consistency**: Eventual consistency with saga pattern where needed

### Deferred for V2
- gRPC (complexity vs benefit for 22 services)
- Service mesh (Istio/Linkerd - overkill for current scale)
- API Gateway (can add later if needed)

## Service Dependency Analysis

### Tier 1 - No Dependencies (Deploy First)
1. **payment** - Stripe integration, self-contained
2. **time-manager** - Time/day-night cycle, publishes events
3. **weather-manager** - Weather state, publishes events
4. **storyteller** - Simple narrative service
5. **ue-version-monitor** - Monitors UE versions
6. **capability-registry** - UE5 capability database

### Tier 2 - Core Infrastructure (Deploy Second)
7. **event-bus** - Central event routing
8. **state-manager** - Game state persistence (has shared DB)
9. **model-management** - AI model registry

### Tier 3 - AI Services (Deploy Third)
10. **ai-integration** - LLM client, depends on model-management
11. **ai-router** - Intelligent routing

### Tier 4 - Game Systems (Deploy Fourth)
12. **quest-system** - Depends on ai-integration, state-manager
13. **world-state** - Depends on state-manager, event-bus
14. **npc-behavior** - Depends on ai-integration, state-manager
15. **knowledge-base** - Semantic search
16. **language-system** - Depends on ai-integration, model-management

### Tier 5 - Orchestration (Deploy Fifth)
17. **orchestration** - Depends on ai-integration, multiple services
18. **story-teller** - Depends on state-manager, ai-integration
19. **environmental-narrative** - Depends on state-manager

### Tier 6 - Configuration (Deploy Last)
20. **settings** - Configuration service
21. **performance-mode** - Performance settings
22. **router** - Service routing

## Shared HTTP Client Library Structure

```
services/shared/
├── __init__.py
├── http_clients/
│   ├── __init__.py
│   ├── base_client.py          # Base HTTP client with retry/circuit breaker
│   ├── model_management_client.py
│   ├── state_manager_client.py
│   ├── ai_integration_client.py
│   ├── event_bus_client.py
│   └── ...
└── models/
    ├── __init__.py
    └── common_models.py         # Shared Pydantic models
```

## Refactoring Process Per Service

### Step 1: Analyze Dependencies
- Identify all imports from other services
- Document required endpoints/methods
- Create HTTP client interface

### Step 2: Implement HTTP Client (PEER CODED)
- Create client class with all needed methods
- Implement circuit breaker pattern
- Add retry logic with exponential backoff
- Peer review with GPT-4o or Gemini 2.5 Pro

### Step 3: Refactor Service Code (PEER CODED)
- Replace direct imports with HTTP client calls
- Update all call sites
- Handle async/await properly
- Peer review changes

### Step 4: Update Dockerfile
- Remove cross-service code copies
- Include only service code + shared clients
- Test build locally

### Step 5: Test Service (PAIRWISE TESTED)
- Unit tests for service logic
- Integration tests with mocked HTTP responses
- Contract tests for API compliance
- Peer validate test coverage

### Step 6: Deploy and Verify
- Deploy to ECS
- Verify service starts successfully
- Test actual HTTP calls to dependencies
- Monitor logs for errors

### Step 7: Update Documentation
- Document new HTTP endpoints used
- Update service architecture diagram
- Note any breaking changes

## Testing Strategy

### Per-Service Testing
- Unit tests: Service logic without external calls
- Integration tests: With HTTP mocks
- Contract tests: API adherence

### Cross-Service Testing
- End-to-end tests after each tier deployment
- Performance tests for latency
- Chaos testing (kill random services)

### Rollback Strategy
- Keep old monolithic image tagged
- Blue-green deployment per tier
- Can rollback entire tier if issues

## Current Status

- Phase 1: Architecture design ✓ (peer reviewed by GPT-4o)
- Phase 2: Create base HTTP client - NOT STARTED
- Phase 3: Refactor Tier 1 services - NOT STARTED
- Phase 4: Refactor Tier 2 services - NOT STARTED
- Phase 5: Refactor Tier 3 services - NOT STARTED
- Phase 6: Refactor Tier 4 services - NOT STARTED
- Phase 7: Refactor Tier 5 services - NOT STARTED
- Phase 8: Refactor Tier 6 services - NOT STARTED
- Phase 9: Comprehensive testing - NOT STARTED
- Phase 10: Documentation - NOT STARTED

## Estimated Timeline

- Week 1: Tiers 1-2 (9 services)
- Week 2: Tiers 3-4 (10 services)
- Week 3: Tiers 5-6 (3 services)
- Week 4: Testing and documentation

Total: ~4 weeks for proper implementation

