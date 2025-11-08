"""
Shared Binary Messaging Module for All Services
Provides unified binary Protocol Buffers event publishing/subscribing
"""

from .publisher import BinaryEventPublisher, publish_binary_event, get_publisher
from .subscriber import BinaryEventSubscriber, get_subscriber

__all__ = [
    'BinaryEventPublisher',
    'publish_binary_event',
    'get_publisher',
    'BinaryEventSubscriber',
    'get_subscriber',
]

