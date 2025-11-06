"""
AI-005: Continuous Batching Configuration
Configures vLLM continuous batching for optimal GPU utilization.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
import os


@dataclass
class BatchingConfig:
    """Configuration for continuous batching."""
    max_batch_size: int = 32
    max_seq_len: int = 2048
    max_num_batched_tokens: int = 8192
    max_num_seqs: int = 256
    enable_chunked_prefill: bool = True
    preemption_mode: str = "recompute"  # "recompute" or "swap"
    gpu_memory_utilization: float = 0.9
    max_model_len: Optional[int] = None
    enable_prefix_caching: bool = True


class ContinuousBatchingManager:
    """
    Manages continuous batching configuration for vLLM.
    Optimizes batch sizes and monitors GPU utilization.
    """
    
    def __init__(self, config: Optional[BatchingConfig] = None):
        self.config = config or BatchingConfig()
        self._gpu_utilization_history: list = []
        self._batch_size_history: list = []
        self._latency_history: list = []
        
    def get_vllm_batch_config(self) -> Dict[str, Any]:
        """
        Get vLLM batch configuration dictionary.
        These parameters are passed to vLLM LLM initialization.
        """
        config_dict = {
            "max_model_len": self.config.max_model_len or self.config.max_seq_len,
            "max_num_batched_tokens": self.config.max_num_batched_tokens,
            "max_num_seqs": self.config.max_num_seqs,
            "enable_chunked_prefill": self.config.enable_chunked_prefill,
            "enable_prefix_caching": self.config.enable_prefix_caching,
        }
        
        # GPU memory utilization
        if self.config.gpu_memory_utilization:
            config_dict["gpu_memory_utilization"] = self.config.gpu_memory_utilization
        
        return config_dict
    
    def get_vllm_serving_config(self) -> Dict[str, Any]:
        """
        Get vLLM serving configuration for API server.
        These parameters control request batching behavior.
        """
        return {
            "max_batch_size": self.config.max_batch_size,
            "max_seq_len": self.config.max_seq_len,
            "preemption_mode": self.config.preemption_mode,
        }
    
    def update_config(
        self,
        max_batch_size: Optional[int] = None,
        max_seq_len: Optional[int] = None,
        max_num_batched_tokens: Optional[int] = None,
        max_num_seqs: Optional[int] = None,
        gpu_memory_utilization: Optional[float] = None,
        enable_chunked_prefill: Optional[bool] = None,
        enable_prefix_caching: Optional[bool] = None
    ):
        """
        Update batching configuration dynamically.
        
        Args:
            max_batch_size: Maximum batch size
            max_seq_len: Maximum sequence length
            max_num_batched_tokens: Maximum batched tokens
            max_num_seqs: Maximum number of sequences
            gpu_memory_utilization: GPU memory utilization (0.0-1.0)
            enable_chunked_prefill: Enable chunked prefill
            enable_prefix_caching: Enable prefix caching
        """
        if max_batch_size is not None:
            self.config.max_batch_size = max_batch_size
        if max_seq_len is not None:
            self.config.max_seq_len = max_seq_len
        if max_num_batched_tokens is not None:
            self.config.max_num_batched_tokens = max_num_batched_tokens
        if max_num_seqs is not None:
            self.config.max_num_seqs = max_num_seqs
        if gpu_memory_utilization is not None:
            self.config.gpu_memory_utilization = max(0.0, min(1.0, gpu_memory_utilization))
        if enable_chunked_prefill is not None:
            self.config.enable_chunked_prefill = enable_chunked_prefill
        if enable_prefix_caching is not None:
            self.config.enable_prefix_caching = enable_prefix_caching
    
    def record_gpu_utilization(self, utilization: float):
        """Record GPU utilization for monitoring."""
        self._gpu_utilization_history.append(utilization)
        if len(self._gpu_utilization_history) > 1000:
            self._gpu_utilization_history = self._gpu_utilization_history[-1000:]
    
    def record_batch_size(self, batch_size: int):
        """Record batch size for monitoring."""
        self._batch_size_history.append(batch_size)
        if len(self._batch_size_history) > 1000:
            self._batch_size_history = self._batch_size_history[-1000:]
    
    def record_latency(self, latency_ms: float):
        """Record latency for monitoring."""
        self._latency_history.append(latency_ms)
        if len(self._latency_history) > 1000:
            self._latency_history = self._latency_history[-1000:]
    
    def get_avg_gpu_utilization(self) -> float:
        """Get average GPU utilization."""
        if not self._gpu_utilization_history:
            return 0.0
        return sum(self._gpu_utilization_history) / len(self._gpu_utilization_history)
    
    def get_avg_batch_size(self) -> float:
        """Get average batch size."""
        if not self._batch_size_history:
            return 0.0
        return sum(self._batch_size_history) / len(self._batch_size_history)
    
    def get_avg_latency(self) -> float:
        """Get average latency."""
        if not self._latency_history:
            return 0.0
        return sum(self._latency_history) / len(self._latency_history)
    
    def optimize_batch_size(self) -> bool:
        """
        Optimize batch size based on GPU utilization and latency.
        Returns True if configuration was updated.
        """
        avg_gpu_util = self.get_avg_gpu_utilization()
        avg_latency = self.get_avg_latency()
        
        # If GPU utilization is low and latency is acceptable, increase batch size
        if avg_gpu_util < 0.7 and avg_latency < 500:
            if self.config.max_batch_size < 64:
                self.config.max_batch_size = min(64, self.config.max_batch_size + 8)
                return True
        
        # If GPU utilization is high and latency is high, decrease batch size
        elif avg_gpu_util > 0.95 and avg_latency > 1000:
            if self.config.max_batch_size > 8:
                self.config.max_batch_size = max(8, self.config.max_batch_size - 4)
                return True
        
        return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get batching metrics."""
        return {
            "config": {
                "max_batch_size": self.config.max_batch_size,
                "max_seq_len": self.config.max_seq_len,
                "max_num_batched_tokens": self.config.max_num_batched_tokens,
                "max_num_seqs": self.config.max_num_seqs,
                "gpu_memory_utilization": self.config.gpu_memory_utilization,
                "enable_chunked_prefill": self.config.enable_chunked_prefill,
                "enable_prefix_caching": self.config.enable_prefix_caching,
            },
            "metrics": {
                "avg_gpu_utilization": self.get_avg_gpu_utilization(),
                "avg_batch_size": self.get_avg_batch_size(),
                "avg_latency_ms": self.get_avg_latency(),
            },
            "history_size": {
                "gpu_utilization": len(self._gpu_utilization_history),
                "batch_size": len(self._batch_size_history),
                "latency": len(self._latency_history),
            }
        }

