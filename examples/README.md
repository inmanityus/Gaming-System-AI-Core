# NATS SDK Examples

## Prerequisites

1. **NATS Server Running**:
   ```bash
   # Using Docker
   docker run -p 4222:4222 nats:latest
   
   # Or using NATS cluster (production)
   # See infrastructure/nats/terraform/
   ```

2. **Python Dependencies**:
   ```bash
   pip install -r ../sdk/requirements.txt
   pip install nats-py protobuf
   ```

3. **Generated Protobuf Files**:
   ```bash
   # From project root
   python -m grpc_tools.protoc -I=proto --python_out=generated proto/*.proto
   ```

## Examples

### 1. Simple Request/Reply Client

```bash
python ai_integration_client.py
```

Demonstrates:
- Creating protobuf request
- Setting Meta fields (request_id, trace_id, idempotency_key)
- Using presence wrappers (DoubleValue, UInt32Value)
- Sending request via NATS
- Receiving and parsing response

### 2. Service Implementation

```bash
python ai_integration_service.py
```

Demonstrates:
- Subscribing to NATS subject with queue group
- Load-balanced request processing
- Deserializing protobuf requests
- Processing requests
- Sending protobuf responses
- Error handling

### 3. Streaming Client

```bash
python streaming_client.py
```

Demonstrates:
- Enabling streaming with BoolValue(True)
- Streaming token chunks
- Handling LLMStreamChunk messages
- Detecting final chunk (is_final=true)
- Displaying tokens in real-time

## Running End-to-End

### Terminal 1: Start Service
```bash
python ai_integration_service.py
```

Output:
```
AI Integration Service started
Listening on svc.ai.llm.v1.infer with queue group q.ai.llm.infer
```

### Terminal 2: Run Client
```bash
python ai_integration_client.py
```

Output:
```
Connected to NATS
Sending request to svc.ai.llm.v1.infer
Generation ID: gen-abc123
Output: Response to: Tell me about NATS messaging
Tokens used: 30
Finish reason: stop
```

### Terminal 3: Run Streaming Client
```bash
python streaming_client.py
```

Output:
```
Connected to NATS
Sending streaming request to svc.ai.llm.v1.infer
This is a demo response...

Generation complete
Generation ID: gen-xyz789
Finish reason: stop
Total tokens: 150
```

## Architecture

```
┌─────────────┐         NATS         ┌─────────────┐
│   Client    │ ──────────────────>  │   Service   │
│  (Example)  │ <────────────────── │  (Example)  │
└─────────────┘      Protobuf        └─────────────┘

Subject: svc.ai.llm.v1.infer
Queue Group: q.ai.llm.infer (load balanced)
Protocol: Protobuf binary
```

## Integration with HTTP Gateway

Clients can also use HTTP gateway for gradual migration:

```bash
# HTTP request (gateway translates to NATS)
curl -X POST http://localhost:8000/ai/llm/infer \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "gpt-5-pro",
    "input": {"prompt": "Hello"},
    "params": {"temperature": 0.7}
  }'
```

Gateway translates:
1. HTTP JSON → Protobuf
2. POST /ai/llm/infer → svc.ai.llm.v1.infer
3. NATS request/reply
4. Protobuf → HTTP JSON

## Production Deployment

For production services:

1. **Use NATSClient SDK** (not these examples directly)
2. **Add OpenTelemetry tracing** (sdk.otel)
3. **Add circuit breakers** (sdk.circuit_breaker)
4. **Add health checks** (/health, /ready endpoints)
5. **Add metrics** (Prometheus)
6. **Add logging** (structured JSON logs)
7. **Configure timeouts** (per-route)
8. **Handle reconnects** (automatic in SDK)

See `services/ai_integration/` for full production implementation.

## Troubleshooting

### "Connection refused"
- Ensure NATS server is running on localhost:4222
- Check firewall rules
- Verify NATS_URL environment variable

### "No responders"
- Service not running or not subscribed to subject
- Check subject name matches exactly
- Check queue group name

### "Timeout"
- Service too slow to respond
- Increase timeout parameter
- Check service logs for errors

### "Protobuf parse error"
- Protobuf schema mismatch
- Regenerate protobuf files
- Check proto package versions match

## References

- [NATS Documentation](https://docs.nats.io/)
- [Protocol Buffers](https://protobuf.dev/)
- [ADR-002: NATS Binary Messaging](../docs/architecture/ADR-002-NATS-Binary-Messaging.md)
- [SDK Documentation](../sdk/README.md)

