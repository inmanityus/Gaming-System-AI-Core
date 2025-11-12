"""
gRPC Integration for Language System
Provides gRPC server and client for language generation services
"""

from language_system.grpc.grpc_server import LanguageSystemGRPCServer
from language_system.grpc.grpc_client import LanguageSystemGRPCClient

__all__ = ['LanguageSystemGRPCServer', 'LanguageSystemGRPCClient']

