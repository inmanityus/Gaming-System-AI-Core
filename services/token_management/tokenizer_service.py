"""
Tokenizer service for counting tokens across different model providers.
"""
import tiktoken
import asyncio
from typing import List, Dict, Optional, Union
from functools import lru_cache
import logging

from .models import ModelProvider, Message


logger = logging.getLogger(__name__)


class TokenizerService:
    """Unified tokenizer service supporting multiple model providers."""
    
    def __init__(self):
        self._tokenizers = {}
        self._encoding_cache = {}
        self._initialize_tokenizers()
    
    def _initialize_tokenizers(self):
        """Initialize tokenizers for different providers."""
        try:
            # OpenAI tokenizers
            self._tokenizers["gpt-4o"] = tiktoken.encoding_for_model("gpt-4o-mini")  # Use similar model
            self._tokenizers["gpt-4"] = tiktoken.encoding_for_model("gpt-4")
            
            # Claude uses similar tokenization to GPT-4
            self._tokenizers["claude"] = tiktoken.encoding_for_model("gpt-4")
            
            # For other models, use cl100k_base as default
            self._tokenizers["default"] = tiktoken.get_encoding("cl100k_base")
        except Exception as e:
            logger.error(f"Error initializing tokenizers: {e}")
            # Fallback to basic estimation
            self._tokenizers["default"] = None
    
    @lru_cache(maxsize=1000)
    def _get_tokenizer(self, model_name: str):
        """Get appropriate tokenizer for model."""
        if model_name in self._tokenizers:
            return self._tokenizers[model_name]
        
        # Map model families to tokenizers
        if model_name.startswith("gpt"):
            return self._tokenizers.get("gpt-4", self._tokenizers["default"])
        elif model_name.startswith("claude"):
            return self._tokenizers.get("claude", self._tokenizers["default"])
        else:
            return self._tokenizers["default"]
    
    def count_tokens(
        self,
        text: Union[str, List[Dict[str, str]], List[Message]],
        model_name: str = "gpt-4"
    ) -> int:
        """
        Count tokens for text or messages.
        
        Args:
            text: String, list of message dicts, or list of Message objects
            model_name: Model name for tokenizer selection
            
        Returns:
            Token count
        """
        if isinstance(text, str):
            return self._count_text_tokens(text, model_name)
        else:
            return self._count_messages_tokens(text, model_name)
    
    def _count_text_tokens(self, text: str, model_name: str) -> int:
        """Count tokens in a text string."""
        tokenizer = self._get_tokenizer(model_name)
        
        if tokenizer is None:
            # Fallback estimation: ~4 characters per token
            return len(text) // 4
        
        try:
            tokens = tokenizer.encode(text)
            return len(tokens)
        except Exception as e:
            logger.error(f"Error counting tokens: {e}")
            return len(text) // 4
    
    def _count_messages_tokens(
        self,
        messages: Union[List[Dict[str, str]], List[Message]],
        model_name: str
    ) -> int:
        """Count tokens in a list of messages."""
        tokenizer = self._get_tokenizer(model_name)
        
        # Convert Message objects to dicts if needed
        if messages and isinstance(messages[0], Message):
            messages = [msg.to_dict() for msg in messages]
        
        if tokenizer is None:
            # Fallback estimation
            total_chars = sum(len(msg.get("content", "")) for msg in messages)
            # Add overhead for message structure
            overhead = len(messages) * 10
            return (total_chars // 4) + overhead
        
        # Accurate counting with message overhead
        total_tokens = 0
        
        # Different models have different per-message overhead
        per_message_tokens = 3  # Default overhead
        if model_name.startswith("gpt-4"):
            per_message_tokens = 3
        elif model_name.startswith("claude"):
            per_message_tokens = 4
        
        for message in messages:
            total_tokens += per_message_tokens
            
            # Role tokens
            role = message.get("role", "")
            content = message.get("content", "")
            
            if role:
                total_tokens += self._count_text_tokens(role, model_name)
            if content:
                total_tokens += self._count_text_tokens(content, model_name)
        
        # Add tokens for message separation
        total_tokens += 3  # Typical conversation ending tokens
        
        return total_tokens
    
    async def count_tokens_async(
        self,
        text: Union[str, List[Dict[str, str]], List[Message]],
        model_name: str = "gpt-4"
    ) -> int:
        """Async version of token counting."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.count_tokens,
            text,
            model_name
        )
    
    def estimate_tokens_for_summary(self, original_tokens: int) -> int:
        """
        Estimate token count after summarization.
        Typically summaries are 20-30% of original length.
        """
        return int(original_tokens * 0.25)
    
    def calculate_compression_ratio(
        self,
        original_tokens: int,
        compressed_tokens: int
    ) -> float:
        """Calculate compression ratio."""
        if original_tokens == 0:
            return 0.0
        return 1.0 - (compressed_tokens / original_tokens)
