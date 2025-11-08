"""
gRPC Client for Language System
Provides client interface for UE5 and other services to communicate with language system
"""

import asyncio
import logging
from typing import Dict, Any, AsyncIterator, Optional
import grpc

from proto import language_service_pb2, language_service_pb2_grpc

logger = logging.getLogger(__name__)


class LanguageSystemGRPCClient:
    """gRPC client for Language System service"""
    
    def __init__(self, host: str = "localhost", port: int = 50051):
        self.host = host
        self.port = port
        self.channel: Optional[grpc.aio.Channel] = None
        self.stub: Optional[language_service_pb2_grpc.LanguageServiceStub] = None
    
    async def connect(self):
        """Connect to the gRPC server"""
        self.channel = grpc.aio.insecure_channel(f"{self.host}:{self.port}")
        self.stub = language_service_pb2_grpc.LanguageServiceStub(self.channel)
        logger.info(f"Connected to Language System gRPC server at {self.host}:{self.port}")
    
    async def disconnect(self):
        """Disconnect from the gRPC server"""
        if self.channel:
            await self.channel.close()
            logger.info("Disconnected from Language System gRPC server")
    
    async def generate_sentence(
        self,
        language_name: str,
        intent: str,
        context: Optional[Dict[str, str]] = None,
        emotion: Optional[str] = None,
        complexity: int = 1
    ) -> Dict[str, Any]:
        """Generate a sentence in the specified language"""
        if self.stub is None:
            await self.connect()
        
        request = language_service_pb2.GenerateSentenceRequest(
            language_name=language_name,
            intent=intent,
            context=context or {},
            emotion=emotion or "",
            complexity=complexity
        )
        
        try:
            response = await self.stub.GenerateSentence(request)
            return {
                "sentence": response.sentence,
                "language_name": response.language_name,
                "intent": response.intent,
                "phonemes": response.phonemes,
                "metadata": dict(response.metadata)
            }
        except grpc.RpcError as e:
            logger.error(f"gRPC error generating sentence: {e}")
            raise
    
    async def generate_sentence_stream(
        self,
        language_name: str,
        intent: str,
        context: Optional[Dict[str, str]] = None,
        emotion: Optional[str] = None,
        complexity: int = 1
    ) -> AsyncIterator[str]:
        """Stream sentence generation token by token"""
        if self.stub is None:
            await self.connect()
        
        request = language_service_pb2.GenerateSentenceRequest(
            language_name=language_name,
            intent=intent,
            context=context or {},
            emotion=emotion or "",
            complexity=complexity
        )
        
        try:
            async for token in self.stub.GenerateSentenceStream(request):
                yield token.token
                if token.is_complete:
                    break
        except grpc.RpcError as e:
            logger.error(f"gRPC error streaming sentence: {e}")
            raise
    
    async def translate(
        self,
        text: str,
        from_language: str,
        to_language: str,
        context: Optional[Dict[str, str]] = None,
        proficiency_level: int = 1
    ) -> Dict[str, Any]:
        """Translate text between languages"""
        if self.stub is None:
            await self.connect()
        
        request = language_service_pb2.TranslateRequest(
            text=text,
            from_language=from_language,
            to_language=to_language,
            context=context or {},
            proficiency_level=proficiency_level
        )
        
        try:
            response = await self.stub.Translate(request)
            return {
                "translated_text": response.translated_text,
                "from_language": response.from_language,
                "to_language": response.to_language,
                "confidence": response.confidence,
                "cultural_notes": dict(response.cultural_notes)
            }
        except grpc.RpcError as e:
            logger.error(f"gRPC error translating: {e}")
            raise
    
    async def interpret(
        self,
        text: str,
        language: str,
        context: Optional[Dict[str, str]] = None,
        include_hidden_meanings: bool = False
    ) -> Dict[str, Any]:
        """Provide contextual interpretation"""
        if self.stub is None:
            await self.connect()
        
        request = language_service_pb2.InterpretRequest(
            text=text,
            language=language,
            context=context or {},
            include_hidden_meanings=include_hidden_meanings
        )
        
        try:
            response = await self.stub.Interpret(request)
            return {
                "literal_translation": response.literal_translation,
                "contextual_meaning": response.contextual_meaning,
                "cultural_context": dict(response.cultural_context),
                "hidden_meanings": list(response.hidden_meanings),
                "metadata": dict(response.metadata)
            }
        except grpc.RpcError as e:
            logger.error(f"gRPC error interpreting: {e}")
            raise
    
    async def list_languages(
        self,
        language_type: Optional[str] = None
    ) -> list:
        """List all available languages"""
        if self.stub is None:
            await self.connect()
        
        request = language_service_pb2.ListLanguagesRequest(
            language_type=language_type or ""
        )
        
        try:
            response = await self.stub.ListLanguages(request)
            return [
                {
                    "name": lang.name,
                    "language_type": lang.language_type,
                    "language_family": lang.language_family,
                    "culture": lang.culture,
                    "level": lang.level,
                    "description": lang.description
                }
                for lang in response.languages
            ]
        except grpc.RpcError as e:
            logger.error(f"gRPC error listing languages: {e}")
            raise
    
    async def get_language(self, language_name: str) -> Dict[str, Any]:
        """Get detailed language definition"""
        if self.stub is None:
            await self.connect()
        
        request = language_service_pb2.GetLanguageRequest(
            language_name=language_name
        )
        
        try:
            response = await self.stub.GetLanguage(request)
            return {
                "language": {
                    "name": response.language.name,
                    "language_type": response.language.language_type,
                    "language_family": response.language.language_family,
                    "culture": response.language.culture,
                    "level": response.language.level,
                    "description": response.language.description
                },
                "phonemes": dict(response.phonemes),
                "grammar_rules": dict(response.grammar_rules),
                "vocabulary_size": response.vocabulary_size
            }
        except grpc.RpcError as e:
            logger.error(f"gRPC error getting language: {e}")
            raise
    
    async def health_check(self) -> Dict[str, str]:
        """Health check"""
        if self.stub is None:
            await self.connect()
        
        request = language_service_pb2.HealthCheckRequest()
        
        try:
            response = await self.stub.HealthCheck(request)
            return {
                "status": response.status,
                "service": response.service,
                "version": response.version
            }
        except grpc.RpcError as e:
            logger.error(f"gRPC error health check: {e}")
            raise


# Context manager for easy usage
class LanguageSystemClient:
    """Context manager wrapper for LanguageSystemGRPCClient"""
    
    def __init__(self, host: str = "localhost", port: int = 50051):
        self.client = LanguageSystemGRPCClient(host, port)
    
    async def __aenter__(self):
        await self.client.connect()
        return self.client
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.disconnect()

