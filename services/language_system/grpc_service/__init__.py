from __future__ import annotations

"""
gRPC Integration for Language System
Provides gRPC server and client for language generation services
"""

from services.language_system.grpc_service.grpc_server import LanguageSystemGRPCServer
from services.language_system.grpc_service.grpc_client import LanguageSystemGRPCClient

__all__ = ['LanguageSystemGRPCServer', 'LanguageSystemGRPCClient']


