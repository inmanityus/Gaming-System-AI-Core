# Distributed Messaging Architecture for Weather Manager

## Overview

The Weather Manager service has been refactored to use **AWS SNS/SQS** for distributed messaging instead of direct Python imports between services. This enables true microservice architecture where services are completely decoupled.

---

## Architecture

```
┌─────────────────┐         ┌──────────┐         ┌─────────────────┐
│ Weather Manager │────────>│ SNS Topic│────────>│  Subscribers    │
│   (Publisher)   │ Publish │  weather-│ Fanout  │  (SQS Queues)   │
└─────────────────┘         │  events  │         └─────────────────┘
                            └──────────┘               │
                                 │                     │
                                 │                     ▼
                                 │              ┌──────────────┐
                                 └─────────────>│ Other Services│
                                                │ (Subscribers) │
                                                └──────────────┘
```

### Components

1. **SNS Topic** (`weather-events`): Central event hub
2. **SQS Queues**: One per subscribing service
3. **Event Publisher** (`event_publisher.py`): Publishes to SNS
4. **Event Subscriber** (`event_subscriber.py`): Polls SQS queue

---

## Benefits of Distributed Messaging

### ✅ True Microservice Independence
- **No code dependencies** between services
- Services can be deployed independently
- Can scale services independently
- Can use different tech stacks per service

### ✅ Resilience & Reliability
- **Async communication**: Services don't fail if subscribers are down
- **Message persistence**: SQS stores messages until processed
- **Retry logic**: Failed messages automatically retried
- **Dead Letter Queues**: Failed messages go to DLQ for investigation

### ✅ Scalability
- **Fanout pattern**: One message → many subscribers
- **Load distribution**: Multiple consumers per queue
- **Auto-scaling**: Scale based on queue depth
- **No bottlenecks**: No single service blocks others

### ✅ Observability
- **CloudWatch metrics**: Queue depth, message age, delivery failures
- **X-Ray tracing**: Track messages across services
- **Audit trail**: All events logged
- **Debugging**: Inspect messages in queues

---

## AWS Infrastructure Required

### 1. SNS Topic

```bash
# Create SNS topic for weather events
aws sns create-topic --name weather-events --region us-east-1

# Output: arn:aws:sns:us-east-1:695353648052:weather-events
```

### 2. SQS Queue (per subscribing service)

```bash
# Create SQS queue for weather-manager
aws sqs create-queue --queue-name weather-manager-events --region us-east-1

# Subscribe queue to SNS topic
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:695353648052:weather-events \
  --protocol sqs \
  --notification-endpoint arn:aws:sqs:us-east-1:695353648052:weather-manager-events
```

### 3. IAM Permissions

**For ECS Task Role** (to publish/subscribe):
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sns:Publish"
      ],
      "Resource": "arn:aws:sns:us-east-1:695353648052:weather-events"
    },
    {
      "Effect": "Allow",
      "Action": [
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes"
      ],
      "Resource": "arn:aws:sqs:us-east-1:695353648052:weather-manager-events"
    }
  ]
}
```

---

## Environment Variables

### Required for ECS Deployment

```bash
# For publishing events
WEATHER_EVENTS_TOPIC_ARN=arn:aws:sns:us-east-1:695353648052:weather-events
AWS_REGION=us-east-1

# For subscribing to events (optional)
WEATHER_MANAGER_QUEUE_URL=https://sqs.us-east-1.amazonaws.com/695353648052/weather-manager-events
```

---

## Usage Examples

### Publishing Events

```python
from event_publisher import publish_weather_event

# Publish weather change
await publish_weather_event(
    "weather.changed",
    {
        "old_state": "clear",
        "new_state": "rain",
        "intensity": 0.7
    }
)
```

### Subscribing to Events

```python
from event_subscriber import get_event_subscriber

subscriber = get_event_subscriber()

# Register handler
async def handle_weather_change(event):
    print(f"Weather changed: {event['data']}")

subscriber.subscribe("weather.changed", handle_weather_change)

# Start polling
await subscriber.start()
```

---

## Event Types

### Published by Weather Manager

| Event Type | Description | Data |
|------------|-------------|------|
| `weather.changed` | Weather state changed | `old_state`, `new_state`, `weather` |
| `weather.severe` | Severe weather alert | `state`, `intensity`, `warning` |
| `season.changed` | Season changed | `old_season`, `new_season` |

### Subscribed by Weather Manager (Optional)

| Event Type | Source | Description |
|------------|--------|-------------|
| `time.changed` | time-manager | Time of day changed |

---

## Deployment Steps

### Step 1: Create AWS Infrastructure

```bash
# Run infrastructure setup script
./scripts/setup-distributed-messaging.sh
```

Or manually:
```bash
# 1. Create SNS topic
aws sns create-topic --name weather-events

# 2. Create SQS queue
aws sqs create-queue --queue-name weather-manager-events

# 3. Subscribe queue to topic
aws sns subscribe \
  --topic-arn <TOPIC_ARN> \
  --protocol sqs \
  --notification-endpoint <QUEUE_ARN>

# 4. Grant SNS permission to send to SQS
aws sqs set-queue-attributes \
  --queue-url <QUEUE_URL> \
  --attributes file://queue-policy.json
```

### Step 2: Update ECS Task Definition

Add environment variables and IAM permissions:

```json
{
  "taskRoleArn": "arn:aws:iam::695353648052:role/weatherManagerTaskRole",
  "containerDefinitions": [{
    "name": "weather-manager",
    "environment": [
      {
        "name": "WEATHER_EVENTS_TOPIC_ARN",
        "value": "arn:aws:sns:us-east-1:695353648052:weather-events"
      },
      {
        "name": "AWS_REGION",
        "value": "us-east-1"
      }
    ]
  }]
}
```

### Step 3: Deploy Service

```bash
# Rebuild Docker image
docker build -t weather-manager:latest ./services/weather_manager

# Push to ECR
docker tag weather-manager:latest 695353648052.dkr.ecr.us-east-1.amazonaws.com/bodybroker-services:weather_manager-latest
docker push 695353648052.dkr.ecr.us-east-1.amazonaws.com/bodybroker-services:weather_manager-latest

# Update ECS service
aws ecs update-service \
  --cluster gaming-system-cluster \
  --service weather-manager \
  --force-new-deployment
```

---

## Monitoring

### CloudWatch Metrics

**SNS Topic**:
- `NumberOfMessagesPublished`: Messages published to topic
- `NumberOfNotificationsFailed`: Failed deliveries

**SQS Queue**:
- `ApproximateNumberOfMessagesVisible`: Messages waiting in queue
- `ApproximateAgeOfOldestMessage`: Age of oldest unprocessed message
- `NumberOfMessagesReceived`: Messages consumed
- `NumberOfMessagesDeleted`: Messages successfully processed

### CloudWatch Alarms

```bash
# Alert if messages are aging (processing too slow)
aws cloudwatch put-metric-alarm \
  --alarm-name weather-events-queue-depth \
  --metric-name ApproximateAgeOfOldestMessage \
  --namespace AWS/SQS \
  --statistic Maximum \
  --period 300 \
  --threshold 300 \
  --comparison-operator GreaterThanThreshold
```

---

## Testing

### Local Testing (Without AWS)

For development, you can mock the publisher/subscriber:

```python
# mock_events.py
class MockEventPublisher:
    async def publish_event(self, event_type, data, attributes=None):
        print(f"[MOCK] Published {event_type}: {data}")
        return True

# Use in development
os.environ["USE_MOCK_EVENTS"] = "true"
```

### Integration Testing (With LocalStack)

```bash
# Start LocalStack for local AWS simulation
docker run -d -p 4566:4566 localstack/localstack

# Configure to use LocalStack
export AWS_ENDPOINT_URL=http://localhost:4566
```

---

## Troubleshooting

### Events Not Being Received

1. **Check SNS subscription**:
   ```bash
   aws sns list-subscriptions-by-topic --topic-arn <TOPIC_ARN>
   ```

2. **Check SQS queue permissions**:
   ```bash
   aws sqs get-queue-attributes --queue-url <QUEUE_URL> --attribute-names Policy
   ```

3. **Check IAM permissions** on ECS task role

4. **Check CloudWatch Logs** for error messages

### High Queue Depth

1. **Increase consumer count** (scale up ECS service)
2. **Optimize message processing** (reduce handler time)
3. **Check for errors** in CloudWatch Logs
4. **Enable batch processing** (process multiple messages at once)

---

## Cost Optimization

### SNS Costs
- **$0.50** per million requests (first million free)
- **Negligible** for typical weather events

### SQS Costs
- **$0.40** per million requests (first million free)
- **Free** data transfer within same region
- **Long polling** reduces costs (vs short polling)

### Estimated Monthly Cost
- **1M weather events/month**: ~$1.00
- **10M weather events/month**: ~$10.00
- **100M weather events/month**: ~$90.00

---

## Migration from Old Architecture

### Old Code (Direct Import)
```python
from services.event_bus.event_bus import GameEventBus

event_bus = GameEventBus()
await event_bus.publish(event)
```

### New Code (Distributed Messaging)
```python
from event_publisher import publish_weather_event

await publish_weather_event("weather.changed", data)
```

### Benefits
- ✅ No service dependencies
- ✅ Can deploy weather-manager independently
- ✅ Automatic retry and persistence
- ✅ Better observability

---

## Future Enhancements

### 1. Event Schema Validation
```python
# Add JSON Schema validation
schema = {
    "type": "object",
    "properties": {
        "old_state": {"type": "string"},
        "new_state": {"type": "string"}
    },
    "required": ["old_state", "new_state"]
}
```

### 2. Event Versioning
```python
# Support multiple event versions
await publish_weather_event(
    "weather.changed",
    data,
    attributes={"version": "v2"}
)
```

### 3. Message Filtering
```python
# SNS filter policy for subscribers
filter_policy = {
    "event_type": ["weather.severe"],  # Only severe weather
    "intensity": [{"numeric": [">=", 0.8]}]  # Only high intensity
}
```

### 4. Dead Letter Queue
```python
# Configure DLQ for failed messages
aws sqs create-queue --queue-name weather-events-dlq

aws sqs set-queue-attributes \
  --queue-url <QUEUE_URL> \
  --attributes RedrivePolicy='{"deadLetterTargetArn":"<DLQ_ARN>","maxReceiveCount":"3"}'
```

---

## References

- [AWS SNS Documentation](https://docs.aws.amazon.com/sns/)
- [AWS SQS Documentation](https://docs.aws.amazon.com/sqs/)
- [Microservice Patterns](https://microservices.io/patterns/index.html)
- [Event-Driven Architecture](https://aws.amazon.com/event-driven-architecture/)

---

**Last Updated**: 2025-11-07  
**Author**: Claude Sonnet 4.5  
**Status**: Production Ready  
**AWS Account**: 695353648052  
**Region**: us-east-1

