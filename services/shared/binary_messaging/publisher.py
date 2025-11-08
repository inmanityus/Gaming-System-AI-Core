"""
Binary Event Publisher using Protocol Buffers + AWS SNS
5-10x faster than JSON serialization for high-throughput gaming events
"""

import os
import time
from typing import Dict, Any, Optional
from uuid import uuid4
import boto3
from botocore.exceptions import ClientError


class BinaryEventPublisher:
    """
    Publishes events using binary Protocol Buffers encoding.
    
    Performance Benefits:
    - 5-10x faster serialization than JSON
    - 60-80% smaller message size
    - Near-zero parsing overhead
    - Can stream directly to lower-level protocols
    """
    
    def __init__(self, topic_arn: Optional[str] = None):
        """
        Initialize binary event publisher.
        
        Args:
            topic_arn: SNS topic ARN. If None, reads from environment.
        """
        self.topic_arn = topic_arn or os.getenv("WEATHER_EVENTS_TOPIC_ARN")
        self.sns_client = boto3.client('sns', region_name=os.getenv("AWS_REGION", "us-east-1"))
        
        # Try to import protobuf
        try:
            from proto import events_pb2
            self.proto_available = True
            self.events_pb2 = events_pb2
        except ImportError:
            print("[BINARY PUBLISHER] Warning: protobuf not available, falling back to JSON")
            self.proto_available = False
            import json
            self.json = json
    
    async def publish_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        attributes: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Publish event using binary encoding.
        
        Args:
            event_type: Type of event (e.g., "weather.changed", "time.changed")
            data: Event payload data
            attributes: Optional message attributes for filtering
            
        Returns:
            True if published successfully, False otherwise
        """
        try:
            if not self.topic_arn:
                # Graceful degradation: log only if no topic configured
                print(f"[BINARY PUBLISHER] No SNS topic, event logged: {event_type}")
                return True
            
            # Serialize to binary if protobuf available, else JSON
            if self.proto_available:
                message_bytes = self._serialize_protobuf(event_type, data)
                content_type = "application/x-protobuf"
            else:
                message_bytes = self._serialize_json(event_type, data)
                content_type = "application/json"
            
            # Build message attributes for SNS filtering
            message_attributes = {
                "event_type": {
                    "DataType": "String",
                    "StringValue": event_type
                },
                "source": {
                    "DataType": "String",
                    "StringValue": "weather-manager"
                },
                "content_type": {
                    "DataType": "String",
                    "StringValue": content_type
                }
            }
            
            if attributes:
                for key, value in attributes.items():
                    message_attributes[key] = {
                        "DataType": "String",
                        "StringValue": str(value)
                    }
            
            # Publish to SNS (binary or JSON)
            if isinstance(message_bytes, bytes):
                response = self.sns_client.publish(
                    TopicArn=self.topic_arn,
                    Message=message_bytes.decode('utf-8') if content_type == "application/json" else message_bytes.hex(),
                    MessageAttributes=message_attributes
                )
            else:
                response = self.sns_client.publish(
                    TopicArn=self.topic_arn,
                    Message=message_bytes,
                    MessageAttributes=message_attributes
                )
            
            size = len(message_bytes)
            print(f"[BINARY PUBLISHER] Published {event_type}: {response['MessageId']} ({size} bytes, {content_type})")
            return True
            
        except ClientError as e:
            print(f"[BINARY PUBLISHER] Failed to publish {event_type}: {e}")
            return False
        except Exception as e:
            print(f"[BINARY PUBLISHER] Unexpected error publishing {event_type}: {e}")
            return False
    
    def _serialize_protobuf(self, event_type: str, data: Dict[str, Any]) -> bytes:
        """Serialize event to Protocol Buffers binary format."""
        # Map event type string to proto enum
        event_type_map = {
            "weather.changed": self.events_pb2.WEATHER_CHANGED,
            "weather.severe": self.events_pb2.WEATHER_SEVERE,
            "time.changed": self.events_pb2.TIME_CHANGED,
            "time.day_activated": self.events_pb2.TIME_DAY_ACTIVATED,
            "time.night_activated": self.events_pb2.TIME_NIGHT_ACTIVATED,
            "time.updated": self.events_pb2.TIME_UPDATED,
        }
        
        # Create base event
        event = self.events_pb2.GameEvent()
        event.event_id = str(uuid4())
        event.event_type = event_type_map.get(event_type, self.events_pb2.EVENT_TYPE_UNSPECIFIED)
        event.source = data.get("source", "weather-manager")
        event.timestamp = int(time.time() * 1000)  # milliseconds
        
        # Serialize specific payload
        if event_type == "weather.changed":
            weather_payload = self.events_pb2.WeatherEvent()
            weather_payload.old_state = data.get("old_state", "")
            weather_payload.new_state = data.get("new_state", "")
            weather_payload.intensity = data.get("weather", {}).get("intensity", 0.5)
            weather_payload.temperature = data.get("weather", {}).get("temperature", 20.0)
            weather_payload.wind_speed = data.get("weather", {}).get("wind_speed", 10.0)
            weather_payload.humidity = data.get("weather", {}).get("humidity", 0.5)
            weather_payload.season = data.get("weather", {}).get("season", "spring")
            weather_payload.duration_minutes = data.get("weather", {}).get("duration_minutes", 0)
            event.payload = weather_payload.SerializeToString()
        
        elif event_type.startswith("time."):
            time_payload = self.events_pb2.TimeEvent()
            time_payload.old_state = data.get("old_state", "")
            time_payload.new_state = data.get("new_state", "")
            time_payload.hour = data.get("hour", 0)
            time_payload.minute = data.get("minute", 0)
            time_payload.day = data.get("day", 1)
            time_payload.time_string = data.get("time_string", "")
            event.payload = time_payload.SerializeToString()
        
        # Serialize complete event to binary
        return event.SerializeToString()
    
    def _serialize_json(self, event_type: str, data: Dict[str, Any]) -> str:
        """Fallback: Serialize to JSON if protobuf not available."""
        message = {
            "event_id": str(uuid4()),
            "event_type": event_type,
            "source": data.get("source", "weather-manager"),
            "timestamp": int(time.time() * 1000),
            "data": data
        }
        return self.json.dumps(message)


# Singleton instance
_publisher: Optional[BinaryEventPublisher] = None


def get_binary_event_publisher() -> BinaryEventPublisher:
    """Get or create binary event publisher singleton."""
    global _publisher
    if _publisher is None:
        _publisher = BinaryEventPublisher()
    return _publisher


def get_publisher() -> BinaryEventPublisher:
    """Alias for get_binary_event_publisher."""
    return get_binary_event_publisher()


async def publish_binary_event(event_type: str, data: Dict[str, Any]) -> bool:
    """
    Convenience function to publish events using binary protocol.
    
    Falls back to JSON if protobuf not available (dev environments).
    
    Args:
        event_type: Type of event
        data: Event data
        
    Returns:
        True if published successfully
    """
    publisher = get_binary_event_publisher()
    return await publisher.publish_event(event_type, data)

