# ADR 001: Report Generation Pipeline Architecture

**Status**: Accepted  
**Date**: 2025-11-12  
**Decision Makers**: Claude Sonnet 4.5, Gemini 2.5 Pro, GPT-5  
**Context**: DOC-1 - Architecture Decision Record for 100/100 quality

---

## Context

The validation report system needs to generate reports in multiple formats (JSON, HTML, PDF) from AI testing data. The generation process is computationally intensive (especially PDF) and must not block API requests.

## Decision

Implement a **4-step pipeline architecture** with async/await and ProcessPoolExecutor for CPU-bound operations:

```
DataCollection → DataTransformation → ReportGeneration → Storage
```

### Pipeline Steps

1. **DataCollectionStep**: Gather test run data from orchestrator storage
2. **DataTransformationStep**: Transform raw data into report structure
3. **ReportGenerationStep**: Generate report in requested format
4. **StorageStep**: Upload report to S3 and update metadata

### Concurrency Model

- **Async/await** for I/O-bound operations (database, S3)
- **ProcessPoolExecutor** for CPU-bound operations (PDF generation)
- **BackgroundTasks** for async job execution

## Rationale

### Why Pipeline Architecture?

✅ **Separation of Concerns**: Each step has single responsibility  
✅ **Testability**: Steps can be tested independently  
✅ **Extensibility**: Easy to add new steps or modify existing ones  
✅ **Error Handling**: Failures isolated to specific steps  
✅ **Observability**: Can track progress through pipeline

### Why ProcessPoolExecutor for PDF?

✅ **Non-Blocking**: Keeps event loop responsive  
✅ **CPU Isolation**: PDF rendering doesn't starve other requests  
✅ **Simple**: No external dependencies (Celery, RabbitMQ)  
✅ **Sufficient**: Works for current scale

### Why Not Celery?

❌ **Complexity**: Requires Redis/RabbitMQ broker  
❌ **Overhead**: Additional infrastructure to manage  
❌ **Scale**: Current load doesn't justify distributed task queue  

**Future**: Migrate to Celery when concurrent report generation exceeds 10/minute

## Consequences

### Positive

- ✅ API stays responsive during PDF generation
- ✅ Clear error boundaries and recovery
- ✅ Easy to test and maintain
- ✅ Observable with metrics per step
- ✅ Graceful degradation if storage fails

### Negative

- ⚠️ Limited to single machine (ProcessPoolExecutor doesn't distribute)
- ⚠️ Memory overhead from separate processes
- ⚠️ No job persistence if application crashes mid-generation

### Mitigation Strategies

- **Scale Limitation**: Horizontal scaling requires moving to Celery/ARQ
- **Memory Overhead**: Configure max_workers based on available RAM
- **Job Persistence**: Database tracks report status for recovery

## Alternatives Considered

### 1. Synchronous Generation (Rejected)

**Pros**: Simplest implementation  
**Cons**: Blocks API for seconds/minutes during PDF generation

**Why Rejected**: Unacceptable UX, API becomes unusable during generation

### 2. Celery Distributed Task Queue (Deferred)

**Pros**: Scalable, persistent, distributed  
**Cons**: Complex, requires Redis/RabbitMQ, overhead

**Why Deferred**: Over-engineering for current scale, can migrate later

### 3. AWS Lambda for PDF Generation (Considered)

**Pros**: Serverless, infinite scale  
**Cons**: Cold starts, GTK libraries package size, network latency

**Why Not Chosen**: Local execution faster for development, can add later

## Implementation Notes

- PDF generation timeout: 120 seconds
- ProcessPool workers: 2 (configurable)
- Pipeline steps execute sequentially with error recovery
- Each step logs progress for observability

## Review & Validation

- ✅ Peer reviewed by GPT-5 (architecture validation)
- ✅ Peer reviewed by Gemini 2.5 Pro (scalability analysis)
- ✅ Peer reviewed by Claude Sonnet 4.5 (implementation review)

## Future Considerations

**When to Migrate to Celery**:
- Report generation exceeds 10/minute sustained
- Need distributed workers across multiple machines
- Require job persistence across application restarts
- Need advanced scheduling (cron-like report generation)

**Migration Path**:
1. Add Celery + Redis to docker-compose.yml
2. Create task modules (tasks/generate_report.py)
3. Replace BackgroundTasks with celery.send_task()
4. Deploy Celery workers separately
5. Maintain backward compatibility during transition

---

**Status**: ✅ Implemented and operational  
**Review Date**: 2025-11-12  
**Next Review**: When load exceeds 10 reports/minute

