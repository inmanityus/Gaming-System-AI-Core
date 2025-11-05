"""
gRPC Server for Language System
Implements LanguageService protocol for real-time language generation
"""

import asyncio
import logging
from typing import Dict, Any, AsyncIterator
import grpc
from concurrent import futures

from ..core.language_definition import LanguageRegistry
from ..generation.sentence_generator import SentenceGenerator, SentenceRequest
from ..translation.translator import Translator
from ..translation.interpreter import Interpreter
from ..data.language_definitions import (
    create_vampire_language,
    create_werewolf_language,
    create_zombie_language,
    create_ghoul_language,
    create_lich_language,
    create_italian_language,
    create_french_language,
    create_spanish_language,
    create_common_language,
    create_music_language,
)

# Import generated protobuf code
from ..proto import language_service_pb2, language_service_pb2_grpc

logger = logging.getLogger(__name__)


class LanguageSystemServicer:
    """Implementation of LanguageService gRPC service"""
    
    def __init__(self):
        self.language_registry = LanguageRegistry()
        self.sentence_generator = SentenceGenerator()
        self.translator = Translator()
        self.interpreter = Interpreter()
        self._register_languages()
    
    def _register_languages(self):
        """Register all language definitions"""
        languages = [
            create_vampire_language(),
            create_werewolf_language(),
            create_zombie_language(),
            create_ghoul_language(),
            create_lich_language(),
            create_italian_language(),
            create_french_language(),
            create_spanish_language(),
            create_common_language(),
            create_music_language(),
        ]
        
        for language in languages:
            self.language_registry.register(language)
        
        logger.info(f"Registered {len(languages)} languages for gRPC service")
    
    async def GenerateSentence(
        self,
        request,
        context: grpc.aio.ServicerContext
    ):
        """Generate a sentence in the specified language"""
        try:
            language = self.language_registry.get(request.language_name)
            if not language:
                await context.set_code(grpc.StatusCode.NOT_FOUND)
                await context.set_details(f"Language '{request.language_name}' not found")
                return None
            
            sentence_request = SentenceRequest(
                language=language,
                intent=request.intent,
                context=dict(request.context),
                emotion=request.emotion,
                complexity=request.complexity,
            )
            
            sentence = self.sentence_generator.generate(sentence_request)
            
            # Convert to response
            response = language_service_pb2.GenerateSentenceResponse(
                sentence=sentence,
                language_name=request.language_name,
                intent=request.intent,
                phonemes="",  # TODO: Add phoneme generation
                metadata={}
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating sentence: {e}", exc_info=True)
            await context.set_code(grpc.StatusCode.INTERNAL)
            await context.set_details(str(e))
            return None
    
    async def GenerateSentenceStream(
        self,
        request,
        context: grpc.aio.ServicerContext
    ) -> AsyncIterator:
        """Stream sentence generation token by token"""
        try:
            language = self.language_registry.get(request.language_name)
            if not language:
                await context.set_code(grpc.StatusCode.NOT_FOUND)
                await context.set_details(f"Language '{request.language_name}' not found")
                return
            
            sentence_request = SentenceRequest(
                language=language,
                intent=request.intent,
                context=dict(request.context),
                emotion=request.emotion,
                complexity=request.complexity,
            )
            
            sentence = self.sentence_generator.generate(sentence_request)
            
            # Stream tokens (simplified - split by words)
            words = sentence.split()
            total_words = len(words)
            
            for i, word in enumerate(words):
                token = language_service_pb2.SentenceToken(
                    token=word + (" " if i < total_words - 1 else ""),
                    is_complete=(i == total_words - 1),
                    progress=(i + 1) / total_words if total_words > 0 else 1.0
                )
                yield token
                await asyncio.sleep(0.05)  # Small delay for streaming effect
            
        except Exception as e:
            logger.error(f"Error streaming sentence: {e}", exc_info=True)
            await context.set_code(grpc.StatusCode.INTERNAL)
            await context.set_details(str(e))
    
    async def Translate(
        self,
        request,
        context: grpc.aio.ServicerContext
    ):
        """Translate text between languages"""
        try:
            from_lang = self.language_registry.get(request.from_language)
            to_lang = self.language_registry.get(request.to_language)
            
            if not from_lang or not to_lang:
                await context.set_code(grpc.StatusCode.NOT_FOUND)
                await context.set_details("Source or target language not found")
                return None
            
            translation = await self.translator.translate(
                text=request.text,
                from_language=from_lang,
                to_language=to_lang,
                context=dict(request.context),
                proficiency_level=request.proficiency_level
            )
            
            response = language_service_pb2.TranslateResponse(
                translated_text=translation.text,
                from_language=request.from_language,
                to_language=request.to_language,
                confidence=translation.confidence,
                cultural_notes=translation.cultural_notes or {}
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error translating: {e}", exc_info=True)
            await context.set_code(grpc.StatusCode.INTERNAL)
            await context.set_details(str(e))
            return None
    
    async def Interpret(
        self,
        request,
        context: grpc.aio.ServicerContext
    ):
        """Provide contextual interpretation"""
        try:
            language = self.language_registry.get(request.language)
            if not language:
                await context.set_code(grpc.StatusCode.NOT_FOUND)
                await context.set_details(f"Language '{request.language}' not found")
                return None
            
            interpretation = await self.interpreter.interpret(
                text=request.text,
                language=language,
                context=dict(request.context),
                include_hidden_meanings=request.include_hidden_meanings
            )
            
            response = language_service_pb2.InterpretResponse(
                literal_translation=interpretation.literal_translation,
                contextual_meaning=interpretation.contextual_meaning,
                cultural_context=interpretation.cultural_context or {},
                hidden_meanings=list(interpretation.hidden_meanings or []),
                metadata=interpretation.metadata or {}
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error interpreting: {e}", exc_info=True)
            await context.set_code(grpc.StatusCode.INTERNAL)
            await context.set_details(str(e))
            return None
    
    async def ListLanguages(
        self,
        request,
        context: grpc.aio.ServicerContext
    ):
        """List all available languages"""
        try:
            all_languages = self.language_registry.list_all()
            
            language_infos = []
            for lang_name in all_languages:
                lang = self.language_registry.get(lang_name)
                if lang:
                    # Filter by type if specified
                    if request.language_type and lang.language_type.value != request.language_type:
                        continue
                    
                    info = language_service_pb2.LanguageInfo(
                        name=lang.name,
                        language_type=lang.language_type.value,
                        language_family=lang.language_family,
                        culture=lang.culture,
                        level=lang.level,
                        description=lang.metadata.get("description", "")
                    )
                    language_infos.append(info)
            
            response = language_service_pb2.ListLanguagesResponse(
                languages=language_infos
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error listing languages: {e}", exc_info=True)
            await context.set_code(grpc.StatusCode.INTERNAL)
            await context.set_details(str(e))
            return None
    
    async def GetLanguage(
        self,
        request,
        context: grpc.aio.ServicerContext
    ):
        """Get detailed language definition"""
        try:
            language = self.language_registry.get(request.language_name)
            if not language:
                await context.set_code(grpc.StatusCode.NOT_FOUND)
                await context.set_details(f"Language '{request.language_name}' not found")
                return None
            
            info = language_service_pb2.LanguageInfo(
                name=language.name,
                language_type=language.language_type.value,
                language_family=language.language_family,
                culture=language.culture,
                level=language.level,
                description=language.metadata.get("description", "")
            )
            
            # Convert phonemes and grammar to maps
            phonemes_map = {
                "vowels": ",".join(language.phoneme_inventory.vowels),
                "consonants": ",".join(language.phoneme_inventory.consonants),
            }
            
            grammar_map = {
                "word_order": language.grammar_rules.word_order,
                "sentence_structure": language.grammar_rules.sentence_structure,
            }
            
            response = language_service_pb2.GetLanguageResponse(
                language=info,
                phonemes=phonemes_map,
                grammar_rules=grammar_map,
                vocabulary_size=len(language.lexicon.words)
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error getting language: {e}", exc_info=True)
            await context.set_code(grpc.StatusCode.INTERNAL)
            await context.set_details(str(e))
            return None
    
    async def HealthCheck(
        self,
        request,
        context: grpc.aio.ServicerContext
    ):
        """Health check endpoint"""
        response = language_service_pb2.HealthCheckResponse(
            status="healthy",
            service="language-system",
            version="1.0.0"
        )
        return response


class LanguageSystemGRPCServer:
    """gRPC server for Language System"""
    
    def __init__(self, port: int = 50051, max_workers: int = 10):
        self.port = port
        self.max_workers = max_workers
        self.server = None
        self.servicer = None
    
    async def start(self):
        """Start the gRPC server"""
        self.servicer = LanguageSystemServicer()
        
        self.server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=self.max_workers))
        language_service_pb2_grpc.add_LanguageServiceServicer_to_server(
            self.servicer, self.server
        )
        
        listen_addr = f'[::]:{self.port}'
        self.server.add_insecure_port(listen_addr)
        
        await self.server.start()
        logger.info(f"Language System gRPC server started on port {self.port}")
    
    async def stop(self, grace_period: float = 5.0):
        """Stop the gRPC server"""
        if self.server:
            await self.server.stop(grace_period)
            logger.info("Language System gRPC server stopped")
    
    async def wait_for_termination(self):
        """Wait for server termination"""
        if self.server:
            await self.server.wait_for_termination()


async def serve():
    """Main server entry point"""
    server = LanguageSystemGRPCServer(port=50051)
    await server.start()
    await server.wait_for_termination()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(serve())

