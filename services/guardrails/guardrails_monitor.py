"""
Guardrails Monitor
==================

Core service that applies content moderation and safety filters based on
player-specific content policies. Integrates with Model Management to
influence AI behavior in real-time.
"""

from __future__ import annotations

import asyncio
from typing import Dict, List, Optional, Any
from uuid import UUID

import nats
from loguru import logger
from pydantic import BaseModel

from services.settings.content_schemas import SessionContentPolicySnapshot
from .policy_cache import PolicyCache


class ContentModerationRequest(BaseModel):
    """Request to moderate content before/after model generation."""
    session_id: UUID
    player_id: UUID
    content_type: str  # "text", "vision", "audio", "fused"
    content: str  # The actual content to moderate
    context: Optional[Dict[str, Any]] = None
    model_id: Optional[str] = None  # Which model is generating/processing


class ContentModerationResponse(BaseModel):
    """Response from content moderation."""
    allowed: bool
    modified_content: Optional[str] = None  # If content was filtered/modified
    violations: List[Dict[str, Any]] = []
    applied_filters: List[str] = []


class GuardrailsMonitor:
    """
    Main Guardrails service that:
    1. Subscribes to policy updates from Settings
    2. Maintains policy cache for fast lookups
    3. Provides content moderation API for Model Management
    4. Reports violations to Ethelred Coordinator
    """
    
    def __init__(
        self,
        nats_url: str,
        redis_url: str,
        service_name: str = "guardrails-monitor",
    ):
        self.nats_url = nats_url
        self.redis_url = redis_url
        self.service_name = service_name
        
        self.nc: Optional[nats.NATS] = None
        self.policy_cache = PolicyCache(redis_url)
        
        # Filter implementations (stubs for now)
        self._filters: Dict[str, Any] = {}
    
    async def start(self) -> None:
        """Start the Guardrails Monitor."""
        # Connect to dependencies
        self.nc = await nats.connect(self.nats_url)
        await self.policy_cache.connect()
        
        # Subscribe to policy updates
        await self.nc.subscribe(
            "settings.content_policy.session_started",
            cb=self._handle_session_policy
        )
        
        await self.nc.subscribe(
            "settings.content_policy.session_ended", 
            cb=self._handle_session_ended
        )
        
        logger.info(f"{self.service_name} started and subscribed to policy events")
    
    async def stop(self) -> None:
        """Stop the service gracefully."""
        if self.nc:
            await self.nc.close()
        await self.policy_cache.close()
        logger.info(f"{self.service_name} stopped")
    
    async def _handle_session_policy(self, msg: nats.Msg) -> None:
        """Handle new session policy snapshot."""
        try:
            import json
            data = json.loads(msg.data.decode())
            
            # Extract policy from event
            policy_data = data.get("policy_snapshot")
            if not policy_data:
                logger.warning("Received session_started without policy_snapshot")
                return
            
            policy = SessionContentPolicySnapshot(**policy_data)
            
            # Cache for fast lookup
            await self.policy_cache.set_policy(policy.session_id, policy)
            
            logger.info(
                f"Cached policy for session {policy.session_id} "
                f"(player: {policy.player_id}, version: {policy.policy_version})"
            )
            
        except Exception as e:
            logger.error(f"Failed to process session policy: {e}")
    
    async def _handle_session_ended(self, msg: nats.Msg) -> None:
        """Handle session end - cleanup policy."""
        try:
            import json
            data = json.loads(msg.data.decode())
            session_id = UUID(data["session_id"])
            
            await self.policy_cache.invalidate(session_id)
            logger.info(f"Cleared policy cache for ended session {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to process session end: {e}")
    
    async def moderate_content(
        self,
        request: ContentModerationRequest
    ) -> ContentModerationResponse:
        """
        Apply content moderation based on session policy.
        
        This is called by Model Management before/after generation.
        """
        # Get policy from cache
        policy = await self.policy_cache.get_policy(request.session_id)
        if not policy:
            # No policy = most restrictive by default
            logger.warning(f"No policy found for session {request.session_id}, applying defaults")
            return ContentModerationResponse(
                allowed=False,
                violations=[{
                    "reason": "no_policy",
                    "session_id": str(request.session_id)
                }]
            )
        
        # Apply filters based on content type and policy
        violations = []
        modified_content = request.content
        applied_filters = []
        
        # Simple keyword filter for text (placeholder for ML models)
        if request.content_type == "text":
            result = await self._apply_text_filters(
                modified_content,
                policy,
                request.context
            )
            modified_content = result["content"]
            violations.extend(result["violations"])
            applied_filters.extend(result["filters"])
        
        # Determine if content is allowed
        allowed = len(violations) == 0
        
        # Log significant violations
        if not allowed:
            logger.warning(
                f"Content blocked for session {request.session_id}: "
                f"{len(violations)} violations"
            )
            
            # Publish violation event for Ethelred Coordinator
            if self.nc:
                await self.nc.publish(
                    "ethelred.content.violation_detected",
                    json.dumps({
                        "session_id": str(request.session_id),
                        "player_id": str(request.player_id),
                        "content_type": request.content_type,
                        "violations": violations,
                        "model_id": request.model_id,
                    }).encode()
                )
        
        return ContentModerationResponse(
            allowed=allowed,
            modified_content=modified_content if allowed else None,
            violations=violations,
            applied_filters=applied_filters,
        )
    
    async def _apply_text_filters(
        self,
        content: str,
        policy: SessionContentPolicySnapshot,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Apply text content filters based on policy.
        
        This is a simplified implementation that demonstrates the
        integration pattern. Real implementation would use ML models.
        """
        violations = []
        filters_applied = []
        modified = content
        
        # Get allowed levels from policy
        profanity_level = policy.effective_levels.get("language_profanity", 0)
        violence_level = policy.effective_levels.get("violence_gore", 0)
        
        # Simple profanity filter (would be ML model in production)
        if profanity_level < 3:
            # Basic word replacement
            profanity_words = ["fuck", "shit", "damn"]
            for word in profanity_words:
                if word in modified.lower():
                    if profanity_level == 0:
                        # Completely block
                        violations.append({
                            "category": "language_profanity",
                            "severity": "high",
                            "detail": f"Profanity detected: {word}"
                        })
                    else:
                        # Mask the word
                        modified = modified.replace(word, "*" * len(word))
                        filters_applied.append("profanity_mask")
        
        # Violence content filter
        if violence_level < 2:
            violence_keywords = ["blood", "gore", "mutilate", "dismember"]
            for keyword in violence_keywords:
                if keyword in modified.lower():
                    violations.append({
                        "category": "violence_gore",
                        "severity": "medium",
                        "detail": f"Violence keyword: {keyword}"
                    })
        
        return {
            "content": modified,
            "violations": violations,
            "filters": filters_applied,
        }
    
    async def get_policy_for_session(
        self,
        session_id: UUID
    ) -> Optional[SessionContentPolicySnapshot]:
        """Get cached policy for a session (used by other services)."""
        return await self.policy_cache.get_policy(session_id)

