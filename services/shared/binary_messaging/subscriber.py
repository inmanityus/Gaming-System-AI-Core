"""
Distributed Event Subscriber using AWS SQS
Subscribes to events from SNS topics via SQS queue
"""

import json
import os
import asyncio
from typing import Callable, Dict, Any, Optional
import boto3
from botocore.exceptions import ClientError


class DistributedEventSubscriber:
    """Subscribes to events via SQS queue."""
    
    def __init__(self, queue_url: Optional[str] = None):
        """
        Initialize event subscriber.
        
        Args:
            queue_url: SQS queue URL. If None, reads from environment.
        """
        self.queue_url = queue_url or os.getenv("WEATHER_MANAGER_QUEUE_URL")
        self.sqs_client = boto3.client('sqs', region_name=os.getenv("AWS_REGION", "us-east-1"))
        self.running = False
        self.handlers: Dict[str, Callable] = {}
        
    def subscribe(self, event_type: str, handler: Callable):
        """
        Register a handler for specific event type.
        
        Args:
            event_type: Type of event to handle (e.g., "time.changed")
            handler: Async function to call when event received
        """
        self.handlers[event_type] = handler
        print(f"[EVENT SUBSCRIBER] Registered handler for {event_type}")
        
    def unsubscribe(self, event_type: str):
        """Unregister handler for event type."""
        if event_type in self.handlers:
            del self.handlers[event_type]
            print(f"[EVENT SUBSCRIBER] Unregistered handler for {event_type}")
    
    async def start(self):
        """Start polling for messages."""
        if not self.queue_url:
            print("[EVENT SUBSCRIBER] No queue URL configured, skipping event subscription")
            return
            
        self.running = True
        print(f"[EVENT SUBSCRIBER] Started polling queue: {self.queue_url}")
        
        while self.running:
            try:
                # Poll for messages
                response = self.sqs_client.receive_message(
                    QueueUrl=self.queue_url,
                    MaxNumberOfMessages=10,
                    WaitTimeSeconds=20,  # Long polling
                    MessageAttributeNames=['All']
                )
                
                messages = response.get('Messages', [])
                
                for message in messages:
                    try:
                        # Parse SNS message
                        body = json.loads(message['Body'])
                        
                        # SNS wraps the actual message
                        if 'Message' in body:
                            event_data = json.loads(body['Message'])
                        else:
                            event_data = body
                        
                        event_type = event_data.get('event_type')
                        
                        # Call handler if registered
                        if event_type in self.handlers:
                            handler = self.handlers[event_type]
                            if asyncio.iscoroutinefunction(handler):
                                await handler(event_data)
                            else:
                                handler(event_data)
                        
                        # Delete processed message
                        self.sqs_client.delete_message(
                            QueueUrl=self.queue_url,
                            ReceiptHandle=message['ReceiptHandle']
                        )
                        
                    except json.JSONDecodeError as e:
                        print(f"[EVENT SUBSCRIBER] Failed to parse message: {e}")
                    except Exception as e:
                        print(f"[EVENT SUBSCRIBER] Error processing message: {e}")
                
                # Small delay if no messages
                if not messages:
                    await asyncio.sleep(1)
                    
            except ClientError as e:
                print(f"[EVENT SUBSCRIBER] SQS error: {e}")
                await asyncio.sleep(5)
            except Exception as e:
                print(f"[EVENT SUBSCRIBER] Unexpected error: {e}")
                await asyncio.sleep(5)
    
    async def stop(self):
        """Stop polling for messages."""
        self.running = False
        print("[EVENT SUBSCRIBER] Stopped polling")


# Singleton instance
_subscriber: Optional[DistributedEventSubscriber] = None


def get_event_subscriber() -> DistributedEventSubscriber:
    """Get or create event subscriber singleton."""
    global _subscriber
    if _subscriber is None:
        _subscriber = DistributedEventSubscriber()
    return _subscriber

