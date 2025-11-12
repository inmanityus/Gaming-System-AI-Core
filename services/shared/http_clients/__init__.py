"""
Shared HTTP Clients for Inter-Service Communication
Eliminates direct imports between microservices
"""

from .model_management_http_client import (
    ModelManagementHTTPClient,
    get_model_management_client
)
from .state_manager_http_client import (
    StateManagerHTTPClient,
    get_state_manager_client
)

__all__ = [
    "ModelManagementHTTPClient",
    "get_model_management_client",
    "StateManagerHTTPClient",
    "get_state_manager_client",
]

