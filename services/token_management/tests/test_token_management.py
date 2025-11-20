"""
Comprehensive tests for Token Window Management System.
"""
import pytest
import asyncio
from datetime import datetime
from typing import List, Dict
import json

from services.token_management.models import (
    ModelInfo, TokenWindow, Message, SessionState,
    MODEL_CONFIGS, ModelProvider
)
from services.token_management.tokenizer_service import TokenizerService
from services.token_management.context_strategy import (
    SummarizationStrategy, SlidingWindowStrategy, HybridStrategy
)
from services.token_management.context_engine import ContextEngine
from services.token_management.llm_gateway import LLMGateway


class TestModels:
    """Test model data structures."""
    
    def test_token_window(self):
        """Test TokenWindow calculations."""
        window = TokenWindow(
            input_window=128000,
            max_output_window=4096,
            total_window=128000,
            safety_buffer=256
        )
        
        assert window.effective_input_window == 127744
        assert window.threshold_90_percent == 114969
    
    def test_model_info(self):
        """Test ModelInfo functionality."""
        model = MODEL_CONFIGS["gpt-4o"]
        
        # Test max output calculation
        input_tokens = 100000
        max_output = model.calculate_max_output_tokens(input_tokens)
        assert max_output == 4096  # Limited by max_output_window
        
        # Test with smaller input
        input_tokens = 1000
        max_output = model.calculate_max_output_tokens(input_tokens)
        assert max_output == 4096
    
    def test_message(self):
        """Test Message class."""
        msg = Message(role="user", content="Hello")
        assert msg.to_dict() == {"role": "user", "content": "Hello"}
    
    def test_session_state(self):
        """Test SessionState management."""
        model = MODEL_CONFIGS["gpt-4o"]
        session = SessionState(
            session_id="test_123",
            model_info=model
        )
        
        # Add messages
        session.add_message("user", "Hello", 2)
        session.add_message("assistant", "Hi there", 3)
        
        assert len(session.messages) == 2
        assert session.total_tokens == 5
        
        # Test compression check
        assert not session.needs_compression(100)
        assert session.needs_compression(115000)


class TestTokenizerService:
    """Test tokenizer functionality."""
    
    @pytest.fixture
    def tokenizer(self):
        return TokenizerService()
    
    def test_count_text_tokens(self, tokenizer):
        """Test basic text token counting."""
        text = "Hello, how are you today?"
        count = tokenizer.count_tokens(text, "gpt-4")
        assert count > 0
        assert count < len(text)  # Should be fewer tokens than characters
    
    def test_count_message_tokens(self, tokenizer):
        """Test message token counting."""
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there"}
        ]
        
        count = tokenizer.count_tokens(messages, "gpt-4")
        assert count > 0
        
        # Should include overhead
        text_only = "".join(m["content"] for m in messages)
        text_count = tokenizer.count_tokens(text_only, "gpt-4")
        assert count > text_count
    
    def test_estimate_summary_tokens(self, tokenizer):
        """Test summary token estimation."""
        original = 1000
        estimated = tokenizer.estimate_tokens_for_summary(original)
        assert estimated == 250  # 25% of original
    
    @pytest.mark.asyncio
    async def test_async_counting(self, tokenizer):
        """Test async token counting."""
        text = "Test async counting"
        count = await tokenizer.count_tokens_async(text, "gpt-4")
        sync_count = tokenizer.count_tokens(text, "gpt-4")
        assert count == sync_count


class TestContextStrategies:
    """Test context compression strategies."""
    
    @pytest.fixture
    def tokenizer(self):
        return TokenizerService()
    
    @pytest.fixture
    def messages(self):
        """Create test messages."""
        msgs = []
        for i in range(10):
            msgs.append(Message(
                role="user" if i % 2 == 0 else "assistant",
                content=f"Message {i}: " + "x" * 100,
                token_count=25
            ))
        return msgs
    
    @pytest.mark.asyncio
    async def test_sliding_window_strategy(self, tokenizer, messages):
        """Test sliding window compression."""
        strategy = SlidingWindowStrategy(tokenizer)
        model = MODEL_CONFIGS["gpt-4o"]
        
        compressed = await strategy.compress_context(
            messages, model, target_reduction=0.5
        )
        
        assert len(compressed) <= len(messages) * 0.5 + 1
        # Should keep most recent messages
        assert compressed[-1].content == messages[-1].content
    
    @pytest.mark.asyncio
    async def test_summarization_strategy_simple(self, tokenizer, messages):
        """Test summarization without LLM."""
        strategy = SummarizationStrategy(tokenizer)
        model = MODEL_CONFIGS["gpt-4o"]
        
        compressed = await strategy.compress_context(
            messages, model, target_reduction=0.5
        )
        
        # Should have summary + recent messages
        assert len(compressed) < len(messages)
        assert compressed[0].role == "system"
        assert "summary" in compressed[0].content.lower()


class TestContextEngine:
    """Test the main context engine."""
    
    @pytest.fixture
    def engine(self):
        return ContextEngine()
    
    @pytest.mark.asyncio
    async def test_process_message(self, engine):
        """Test processing a message."""
        session_id = "test_session_1"
        prompt = "Hello, tell me a story"
        
        messages, max_tokens = await engine.process_message(
            session_id, prompt, "gpt-4o"
        )
        
        assert len(messages) == 1
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == prompt
        assert max_tokens > 0
    
    @pytest.mark.asyncio
    async def test_session_management(self, engine):
        """Test session creation and retrieval."""
        session_id = "test_session_2"
        
        # Process first message
        await engine.process_message(session_id, "Hello", "gpt-4o")
        
        # Check session exists
        assert session_id in engine.sessions
        session_info = engine.get_session_info(session_id)
        assert session_info["session_id"] == session_id
        assert session_info["model"] == "gpt-4o"
    
    @pytest.mark.asyncio
    async def test_add_response(self, engine):
        """Test adding responses to session."""
        session_id = "test_session_3"
        
        # Process message
        await engine.process_message(session_id, "Hello", "gpt-4o")
        
        # Add response
        await engine.add_response(
            session_id,
            "Hello",
            "Hi there! How can I help you?",
            prompt_tokens=2,
            response_tokens=8
        )
        
        session = engine.sessions[session_id]
        assert len(session.messages) == 2
        assert session.total_tokens == 10
    
    @pytest.mark.asyncio
    async def test_compression_trigger(self, engine):
        """Test automatic compression when approaching limits."""
        session_id = "test_compression"
        model_name = "gpt-4o"
        
        # Add many messages to approach limit
        session = engine._get_or_create_session(session_id, model_name)
        
        # Simulate high token usage
        for i in range(100):
            session.add_message(
                "user" if i % 2 == 0 else "assistant",
                "x" * 1000,  # Long message
                1000  # High token count
            )
        
        # Process new message that should trigger compression
        initial_count = len(session.messages)
        messages, max_tokens = await engine.process_message(
            session_id, "One more message", model_name
        )
        
        # Should have compressed
        assert engine.metrics["compressions_performed"] > 0
        assert len(session.messages) < initial_count
    
    def test_metrics(self, engine):
        """Test metrics collection."""
        metrics = engine.get_metrics()
        
        assert "active_sessions" in metrics
        assert "total_compressions" in metrics
        assert "tokens_saved" in metrics
        assert "crashes_prevented" in metrics
    
    def test_cleanup_old_sessions(self, engine):
        """Test session cleanup."""
        # Create old session
        old_session = SessionState(
            session_id="old_session",
            model_info=MODEL_CONFIGS["gpt-4o"]
        )
        # Artificially age it
        old_session.last_activity = datetime(2020, 1, 1)
        engine.sessions["old_session"] = old_session
        
        # Create new session
        engine._get_or_create_session("new_session", "gpt-4o")
        
        # Cleanup
        engine.cleanup_old_sessions(max_age_hours=24)
        
        assert "old_session" not in engine.sessions
        assert "new_session" in engine.sessions


class TestIntegration:
    """Integration tests for the full system."""
    
    @pytest.mark.asyncio
    async def test_full_conversation_flow(self):
        """Test a complete conversation with compression."""
        engine = ContextEngine()
        session_id = "integration_test"
        
        # Simulate conversation
        prompts = [
            "Tell me about quantum computing",
            "What are qubits?",
            "How do quantum gates work?",
            "Explain superposition",
            "What is entanglement?",
            "How do quantum algorithms work?",
            "What is Shor's algorithm?",
            "Explain quantum error correction",
            "What are the challenges?",
            "What's the future of quantum computing?"
        ]
        
        for i, prompt in enumerate(prompts):
            # Process message
            messages, max_tokens = await engine.process_message(
                session_id, prompt, "gpt-4o"
            )
            
            # Simulate response
            response = f"Here's information about: {prompt}"
            await engine.add_response(
                session_id,
                prompt,
                response,
                prompt_tokens=len(prompt) * 3,  # Simulate high usage
                response_tokens=len(response) * 10
            )
            
            # Check session state
            session = engine.sessions[session_id]
            print(f"After message {i+1}: {session.total_tokens} tokens, "
                  f"{len(session.messages)} messages")
        
        # Should have triggered compression
        assert engine.metrics["compressions_performed"] > 0
        
        # Session should still be functional
        final_messages, final_max = await engine.process_message(
            session_id, "Summarize our conversation", "gpt-4o"
        )
        assert len(final_messages) > 0
        assert final_max > 0
