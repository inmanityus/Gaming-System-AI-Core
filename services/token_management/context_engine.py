"""
Context Engine - Core logic for token window management.
"""
import asyncio
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime

from .models import SessionState, ModelInfo, Message, MODEL_CONFIGS
from .tokenizer_service import TokenizerService
from .context_strategy import (
    ContextStrategy,
    SummarizationStrategy,
    SlidingWindowStrategy,
    HybridStrategy
)


logger = logging.getLogger(__name__)


class ContextEngine:
    """
    Core engine for managing conversation context and token windows.
    Prevents token limit crashes by proactive management.
    """
    
    def __init__(
        self,
        tokenizer_service: Optional[TokenizerService] = None,
        default_strategy: str = "hybrid"
    ):
        self.tokenizer = tokenizer_service or TokenizerService()
        self.sessions: Dict[str, SessionState] = {}
        self.strategies: Dict[str, ContextStrategy] = {}
        self.default_strategy = default_strategy
        
        # Initialize strategies
        self._initialize_strategies()
        
        # Metrics
        self.metrics = {
            "compressions_performed": 0,
            "tokens_saved": 0,
            "sessions_crashed_prevented": 0
        }
    
    def _initialize_strategies(self):
        """Initialize available compression strategies."""
        # Create base strategies
        self.strategies["summarization"] = SummarizationStrategy(self.tokenizer)
        self.strategies["sliding_window"] = SlidingWindowStrategy(self.tokenizer)
        
        # Create hybrid strategy
        self.strategies["hybrid"] = HybridStrategy(
            self.tokenizer,
            self.strategies["summarization"],
            window_size=20
        )
    
    def set_llm_client(self, llm_client):
        """Set LLM client for summarization strategy."""
        if "summarization" in self.strategies:
            self.strategies["summarization"].llm_client = llm_client
    
    async def process_message(
        self,
        session_id: str,
        new_prompt: str,
        model_name: str = "gpt-4o"
    ) -> Tuple[List[Dict[str, str]], int]:
        """
        Process a new message, managing token window.
        
        Args:
            session_id: Unique session identifier
            new_prompt: New user prompt
            model_name: Model being used
            
        Returns:
            Tuple of (messages for API, max_output_tokens)
        """
        # Get or create session
        session = self._get_or_create_session(session_id, model_name)
        
        # Count tokens for new prompt
        new_prompt_tokens = self.tokenizer.count_tokens(new_prompt, model_name)
        
        # Check if compression needed
        if session.needs_compression(new_prompt_tokens):
            logger.info(f"Session {session_id} approaching token limit, compressing context")
            await self._compress_session_context(session)
            self.metrics["compressions_performed"] += 1
        
        # Create new message
        new_message = Message(
            role="user",
            content=new_prompt,
            token_count=new_prompt_tokens
        )
        
        # Calculate final context
        potential_messages = session.messages + [new_message]
        potential_tokens = sum(msg.token_count or 0 for msg in potential_messages)
        
        # Safety check - ensure we're not exceeding limits
        if potential_tokens > session.model_info.token_window.effective_input_window:
            # Emergency compression
            logger.warning(f"Emergency compression needed for session {session_id}")
            await self._emergency_compress(session, new_prompt_tokens)
            self.metrics["sessions_crashed_prevented"] += 1
        
        # Add message to session (not persisted until response received)
        final_messages = session.get_messages_for_api() + [new_message.to_dict()]
        
        # Calculate max output tokens
        current_tokens = self.tokenizer.count_tokens(final_messages, model_name)
        max_output_tokens = session.model_info.calculate_max_output_tokens(current_tokens)
        
        logger.debug(
            f"Session {session_id}: {current_tokens} input tokens, "
            f"{max_output_tokens} max output tokens allowed"
        )
        
        return final_messages, max_output_tokens
    
    async def add_response(
        self,
        session_id: str,
        prompt: str,
        response: str,
        prompt_tokens: Optional[int] = None,
        response_tokens: Optional[int] = None
    ):
        """Add a completed exchange to the session."""
        session = self.sessions.get(session_id)
        if not session:
            logger.error(f"Session {session_id} not found")
            return
        
        # Add user message
        if prompt_tokens is None:
            prompt_tokens = self.tokenizer.count_tokens(prompt, session.model_info.name)
        session.add_message("user", prompt, prompt_tokens)
        
        # Add assistant response
        if response_tokens is None:
            response_tokens = self.tokenizer.count_tokens(response, session.model_info.name)
        session.add_message("assistant", response, response_tokens)
        
        logger.info(
            f"Session {session_id}: Total tokens now {session.total_tokens} "
            f"({session.total_tokens / session.model_info.token_window.total_window * 100:.1f}% of limit)"
        )
    
    def _get_or_create_session(self, session_id: str, model_name: str) -> SessionState:
        """Get existing session or create new one."""
        if session_id not in self.sessions:
            model_info = MODEL_CONFIGS.get(model_name)
            if not model_info:
                # Create default model info
                logger.warning(f"Unknown model {model_name}, using default configuration")
                from .models import TokenWindow, ModelProvider
                model_info = ModelInfo(
                    name=model_name,
                    provider=ModelProvider.CUSTOM,
                    version="unknown",
                    token_window=TokenWindow(
                        input_window=8192,
                        max_output_window=4096,
                        total_window=8192
                    )
                )
            
            self.sessions[session_id] = SessionState(
                session_id=session_id,
                model_info=model_info
            )
            logger.info(f"Created new session {session_id} for model {model_name}")
        
        return self.sessions[session_id]
    
    async def _compress_session_context(self, session: SessionState):
        """Compress session context using configured strategy."""
        strategy = self.strategies.get(self.default_strategy)
        if not strategy:
            logger.error(f"Unknown strategy {self.default_strategy}")
            return
        
        original_tokens = session.total_tokens
        
        # Compress messages
        compressed_messages = await strategy.compress_context(
            session.messages,
            session.model_info,
            target_reduction=0.5
        )
        
        # Update session
        session.messages = compressed_messages
        session.compression_count += 1
        
        # Recalculate tokens
        new_total = sum(msg.token_count or 0 for msg in compressed_messages)
        session.total_tokens = new_total
        
        tokens_saved = original_tokens - new_total
        self.metrics["tokens_saved"] += tokens_saved
        
        logger.info(
            f"Compressed session {session.session_id}: "
            f"{original_tokens} -> {new_total} tokens (saved {tokens_saved})"
        )
    
    async def _emergency_compress(self, session: SessionState, new_tokens: int):
        """Emergency compression when about to exceed limits."""
        # Use more aggressive compression
        strategy = self.strategies.get("sliding_window")
        if not strategy:
            strategy = self.strategies[self.default_strategy]
        
        # Keep only essential recent context
        required_reduction = 0.7  # Remove 70% of content
        
        compressed_messages = await strategy.compress_context(
            session.messages,
            session.model_info,
            target_reduction=required_reduction
        )
        
        session.messages = compressed_messages
        session.compression_count += 1
        session.total_tokens = sum(msg.token_count or 0 for msg in compressed_messages)
        
        logger.warning(
            f"Emergency compression for session {session.session_id}: "
            f"Kept {len(compressed_messages)} messages, {session.total_tokens} tokens"
        )
    
    def get_session_info(self, session_id: str) -> Optional[Dict]:
        """Get information about a session."""
        session = self.sessions.get(session_id)
        if not session:
            return None
        
        return {
            "session_id": session_id,
            "model": session.model_info.name,
            "message_count": len(session.messages),
            "total_tokens": session.total_tokens,
            "token_percentage": session.total_tokens / session.model_info.token_window.total_window * 100,
            "compression_count": session.compression_count,
            "created_at": session.created_at.isoformat(),
            "last_activity": session.last_activity.isoformat()
        }
    
    def get_metrics(self) -> Dict:
        """Get engine metrics."""
        return {
            "active_sessions": len(self.sessions),
            "total_compressions": self.metrics["compressions_performed"],
            "tokens_saved": self.metrics["tokens_saved"],
            "crashes_prevented": self.metrics["sessions_crashed_prevented"],
            "sessions": [
                self.get_session_info(sid)
                for sid in self.sessions
            ]
        }
    
    def cleanup_old_sessions(self, max_age_hours: int = 24):
        """Clean up old inactive sessions."""
        cutoff = datetime.utcnow()
        removed = 0
        
        for session_id in list(self.sessions.keys()):
            session = self.sessions[session_id]
            age_hours = (cutoff - session.last_activity).total_seconds() / 3600
            
            if age_hours > max_age_hours:
                del self.sessions[session_id]
                removed += 1
        
        if removed:
            logger.info(f"Cleaned up {removed} old sessions")
