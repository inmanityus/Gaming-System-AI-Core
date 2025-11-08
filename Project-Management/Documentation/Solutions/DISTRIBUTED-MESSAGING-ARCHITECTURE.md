# ✅ Solution: Distributed Messaging Architecture

## Problem Solved

**Original Issue**: weather-manager couldn't deploy to ECS because it had hard dependency on event_bus:
```python
from services.event_bus.event_bus import GameEventBus  # ❌ Hard dependency
```

This violated microservice principles and prevented independent deployment.

---

## Solution: AWS SNS/SQS Distributed Messaging

**New Architecture**: Services communicate via AWS SNS/SQS instead of direct imports:

```
weather-manager → SNS Topic → SQS Queues → Other Services
```

---

## Why Distributed Messaging is Better

### 1. ✅ True Microservice Independence
- **No code dependencies** between services
- Can deploy services independently
- Can scale services independently
- Can use different programming languages per service

### 2. ✅ Resilience
- **Async communication**: Publisher doesn't wait for subscribers
- **Message persistence**: SQS stores messages until processed
- **Automatic retry**: Failed messages automatically retried
- **Dead Letter Queues**: Failed messages moved to DLQ

### 3. ✅ Scalability
- **Fanout pattern**: One message → unlimited subscribers
- **Load distribution**: Multiple consumers per queue
- **Auto-scaling**: Scale based on queue depth
- **No bottlenecks**: No service blocks another

### 4. ✅ Observability
- **CloudWatch metrics**: Queue depth, message age, failures
- **X-Ray tracing**: Track messages across services
- **Audit trail**: All events logged
- **Easy debugging**: Inspect messages in queues

---

## Implementation

### Files Created/Modified

**New Files**:
1. `services/weather_manager/event_publisher.py` - Publishes to SNS
2. `services/weather_manager/event_subscriber.py` - Polls SQS
3. `services/weather_manager/DISTRIBUTED_MESSAGING.md` - Documentation
4. `scripts/setup-distributed-messaging.ps1` - Infrastructure automation

**Modified Files**:
1. `services/weather_manager/weather_manager.py` - Removed event_bus, uses distributed messaging
2. `services/weather_manager/requirements.txt` - Added boto3
3. `services/weather_manager/server.py` - Updated initialization

---

## Quick Start

### Step 1: Create AWS Infrastructure

```powershell
# Automated setup
.\scripts\setup-distributed-messaging.ps1

# Output:
# - SNS Topic ARN
# - SQS Queue URL  
# - IAM Policy ARN
# - Environment variables for ECS
```

### Step 2: Update ECS Task Definition

Add environment variables from setup script output:
```json
{
  "environment": [
    {"name": "WEATHER_EVENTS_TOPIC_ARN", "value": "arn:aws:sns:us-east-1:..."},
    {"name": "AWS_REGION", "value": "us-east-1"}
  ],
  "taskRoleArn": "arn:aws:iam::695353648052:role/weatherManagerTaskRole"
}
```

### Step 3: Deploy

```powershell
# Rebuild image
cd services/weather_manager
docker build -t weather-manager:latest .

# Push to ECR
docker tag weather-manager:latest 695353648052.dkr.ecr.us-east-1.amazonaws.com/bodybroker-services:weather_manager-latest
docker push 695353648052.dkr.ecr.us-east-1.amazonaws.com/bodybroker-services:weather_manager-latest

# Update service
aws ecs update-service --cluster gaming-system-cluster --service weather-manager --force-new-deployment
```

---

## Usage Examples

### Publishing Events

```python
from event_publisher import publish_weather_event

# Weather changed
await publish_weather_event("weather.changed", {
    "old_state": "clear",
    "new_state": "rain",
    "intensity": 0.7,
    "temperature": 18.5
})
```

### Subscribing to Events (Optional)

```python
from event_subscriber import get_event_subscriber

subscriber = get_event_subscriber()

async def handle_time_change(event):
    time_state = event.get("data", {}).get("time_state")
    print(f"Time changed to: {time_state}")

subscriber.subscribe("time.changed", handle_time_change)
await subscriber.start()
```

---

## Event Flow

```
1. Weather Manager detects state change
   ↓
2. publish_weather_event("weather.changed", data)
   ↓
3. Event sent to SNS Topic (weather-events)
   ↓
4. SNS fans out to all subscribed SQS queues
   ↓
5. Subscribers poll their queues
   ↓
6. Process event and delete from queue
```

---

## Comparison: Before vs After

### Before (Direct Import)
```python
# ❌ Hard dependency
from services.event_bus.event_bus import GameEventBus

event_bus = GameEventBus()
await event_bus.publish(event)
```

**Problems**:
- Can't deploy weather-manager without event_bus
- Services tightly coupled
- Requires entire services/ directory in container
- Synchronous (blocks on publish)

### After (Distributed Messaging)
```python
# ✅ No dependencies
from event_publisher import publish_weather_event

await publish_weather_event("weather.changed", data)
```

**Benefits**:
- Can deploy weather-manager independently
- Services completely decoupled
- Only needs boto3 SDK
- Asynchronous (doesn't block)
- Automatic retry and persistence
- CloudWatch observability

---

## Cost Analysis

### SNS/SQS Pricing

| Usage Level | Monthly Cost |
|-------------|--------------|
| 1M events | ~$1.00 |
| 10M events | ~$10.00 |
| 100M events | ~$90.00 |

**First 1 million requests per month are FREE!**

### Cost Optimization

1. **Long polling** (already implemented): Reduces SQS requests
2. **Batch publishing**: Send multiple events in one request
3. **Message filtering**: Subscribers only receive relevant events
4. **Same-region**: Free data transfer within us-east-1

**Estimated Cost for Gaming System**: < $5/month

---

## Monitoring Dashboard

### Key Metrics to Watch

1. **SNS**:
   - `NumberOfMessagesPublished`: Event publication rate
   - `NumberOfNotificationsFailed`: Delivery failures

2. **SQS**:
   - `ApproximateNumberOfMessagesVisible`: Queue backlog
   - `ApproximateAgeOfOldestMessage`: Processing latency
   - `NumberOfMessagesDeleted`: Successful processing rate

3. **CloudWatch Alarms**:
   - Alert if queue depth > 1000 messages
   - Alert if oldest message > 5 minutes
   - Alert if delivery failures > 1%

---

## Testing

### Local Development (No AWS)

Set environment variable to skip AWS:
```powershell
$env:WEATHER_EVENTS_TOPIC_ARN = ""  # Empty = skip publishing
```

Weather Manager will log events but not publish to SNS (graceful degradation).

### Integration Testing (With LocalStack)

```bash
# Start LocalStack
docker run -d -p 4566:4566 localstack/localstack

# Configure
export AWS_ENDPOINT_URL=http://localhost:4566
export WEATHER_EVENTS_TOPIC_ARN=arn:aws:sns:us-east-1:000000000000:weather-events
```

---

## Migration Guide

### For Other Services

If other services also need to move from event_bus to distributed messaging:

1. **Copy event_publisher.py and event_subscriber.py** to the service
2. **Replace direct imports**:
   ```python
   # Old
   from services.event_bus.event_bus import GameEventBus
   
   # New
   from event_publisher import publish_weather_event
   ```
3. **Update requirements.txt**: Add boto3
4. **Update task definition**: Add SNS/SQS environment variables and IAM policy
5. **Deploy**: Rebuild and redeploy

**Time per service**: ~30-45 minutes

---

## Future Enhancements

### 1. Event Schema Validation

Add JSON Schema validation to ensure event structure:
```python
schema = {
    "type": "object",
    "properties": {
        "event_type": {"type": "string"},
        "data": {"type": "object"}
    },
    "required": ["event_type", "data"]
}
```

### 2. Event Versioning

Support multiple event versions:
```python
await publish_weather_event(
    "weather.changed",
    data,
    attributes={"version": "v2"}
)
```

### 3. Message Filtering

Use SNS filter policies so subscribers only receive relevant events:
```json
{
  "event_type": ["weather.severe"],
  "intensity": [{"numeric": [">=", 0.8]}]
}
```

### 4. Dead Letter Queue

Configure DLQ for failed messages:
```bash
aws sqs create-queue --queue-name weather-events-dlq
```

---

## Troubleshooting

### Events Not Being Received

1. Check SNS subscription: `aws sns list-subscriptions-by-topic`
2. Check SQS permissions: `aws sqs get-queue-attributes --attribute-names Policy`
3. Check IAM task role has SNS:Publish and SQS:ReceiveMessage
4. Check CloudWatch Logs for errors

### High Queue Depth

1. Scale up ECS service (more consumers)
2. Optimize event handlers (process faster)
3. Enable batch processing (10 messages at once)
4. Check for errors causing reprocessing

---

## Success Criteria

### ✅ Achieved

- [x] Removed hard dependency on event_bus
- [x] Implemented SNS publishing
- [x] Implemented SQS subscription
- [x] Created infrastructure automation
- [x] Documented architecture
- [x] Backward compatible (graceful degradation if SNS not configured)

### 🎯 Next Steps

- [ ] Run infrastructure setup script
- [ ] Update ECS task definition
- [ ] Redeploy weather-manager
- [ ] Verify service starts successfully
- [ ] Monitor CloudWatch metrics

---

## References

- **Implementation Details**: `services/weather_manager/DISTRIBUTED_MESSAGING.md`
- **Setup Script**: `scripts/setup-distributed-messaging.ps1`
- **AWS SNS**: https://docs.aws.amazon.com/sns/
- **AWS SQS**: https://docs.aws.amazon.com/sqs/
- **Event-Driven Architecture**: https://aws.amazon.com/event-driven-architecture/

---

**Status**: ✅ Ready for Deployment  
**Impact**: Unblocks weather-manager ECS deployment  
**Effort**: Infrastructure setup (10 min) + Deploy (5 min)  
**Date**: 2025-11-07  
**Author**: Claude Sonnet 4.5  
**AWS Account**: 695353648052

