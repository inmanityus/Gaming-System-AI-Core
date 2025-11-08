"""
Distributed Event Publisher using AWS SNS
Replaces direct event_bus imports with message queue
"""

import json
import os
from typing import Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError


class DistributedEventPublisher:
    """Publishes events to AWS SNS for distributed consumption."""
    
    def __init__(self, topic_arn: Optional[str] = None):
        """
        Initialize event publisher.
        
        Args:
            topic_arn: SNS topic ARN. If None, reads from environment.
        """
        self.topic_arn = topic_arn or os.getenv("WEATHER_EVENTS_TOPIC_ARN")
        self.sns_client = boto3.client('sns', region_name=os.getenv("AWS_REGION", "us-east-1"))
        
    async def publish_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        attributes: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Publish event to SNS topic.
        
        Args:
            event_type: Type of event (e.g., "weather.changed", "weather.severe")
            data: Event payload data
            attributes: Optional message attributes for filtering
            
        Returns:
            True if published successfully, False otherwise
        """
        try:
            message = {
                "event_type": event_type,
                "source": "weather-manager",
                "data": data
            }
            
            # Build message attributes for SNS filtering
            message_attributes = {
                "event_type": {
                    "DataType": "String",
                    "StringValue": event_type
                },
                "source": {
                    "DataType": "String",
                    "StringValue": "weather-manager"
                }
            }
            
            if attributes:
                for key, value in attributes.items():
                    message_attributes[key] = {
                        "DataType": "String",
                        "StringValue": str(value)
                    }
            
            # Publish to SNS
            response = self.sns_client.publish(
                TopicArn=self.topic_arn,
                Message=json.dumps(message),
                MessageAttributes=message_attributes
            )
            
            print(f"[EVENT PUBLISHER] Published {event_type}: {response['MessageId']}")
            return True
            
        except ClientError as e:
            print(f"[EVENT PUBLISHER] Failed to publish {event_type}: {e}")
            return False
        except Exception as e:
            print(f"[EVENT PUBLISHER] Unexpected error publishing {event_type}: {e}")
            return False


# Singleton instance
_publisher: Optional[DistributedEventPublisher] = None


def get_event_publisher() -> DistributedEventPublisher:
    """Get or create event publisher singleton."""
    global _publisher
    if _publisher is None:
        _publisher = DistributedEventPublisher()
    return _publisher


async def publish_weather_event(event_type: str, data: Dict[str, Any]) -> bool:
    """
    Convenience function to publish weather events.
    
    Args:
        event_type: Type of weather event
        data: Event data
        
    Returns:
        True if published successfully
    """
    publisher = get_event_publisher()
    return await publisher.publish_event(event_type, data)

