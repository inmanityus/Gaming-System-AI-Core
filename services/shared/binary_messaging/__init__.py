"""
Shared Binary Messaging Module for All Services
Provides unified binary Protocol Buffers event publishing/subscribing
"""

from .publisher import BinaryEventPublisher, publish_binary_event, get_publisher

__all__ = [
    'BinaryEventPublisher',
    'publish_binary_event',
    'get_publisher',
]

