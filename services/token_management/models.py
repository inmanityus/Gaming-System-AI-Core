"""
Data models for token window management system.
"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum


class ModelProvider(str, Enum):
    """Supported model providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    META = "meta"
    CUSTOM = "custom"


@dataclass
class TokenWindow:
    """Token window information for a model."""
    input_window: int
    max_output_window: int
    total_window: int
    safety_buffer: int = 256
    
    @property
    def effective_input_window(self) -> int:
        """Get effective input window after safety buffer."""
        return self.input_window - self.safety_buffer
    
    @property
    def threshold_90_percent(self) -> int:
        """Get 90% threshold for input window."""
        return int(self.effective_input_window * 0.9)


@dataclass
class ModelInfo:
    """Complete information about an AI model."""
    name: str
    provider: ModelProvider
    version: str
    token_window: TokenWindow
    supports_streaming: bool = True
    supports_functions: bool = True
    supports_vision: bool = False
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0
    
    def calculate_max_output_tokens(self, input_tokens: int) -> int:
        """Calculate maximum output tokens given input size."""
        available_tokens = self.token_window.total_window - input_tokens - self.token_window.safety_buffer
        return min(available_tokens, self.token_window.max_output_window)


# Predefined model configurations
MODEL_CONFIGS = {
    # OpenAI Models
    "gpt-4o": ModelInfo(
        name="gpt-4o",
        provider=ModelProvider.OPENAI,
        version="2024-11",
        token_window=TokenWindow(
            input_window=128000,
            max_output_window=4096,
            total_window=128000
        ),
        supports_vision=True,
        cost_per_1k_input=2.50,
        cost_per_1k_output=10.00
    ),
    "gpt-5.1": ModelInfo(  # Speculative
        name="gpt-5.1",
        provider=ModelProvider.OPENAI,
        version="2025-01",
        token_window=TokenWindow(
            input_window=256000,
            max_output_window=16384,
            total_window=256000
        ),
        supports_vision=True,
        cost_per_1k_input=5.00,
        cost_per_1k_output=20.00
    ),
    
    # Anthropic Models
    "claude-3.5-sonnet": ModelInfo(
        name="claude-3.5-sonnet",
        provider=ModelProvider.ANTHROPIC,
        version="20241022",
        token_window=TokenWindow(
            input_window=200000,
            max_output_window=8192,
            total_window=200000
        ),
        cost_per_1k_input=3.00,
        cost_per_1k_output=15.00
    ),
    "claude-4.5": ModelInfo(  # Speculative
        name="claude-4.5",
        provider=ModelProvider.ANTHROPIC,
        version="2025-01",
        token_window=TokenWindow(
            input_window=400000,
            max_output_window=16384,
            total_window=400000
        ),
        cost_per_1k_input=4.00,
        cost_per_1k_output=18.00
    ),
    
    # Google Models
    "gemini-1.5-pro": ModelInfo(
        name="gemini-1.5-pro",
        provider=ModelProvider.GOOGLE,
        version="001",
        token_window=TokenWindow(
            input_window=1000000,
            max_output_window=8192,
            total_window=1000000
        ),
        supports_vision=True,
        cost_per_1k_input=3.50,
        cost_per_1k_output=10.50
    ),
    "gemini-2.5-pro": ModelInfo(  # Speculative
        name="gemini-2.5-pro",
        provider=ModelProvider.GOOGLE,
        version="001",
        token_window=TokenWindow(
            input_window=2000000,
            max_output_window=16384,
            total_window=2000000
        ),
        supports_vision=True,
        cost_per_1k_input=2.50,
        cost_per_1k_output=8.00
    ),
}


@dataclass
class Message:
    """A single message in a conversation."""
    role: str  # "system", "user", "assistant"
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    token_count: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to API format."""
        return {"role": self.role, "content": self.content}


@dataclass
class SessionState:
    """State of a conversation session."""
    session_id: str
    model_info: ModelInfo
    messages: List[Message] = field(default_factory=list)
    total_tokens: int = 0
    compression_count: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_message(self, role: str, content: str, token_count: int):
        """Add a message and update token count."""
        msg = Message(role=role, content=content, token_count=token_count)
        self.messages.append(msg)
        self.total_tokens += token_count
        self.last_activity = datetime.utcnow()
        
    def get_messages_for_api(self) -> List[Dict[str, str]]:
        """Get messages in API format."""
        return [msg.to_dict() for msg in self.messages]
    
    def needs_compression(self, new_tokens: int) -> bool:
        """Check if compression is needed for new tokens."""
        potential_total = self.total_tokens + new_tokens
        return potential_total > self.model_info.token_window.threshold_90_percent
