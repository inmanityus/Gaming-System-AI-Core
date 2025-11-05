"""
gRPC Integration for Language System
Provides gRPC server and client for language generation services
"""

from .grpc_server import LanguageSystemGRPCServer
from .grpc_client import LanguageSystemGRPCClient

__all__ = ['LanguageSystemGRPCServer', 'LanguageSystemGRPCClient']

