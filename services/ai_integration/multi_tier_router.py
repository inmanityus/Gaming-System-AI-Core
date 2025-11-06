"""
AI-004: Multi-Tier Model Serving System
Routes requests to appropriate model tiers based on task responsibilities.
Integrates with Dynamic Model Selection System for cost-benefit analysis.
"""

from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass
import time
import asyncio

from .vllm_client import VLLMClient
from .lora_manager import LoRAManager


class ModelTier(Enum):
    """Model tier enumeration."""
    TIER_1 = "tier_1"  # Small models (Phi-3-mini) - Generic NPCs
    TIER_2 = "tier_2"  # Mid-size + LoRA (Llama-3.1-8B) - Elite NPCs
    TIER_3 = "tier_3"  # Mid-size + personalized LoRA - Major NPCs


@dataclass
class TierConfiguration:
    """Configuration for a model tier."""
    tier: ModelTier
    model_name: str
    base_url: Optional[str] = None
    lora_adapter: Optional[str] = None
    max_tokens: int = 512
    temperature: float = 0.7
    latency_target_ms: int = 500  # Target latency in milliseconds
    concurrency_limit: int = 10  # Max concurrent requests


@dataclass
class TierMetrics:
    """Metrics for a model tier."""
    tier: ModelTier
    request_count: int = 0
    success_count: int = 0
    error_count: int = 0
    total_latency_ms: float = 0.0
    avg_latency_ms: float = 0.0
    p50_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    active_requests: int = 0


class MultiTierModelRouter:
    """
    Routes requests to appropriate model tiers based on task responsibilities.
    Integrates with Dynamic Model Selection System for cost-benefit analysis.
    """
    
    def __init__(
        self,
        vllm_client: Optional[VLLMClient] = None,
        lora_manager: Optional[LoRAManager] = None
    ):
        self.vllm_client = vllm_client or VLLMClient()
        self.lora_manager = lora_manager or LoRAManager()
        
        # Tier configurations
        self.tier_configs: Dict[ModelTier, TierConfiguration] = {
            ModelTier.TIER_1: TierConfiguration(
                tier=ModelTier.TIER_1,
                model_name="phi3:mini",
                max_tokens=256,
                temperature=0.7,
                latency_target_ms=150,
                concurrency_limit=20
            ),
            ModelTier.TIER_2: TierConfiguration(
                tier=ModelTier.TIER_2,
                model_name="llama3.1:8b",
                max_tokens=512,
                temperature=0.7,
                latency_target_ms=300,
                concurrency_limit=10
            ),
            ModelTier.TIER_3: TierConfiguration(
                tier=ModelTier.TIER_3,
                model_name="llama3.1:8b",
                max_tokens=512,
                temperature=0.7,
                latency_target_ms=500,
                concurrency_limit=5
            ),
        }
        
        # Tier metrics
        self.tier_metrics: Dict[ModelTier, TierMetrics] = {
            tier: TierMetrics(tier=tier)
            for tier in ModelTier
        }
        
        # Latency history for percentile calculations
        self.latency_history: Dict[ModelTier, List[float]] = {
            tier: [] for tier in ModelTier
        }
        
        # Concurrency tracking
        self.active_requests: Dict[ModelTier, int] = {
            tier: 0 for tier in ModelTier
        }
        
        # Task responsibility mapping
        self.task_responsibility_map: Dict[str, ModelTier] = {
            # Tier 1: Generic NPCs, simple responses
            "generic_npc_dialogue": ModelTier.TIER_1,
            "simple_question": ModelTier.TIER_1,
            "greeting": ModelTier.TIER_1,
            "farewell": ModelTier.TIER_1,
            
            # Tier 2: Elite NPCs, complex interactions
            "elite_npc_dialogue": ModelTier.TIER_2,
            "complex_question": ModelTier.TIER_2,
            "quest_dialogue": ModelTier.TIER_2,
            "story_progression": ModelTier.TIER_2,
            
            # Tier 3: Major NPCs, personalized interactions
            "major_npc_dialogue": ModelTier.TIER_3,
            "personalized_response": ModelTier.TIER_3,
            "character_development": ModelTier.TIER_3,
            "story_critical": ModelTier.TIER_3,
        }
    
    def _determine_tier_from_context(self, context: Dict[str, Any]) -> ModelTier:
        """
        Determine model tier from request context.
        Uses task responsibilities, not arbitrary selection.
        
        Args:
            context: Request context with task information
        
        Returns:
            Appropriate model tier
        """
        # Check for explicit tier in context
        if "tier" in context:
            tier_str = str(context["tier"]).lower()
            if tier_str == "1" or tier_str == "tier_1":
                return ModelTier.TIER_1
            elif tier_str == "2" or tier_str == "tier_2":
                return ModelTier.TIER_2
            elif tier_str == "3" or tier_str == "tier_3":
                return ModelTier.TIER_3
        
        # Check for task type/responsibility
        task_type = context.get("task_type") or context.get("responsibility")
        if task_type and task_type in self.task_responsibility_map:
            return self.task_responsibility_map[task_type]
        
        # Check for NPC tier/type
        npc_tier = context.get("npc_tier") or context.get("npc_type")
        if npc_tier:
            npc_tier_str = str(npc_tier).lower()
            if "generic" in npc_tier_str or "tier_1" in npc_tier_str:
                return ModelTier.TIER_1
            elif "elite" in npc_tier_str or "tier_2" in npc_tier_str:
                return ModelTier.TIER_2
            elif "major" in npc_tier_str or "tier_3" in npc_tier_str:
                return ModelTier.TIER_3
        
        # Default to Tier 2 (balanced)
        return ModelTier.TIER_2
    
    def _check_concurrency_limit(self, tier: ModelTier) -> bool:
        """Check if tier can accept more requests."""
        config = self.tier_configs[tier]
        return self.active_requests[tier] < config.concurrency_limit
    
    async def route_request(
        self,
        prompt: str,
        context: Dict[str, Any],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Route request to appropriate model tier.
        
        Args:
            prompt: Input prompt
            context: Request context with task information
            max_tokens: Maximum tokens (overrides tier default)
            temperature: Sampling temperature (overrides tier default)
        
        Returns:
            Generation result with tier information
        """
        # Determine tier from context
        tier = self._determine_tier_from_context(context)
        
        # Check concurrency limit
        if not self._check_concurrency_limit(tier):
            # Fallback to lower tier if available
            if tier == ModelTier.TIER_3:
                tier = ModelTier.TIER_2
            elif tier == ModelTier.TIER_2:
                tier = ModelTier.TIER_1
            
            # If still at limit, wait or reject
            if not self._check_concurrency_limit(tier):
                return {
                    "success": False,
                    "error": f"Tier {tier.value} at concurrency limit",
                    "tier": tier.value
                }
        
        # Get tier configuration
        config = self.tier_configs[tier]
        
        # Update active requests
        self.active_requests[tier] += 1
        metrics = self.tier_metrics[tier]
        metrics.active_requests = self.active_requests[tier]
        metrics.request_count += 1
        
        start_time = time.time()
        
        try:
            # Prepare generation parameters
            gen_max_tokens = max_tokens or config.max_tokens
            gen_temperature = temperature if temperature is not None else config.temperature
            
            # Generate with appropriate model and LoRA adapter
            result = await self.vllm_client.generate(
                model=config.model_name,
                prompt=prompt,
                max_tokens=gen_max_tokens,
                temperature=gen_temperature,
                lora_request=config.lora_adapter
            )
            
            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            
            # Update metrics
            metrics.success_count += 1
            metrics.total_latency_ms += latency_ms
            metrics.avg_latency_ms = metrics.total_latency_ms / metrics.success_count
            
            # Update latency history for percentile calculations
            self.latency_history[tier].append(latency_ms)
            if len(self.latency_history[tier]) > 1000:
                self.latency_history[tier] = self.latency_history[tier][-1000:]
            
            # Calculate percentiles
            if len(self.latency_history[tier]) > 0:
                sorted_latencies = sorted(self.latency_history[tier])
                metrics.p50_latency_ms = sorted_latencies[int(len(sorted_latencies) * 0.5)]
                metrics.p95_latency_ms = sorted_latencies[int(len(sorted_latencies) * 0.95)]
                metrics.p99_latency_ms = sorted_latencies[int(len(sorted_latencies) * 0.99)]
            
            # Extract generated text
            generated_text = ""
            if not result.get("error"):
                choices = result.get("choices", [])
                if choices:
                    generated_text = choices[0].get("text", "")
                    if not generated_text:
                        message = choices[0].get("message", {})
                        generated_text = message.get("content", "")
            
            return {
                "success": True,
                "text": generated_text,
                "tier": tier.value,
                "model": config.model_name,
                "lora_adapter": config.lora_adapter,
                "latency_ms": latency_ms,
                "tokens_used": result.get("usage", {}).get("completion_tokens", 0),
            }
            
        except Exception as e:
            # Update error metrics
            metrics.error_count += 1
            latency_ms = (time.time() - start_time) * 1000
            
            return {
                "success": False,
                "error": str(e),
                "tier": tier.value,
                "latency_ms": latency_ms,
            }
            
        finally:
            # Decrement active requests
            self.active_requests[tier] = max(0, self.active_requests[tier] - 1)
            metrics.active_requests = self.active_requests[tier]
    
    def get_tier_metrics(self, tier: Optional[ModelTier] = None) -> Dict[str, Any]:
        """
        Get metrics for a specific tier or all tiers.
        
        Args:
            tier: Specific tier to get metrics for, or None for all tiers
        
        Returns:
            Metrics dictionary
        """
        if tier:
            metrics = self.tier_metrics[tier]
            config = self.tier_configs[tier]
            return {
                "tier": tier.value,
                "model": config.model_name,
                "request_count": metrics.request_count,
                "success_count": metrics.success_count,
                "error_count": metrics.error_count,
                "success_rate": metrics.success_count / max(metrics.request_count, 1),
                "avg_latency_ms": metrics.avg_latency_ms,
                "p50_latency_ms": metrics.p50_latency_ms,
                "p95_latency_ms": metrics.p95_latency_ms,
                "p99_latency_ms": metrics.p99_latency_ms,
                "active_requests": metrics.active_requests,
                "concurrency_limit": config.concurrency_limit,
                "latency_target_ms": config.latency_target_ms,
            }
        else:
            return {
                tier.value: self.get_tier_metrics(tier)
                for tier in ModelTier
            }
    
    def configure_tier(
        self,
        tier: ModelTier,
        model_name: Optional[str] = None,
        lora_adapter: Optional[str] = None,
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        latency_target_ms: Optional[int] = None,
        concurrency_limit: Optional[int] = None
    ):
        """
        Configure a model tier.
        
        Args:
            tier: Model tier to configure
            model_name: Model name (optional)
            lora_adapter: LoRA adapter name (optional)
            max_tokens: Max tokens (optional)
            temperature: Temperature (optional)
            latency_target_ms: Latency target (optional)
            concurrency_limit: Concurrency limit (optional)
        """
        config = self.tier_configs[tier]
        
        if model_name:
            config.model_name = model_name
        if lora_adapter:
            config.lora_adapter = lora_adapter
        if max_tokens:
            config.max_tokens = max_tokens
        if temperature is not None:
            config.temperature = temperature
        if latency_target_ms:
            config.latency_target_ms = latency_target_ms
        if concurrency_limit:
            config.concurrency_limit = concurrency_limit

