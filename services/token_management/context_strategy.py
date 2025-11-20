"""
Context management strategies for handling token limits.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Optional
import asyncio
import logging

from .models import Message, SessionState, ModelInfo
from .tokenizer_service import TokenizerService


logger = logging.getLogger(__name__)


class ContextStrategy(ABC):
    """Abstract base class for context management strategies."""
    
    def __init__(self, tokenizer_service: TokenizerService):
        self.tokenizer = tokenizer_service
    
    @abstractmethod
    async def compress_context(
        self,
        messages: List[Message],
        model_info: ModelInfo,
        target_reduction: float = 0.5
    ) -> List[Message]:
        """
        Compress context to reduce token count.
        
        Args:
            messages: List of messages to compress
            model_info: Model information for token limits
            target_reduction: Target reduction ratio (0.5 = reduce by 50%)
            
        Returns:
            Compressed list of messages
        """
        pass
    
    def estimate_compression_tokens(
        self,
        current_tokens: int,
        strategy_type: str
    ) -> int:
        """Estimate tokens after compression."""
        if strategy_type == "summarization":
            return int(current_tokens * 0.25)
        elif strategy_type == "sliding_window":
            return int(current_tokens * 0.5)
        else:
            return current_tokens


class SummarizationStrategy(ContextStrategy):
    """
    Summarize older messages to compress context.
    This maintains continuity while reducing token count.
    """
    
    def __init__(self, tokenizer_service: TokenizerService, llm_client=None):
        super().__init__(tokenizer_service)
        self.llm_client = llm_client
    
    async def compress_context(
        self,
        messages: List[Message],
        model_info: ModelInfo,
        target_reduction: float = 0.5
    ) -> List[Message]:
        """Compress context using summarization."""
        if len(messages) < 3:
            return messages
        
        # Calculate how many messages to summarize
        total_tokens = sum(msg.token_count or 0 for msg in messages)
        target_tokens = int(total_tokens * (1 - target_reduction))
        
        # Find split point - keep recent messages, summarize older ones
        recent_tokens = 0
        split_index = len(messages)
        
        for i in range(len(messages) - 1, -1, -1):
            msg_tokens = messages[i].token_count or 0
            if recent_tokens + msg_tokens > target_tokens * 0.7:  # Keep 70% as recent
                split_index = i + 1
                break
            recent_tokens += msg_tokens
        
        if split_index >= len(messages) - 2:
            # Not enough old messages to summarize
            return messages
        
        # Split messages
        old_messages = messages[:split_index]
        recent_messages = messages[split_index:]
        
        # Create summary of old messages
        summary_text = await self._create_summary(old_messages, model_info)
        
        # Create summary message
        summary_msg = Message(
            role="system",
            content=f"Summary of previous conversation:\n{summary_text}",
            token_count=self.tokenizer.count_tokens(summary_text, model_info.name)
        )
        
        # Return compressed context
        return [summary_msg] + recent_messages
    
    async def _create_summary(
        self,
        messages: List[Message],
        model_info: ModelInfo
    ) -> str:
        """Create a summary of messages."""
        if not self.llm_client:
            # Fallback to simple concatenation if no LLM available
            return self._simple_summary(messages)
        
        # Prepare summarization prompt
        conversation_text = "\n".join([
            f"{msg.role}: {msg.content[:500]}..."
            if len(msg.content) > 500 else f"{msg.role}: {msg.content}"
            for msg in messages
        ])
        
        summary_prompt = f"""You are a context summarization AI for a continuous gaming session. 
The following is a conversation history between a player and an AI character. 
Your task is to create a concise summary of the key events, decisions, and established facts.

Retain critical information such as:
- Player's name and goals
- Key quests or objectives
- Important items or information acquired
- Significant relationships or interactions
- Promises or commitments made

Original Conversation:
---
{conversation_text}
---

Provide a concise summary (max 500 words):"""
        
        try:
            # Use LLM to create summary
            response = await self.llm_client.create_completion(
                model=model_info.name,
                messages=[{"role": "user", "content": summary_prompt}],
                max_tokens=600,
                temperature=0.3
            )
            return response.content
        except Exception as e:
            logger.error(f"Error creating LLM summary: {e}")
            return self._simple_summary(messages)
    
    def _simple_summary(self, messages: List[Message]) -> str:
        """Create a simple summary without LLM."""
        # Group by role and summarize
        summary_parts = []
        
        # Get first few and last few messages
        if len(messages) > 6:
            key_messages = messages[:3] + messages[-3:]
        else:
            key_messages = messages
        
        for msg in key_messages:
            if msg.role == "system":
                continue
            summary_parts.append(
                f"{msg.role}: {msg.content[:100]}..."
                if len(msg.content) > 100 else msg.content
            )
        
        return f"Previous conversation ({len(messages)} messages):\n" + "\n".join(summary_parts)


class SlidingWindowStrategy(ContextStrategy):
    """
    Keep only recent messages, dropping older ones.
    Simple but may lose important context.
    """
    
    async def compress_context(
        self,
        messages: List[Message],
        model_info: ModelInfo,
        target_reduction: float = 0.5
    ) -> List[Message]:
        """Keep only recent messages."""
        if not messages:
            return messages
        
        # Calculate messages to keep
        messages_to_keep = max(1, int(len(messages) * (1 - target_reduction)))
        
        # Always keep system messages if present
        system_messages = [msg for msg in messages if msg.role == "system"]
        other_messages = [msg for msg in messages if msg.role != "system"]
        
        # Keep most recent messages
        kept_messages = other_messages[-messages_to_keep:]
        
        # Combine system messages with kept messages
        return system_messages + kept_messages


class HybridStrategy(ContextStrategy):
    """
    Combine summarization and sliding window.
    Summarize very old messages, keep sliding window of recent ones.
    """
    
    def __init__(
        self,
        tokenizer_service: TokenizerService,
        summarization_strategy: SummarizationStrategy,
        window_size: int = 20
    ):
        super().__init__(tokenizer_service)
        self.summarization = summarization_strategy
        self.window_size = window_size
    
    async def compress_context(
        self,
        messages: List[Message],
        model_info: ModelInfo,
        target_reduction: float = 0.5
    ) -> List[Message]:
        """Hybrid compression approach."""
        if len(messages) <= self.window_size:
            # Not enough messages, just summarize if needed
            return await self.summarization.compress_context(
                messages, model_info, target_reduction
            )
        
        # Split into old and recent
        old_messages = messages[:-self.window_size]
        recent_messages = messages[-self.window_size:]
        
        # Summarize old messages
        summarized = await self.summarization.compress_context(
            old_messages,
            model_info,
            target_reduction=0.8  # Aggressive compression for old messages
        )
        
        # Combine with recent messages
        return summarized + recent_messages
