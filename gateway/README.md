# HTTP→NATS Gateway

## Purpose

Provides HTTP/JSON → NATS/Protobuf translation for gradual zero-downtime migration from HTTP-based microservices to NATS binary messaging.

## Architecture

```
┌──────────────┐     HTTP/JSON      ┌─────────────────┐     NATS/Protobuf     ┌──────────────┐
│  HTTP Client │ ──────────────────> │  Gateway        │ ────────────────────> │ NATS Service │
│  (Existing)  │ <────────────────── │  (FastAPI)      │ <──────────────────── │  (New)       │
└──────────────┘     HTTP/JSON      └─────────────────┘     NATS/Protobuf     └──────────────┘
```

### Features

- **Request Translation**: JSON → Protobuf
- **Response Translation**: Protobuf → JSON
- **Error Mapping**: Protobuf Error codes → HTTP status codes
- **Streaming Support**: Server-Sent Events for LLM token streaming
- **Metadata Propagation**: HTTP headers → Meta fields
- **Idempotency**: Idempotency key forwarding
- **Health Checks**: NATS connection monitoring

## Supported Routes

### AI Integration
- `POST /ai/llm/infer` → `svc.ai.llm.v1.infer`
  - Non-streaming and streaming (SSE) responses

### Model Management
- `POST /ai/models` → `svc.ai.model.v1.list`
- `POST /ai/models/{model_id}` → `svc.ai.model.v1.get`
- `POST /ai/models/{model_id}/select` → `svc.ai.model.v1.select`

### State Manager
- `POST /state/update` → `svc.state.manager.v1.update`
- `POST /state/get` → `svc.state.manager.v1.get`

### Quest System
- `POST /quest/generate` → `svc.quest.v1.generate`

### NPC Behavior
- `POST /npc/behavior` → `svc.npc.behavior.v1.plan`

## Usage

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set NATS connection
export NATS_URL=nats://localhost:4222

# Run gateway
python http_nats_gateway.py
```

### Docker

```bash
# Build image
docker build -t gaming-system/http-nats-gateway:latest .

# Run container
docker run -p 8000:8000 \
  -e NATS_URL=nats://nats-cluster:4222 \
  gaming-system/http-nats-gateway:latest
```

### AWS ECS Deployment

```bash
# Build and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 695353648052.dkr.ecr.us-east-1.amazonaws.com
docker build -t gaming-system/http-nats-gateway:latest .
docker tag gaming-system/http-nats-gateway:latest 695353648052.dkr.ecr.us-east-1.amazonaws.com/bodybroker-services/http-nats-gateway:latest
docker push 695353648052.dkr.ecr.us-east-1.amazonaws.com/bodybroker-services/http-nats-gateway:latest

# Deploy to ECS (service definition in terraform)
aws ecs update-service --cluster gaming-system-cluster --service http-nats-gateway --force-new-deployment
```

## Request Format

### Non-Streaming

```bash
curl -X POST http://localhost:8000/ai/llm/infer \
  -H "Content-Type: application/json" \
  -H "X-Trace-ID: abc123" \
  -H "X-User-ID: user_456" \
  -d '{
    "model_id": "gpt-5-pro",
    "input": {
      "prompt": "Hello, world!"
    },
    "params": {
      "temperature": 0.7,
      "max_tokens": 100
    },
    "idempotency_key": "unique-key-123"
  }'
```

### Streaming

```bash
curl -X POST http://localhost:8000/ai/llm/infer \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "model_id": "gpt-5-pro",
    "input": {
      "prompt": "Tell me a story"
    },
    "params": {
      "stream": true,
      "max_tokens": 500
    }
  }'
```

Response (SSE):
```
data: {"meta":{...},"generation_id":"gen-123","index":0,"is_final":false,"delta":{"output_text_delta":"Once"}}

data: {"meta":{...},"generation_id":"gen-123","index":1,"is_final":false,"delta":{"output_text_delta":" upon"}}

data: {"meta":{...},"generation_id":"gen-123","index":10,"is_final":true,"finish_reason":"stop","usage":{...}}
```

## Error Handling

Protobuf errors are mapped to HTTP status codes:

| Protobuf Error | HTTP Status | Description |
|----------------|-------------|-------------|
| INVALID_ARGUMENT | 400 | Bad request format |
| UNAUTHENTICATED | 401 | Missing/invalid auth |
| PERMISSION_DENIED | 403 | No access |
| NOT_FOUND | 404 | Resource not found |
| CONFLICT | 409 | Version conflict |
| FAILED_PRECONDITION | 412 | CAS failure |
| RESOURCE_EXHAUSTED | 429 | Rate limited |
| INTERNAL | 500 | Server error |
| UNIMPLEMENTED | 501 | Not implemented |
| UNAVAILABLE | 503 | Service unavailable |
| DEADLINE_EXCEEDED | 504 | Timeout |

## Configuration

### Environment Variables

- `PORT`: HTTP port (default: 8000)
- `HOST`: Bind address (default: 0.0.0.0)
- `NATS_URL`: NATS connection URL (default: nats://localhost:4222)
- `NATS_TIMEOUT_SECONDS`: Request timeout (default: 30)

### Header Propagation

HTTP headers are mapped to Meta fields:

| HTTP Header | Meta Field |
|-------------|------------|
| X-Trace-ID | trace_id |
| X-Client-ID | client_id |
| X-User-ID | user_id |
| X-Tenant-ID | tenant_id |
| X-Custom-* | labels[*] |

## Monitoring

### Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "nats_connected": true,
  "routes": 9
}
```

### Metrics

- Request latency (HTTP → NATS → HTTP)
- NATS connection status
- Error rates by route
- Streaming connection count

## Migration Strategy

### Phase 1: Deploy Gateway

1. Deploy gateway as ECS service
2. Configure ALB to route to gateway
3. Gateway forwards to NATS services
4. Monitor latency and errors

### Phase 2: Traffic Shadowing

1. Send traffic to both HTTP and NATS
2. Compare responses
3. Fix discrepancies

### Phase 3: Gradual Cutover

1. Route 10% → Gateway
2. Monitor for 24 hours
3. Increase to 50%
4. Increase to 100%

### Phase 4: Retire HTTP

1. Remove HTTP endpoints from services
2. Remove gateway
3. Direct NATS-to-NATS communication

## Performance

### Expected Latency

- Gateway overhead: <1ms
- NATS request/reply: 0.3-1ms
- Total: HTTP (5-20ms) → Gateway+NATS (1-2ms)

### Throughput

- Gateway: 10K+ req/sec per instance
- Scale horizontally with ECS auto-scaling

## Troubleshooting

### Gateway Not Starting

- Check NATS_URL is correct
- Verify NATS cluster is running
- Check generated protobuf files exist

### Request Timeout

- Increase NATS_TIMEOUT_SECONDS
- Check backend service health
- Verify NATS subject routing

### Invalid Response

- Check protobuf schema versions match
- Verify route mapping is correct
- Review gateway logs

## References

- [ADR-002: NATS Binary Messaging](../docs/architecture/ADR-002-NATS-Binary-Messaging.md)
- [Binary Messaging Requirements](../docs/architecture/BINARY-MESSAGING-REQUIREMENTS.md)
- [NATS Documentation](https://docs.nats.io/)

