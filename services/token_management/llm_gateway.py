"""
LLM Gateway - Handles API calls with token management and streaming.
"""
import asyncio
import aiohttp
import json
from typing import Dict, List, Optional, AsyncGenerator, Any
import logging
from datetime import datetime
import os

from .models import ModelInfo, MODEL_CONFIGS, ModelProvider
from .tokenizer_service import TokenizerService
from .context_engine import ContextEngine


logger = logging.getLogger(__name__)


class LLMGateway:
    """
    Gateway for all LLM API calls with built-in token management.
    Handles streaming, retries, and prevents token limit crashes.
    """
    
    def __init__(
        self,
        context_engine: Optional[ContextEngine] = None,
        api_keys: Optional[Dict[str, str]] = None
    ):
        self.context_engine = context_engine or ContextEngine()
        self.tokenizer = TokenizerService()
        
        # API configuration
        self.api_keys = api_keys or {
            "openai": os.getenv("OPENAI_API_KEY"),
            "anthropic": os.getenv("ANTHROPIC_API_KEY"),
            "google": os.getenv("GOOGLE_API_KEY")
        }
        
        self.api_endpoints = {
            ModelProvider.OPENAI: "https://api.openai.com/v1/chat/completions",
            ModelProvider.ANTHROPIC: "https://api.anthropic.com/v1/messages",
            ModelProvider.GOOGLE: "https://generativelanguage.googleapis.com/v1/models/{model}:generateContent"
        }
        
        # Set gateway in context engine for summarization
        self.context_engine.set_llm_client(self)
        
        # Metrics
        self.metrics = {
            "api_calls": 0,
            "streaming_calls": 0,
            "retries": 0,
            "errors": 0,
            "truncated_responses": 0
        }
    
    async def create_completion(
        self,
        model: str,
        messages: List[Dict[str, str]],
        session_id: Optional[str] = None,
        stream: bool = True,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> Any:
        """
        Create a completion with automatic token management.
        
        Args:
            model: Model name
            messages: Conversation messages
            session_id: Session ID for context tracking
            stream: Whether to stream response
            temperature: Sampling temperature
            max_tokens: Max output tokens (auto-calculated if not provided)
            **kwargs: Additional model-specific parameters
            
        Returns:
            Response object or async generator for streaming
        """
        model_info = MODEL_CONFIGS.get(model)
        if not model_info:
            raise ValueError(f"Unknown model: {model}")
        
        # Process through context engine if session provided
        if session_id:
            # Extract last message as new prompt
            if not messages or not messages[-1].get("content"):
                raise ValueError("No message content provided")
            
            new_prompt = messages[-1]["content"]
            processed_messages, calculated_max_tokens = await self.context_engine.process_message(
                session_id, new_prompt, model
            )
            messages = processed_messages
            max_tokens = max_tokens or calculated_max_tokens
        else:
            # Calculate max tokens without session
            input_tokens = self.tokenizer.count_tokens(messages, model)
            max_tokens = max_tokens or model_info.calculate_max_output_tokens(input_tokens)
        
        # Ensure max_tokens is reasonable
        max_tokens = min(max_tokens, model_info.token_window.max_output_window)
        if max_tokens < 100:
            logger.warning(f"Very low max_tokens: {max_tokens}. Setting to minimum 100.")
            max_tokens = 100
        
        # Make API call
        if stream and model_info.supports_streaming:
            return self._stream_completion(
                model_info, messages, temperature, max_tokens, session_id, **kwargs
            )
        else:
            return await self._create_completion(
                model_info, messages, temperature, max_tokens, session_id, **kwargs
            )
    
    async def _create_completion(
        self,
        model_info: ModelInfo,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        session_id: Optional[str],
        **kwargs
    ) -> Dict:
        """Create non-streaming completion."""
        self.metrics["api_calls"] += 1
        
        # Build request based on provider
        request_data = self._build_request(
            model_info, messages, temperature, max_tokens, stream=False, **kwargs
        )
        
        headers = self._get_headers(model_info.provider)
        url = self._get_url(model_info)
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=request_data, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"API error: {response.status} - {error_text}")
                        self.metrics["errors"] += 1
                        raise Exception(f"API error: {response.status}")
                    
                    result = await response.json()
                    
                    # Extract content based on provider
                    content = self._extract_content(result, model_info.provider)
                    
                    # Track in session if provided
                    if session_id and messages:
                        prompt = messages[-1]["content"]
                        await self.context_engine.add_response(
                            session_id,
                            prompt,
                            content,
                            prompt_tokens=result.get("usage", {}).get("prompt_tokens"),
                            response_tokens=result.get("usage", {}).get("completion_tokens")
                        )
                    
                    # Check if response was truncated
                    if self._is_truncated(result, model_info.provider):
                        self.metrics["truncated_responses"] += 1
                        logger.warning(f"Response truncated for session {session_id}")
                    
                    return {
                        "content": content,
                        "usage": result.get("usage", {}),
                        "model": model_info.name,
                        "truncated": self._is_truncated(result, model_info.provider)
                    }
                    
        except Exception as e:
            logger.error(f"Error calling {model_info.name}: {e}")
            self.metrics["errors"] += 1
            raise
    
    async def _stream_completion(
        self,
        model_info: ModelInfo,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        session_id: Optional[str],
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream completion response."""
        self.metrics["streaming_calls"] += 1
        
        request_data = self._build_request(
            model_info, messages, temperature, max_tokens, stream=True, **kwargs
        )
        
        headers = self._get_headers(model_info.provider)
        url = self._get_url(model_info)
        
        full_response = []
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=request_data, headers=headers) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        logger.error(f"Streaming API error: {response.status} - {error_text}")
                        self.metrics["errors"] += 1
                        raise Exception(f"API error: {response.status}")
                    
                    # Stream response chunks
                    async for line in response.content:
                        line = line.decode('utf-8').strip()
                        if not line or line == "data: [DONE]":
                            continue
                        
                        if line.startswith("data: "):
                            line = line[6:]
                        
                        try:
                            chunk = json.loads(line)
                            content = self._extract_stream_content(chunk, model_info.provider)
                            if content:
                                full_response.append(content)
                                yield content
                        except json.JSONDecodeError:
                            continue
            
            # Track in session if provided
            if session_id and messages and full_response:
                prompt = messages[-1]["content"]
                response_text = "".join(full_response)
                await self.context_engine.add_response(
                    session_id, prompt, response_text
                )
                
        except Exception as e:
            logger.error(f"Streaming error for {model_info.name}: {e}")
            self.metrics["errors"] += 1
            raise
    
    def _build_request(
        self,
        model_info: ModelInfo,
        messages: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
        stream: bool,
        **kwargs
    ) -> Dict:
        """Build request data based on provider."""
        base_request = {
            "model": model_info.name,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": stream
        }
        
        if model_info.provider == ModelProvider.OPENAI:
            base_request["messages"] = messages
        elif model_info.provider == ModelProvider.ANTHROPIC:
            # Anthropic uses different format
            base_request["messages"] = messages
            base_request["max_tokens"] = max_tokens
        elif model_info.provider == ModelProvider.GOOGLE:
            # Google uses different format
            base_request = {
                "contents": [{"parts": [{"text": msg["content"]}]} for msg in messages],
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens
                }
            }
        
        # Add any additional parameters
        base_request.update(kwargs)
        return base_request
    
    def _get_headers(self, provider: ModelProvider) -> Dict[str, str]:
        """Get headers for API request."""
        headers = {"Content-Type": "application/json"}
        
        if provider == ModelProvider.OPENAI:
            headers["Authorization"] = f"Bearer {self.api_keys.get('openai', '')}"
        elif provider == ModelProvider.ANTHROPIC:
            headers["X-API-Key"] = self.api_keys.get("anthropic", "")
            headers["anthropic-version"] = "2023-06-01"
        elif provider == ModelProvider.GOOGLE:
            # Google uses API key in URL
            pass
        
        return headers
    
    def _get_url(self, model_info: ModelInfo) -> str:
        """Get API endpoint URL."""
        base_url = self.api_endpoints.get(model_info.provider, "")
        
        if model_info.provider == ModelProvider.GOOGLE:
            # Google includes model in URL
            url = base_url.format(model=model_info.name)
            api_key = self.api_keys.get("google", "")
            return f"{url}?key={api_key}"
        
        return base_url
    
    def _extract_content(self, response: Dict, provider: ModelProvider) -> str:
        """Extract content from response based on provider."""
        if provider == ModelProvider.OPENAI:
            return response["choices"][0]["message"]["content"]
        elif provider == ModelProvider.ANTHROPIC:
            return response["content"][0]["text"]
        elif provider == ModelProvider.GOOGLE:
            return response["candidates"][0]["content"]["parts"][0]["text"]
        return ""
    
    def _extract_stream_content(self, chunk: Dict, provider: ModelProvider) -> str:
        """Extract content from stream chunk based on provider."""
        try:
            if provider == ModelProvider.OPENAI:
                return chunk["choices"][0]["delta"].get("content", "")
            elif provider == ModelProvider.ANTHROPIC:
                return chunk["delta"]["text"]
            elif provider == ModelProvider.GOOGLE:
                return chunk["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            return ""
        return ""
    
    def _is_truncated(self, response: Dict, provider: ModelProvider) -> bool:
        """Check if response was truncated."""
        if provider == ModelProvider.OPENAI:
            return response["choices"][0].get("finish_reason") == "length"
        elif provider == ModelProvider.ANTHROPIC:
            return response.get("stop_reason") == "max_tokens"
        elif provider == ModelProvider.GOOGLE:
            return response["candidates"][0].get("finishReason") == "MAX_TOKENS"
        return False
    
    def get_metrics(self) -> Dict:
        """Get gateway metrics."""
        return {
            **self.metrics,
            "context_engine": self.context_engine.get_metrics()
        }
