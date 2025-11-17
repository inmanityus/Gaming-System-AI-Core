"""
NATS Integration for Guardrails Monitor
========================================

Handles all NATS messaging for the Guardrails service, including:
- Subscribing to policy updates from Settings
- Publishing violation events to Ethelred
- Responding to moderation requests from Model Management
"""

from __future__ import annotations

import asyncio
import json
from typing import Optional, Callable
from uuid import UUID

import nats
from loguru import logger

from .guardrails_monitor import GuardrailsMonitor, ContentModerationRequest


class GuardrailsNATSIntegration:
    """NATS message handling for Guardrails Monitor."""
    
    def __init__(
        self,
        monitor: GuardrailsMonitor,
        service_name: str = "guardrails-monitor"
    ):
        self.monitor = monitor
        self.service_name = service_name
        self.nc: Optional[nats.NATS] = None
    
    async def start(self, nats_url: str) -> None:
        """Start NATS integration."""
        self.nc = await nats.connect(nats_url)
        
        # Subscribe to moderation requests from Model Management
        await self.nc.subscribe(
            "model.content.moderation_request",
            cb=self._handle_moderation_request
        )
        
        # Subscribe to content validation requests from other services
        await self.nc.subscribe(
            "guardrails.validate_content",
            cb=self._handle_validation_request
        )
        
        logger.info(f"{self.service_name} NATS integration started")
    
    async def stop(self) -> None:
        """Stop NATS integration."""
        if self.nc:
            await self.nc.close()
        logger.info(f"{self.service_name} NATS integration stopped")
    
    async def _handle_moderation_request(self, msg: nats.Msg) -> None:
        """
        Handle content moderation request from Model Management.
        
        Request format:
        {
            "session_id": "uuid",
            "player_id": "uuid", 
            "content_type": "text|vision|audio",
            "content": "...",
            "context": {...},
            "model_id": "model-name"
        }
        
        Response format:
        {
            "allowed": true/false,
            "modified_content": "...",
            "violations": [...],
            "applied_filters": [...]
        }
        """
        try:
            # Parse request
            data = json.loads(msg.data.decode())
            request = ContentModerationRequest(
                session_id=UUID(data["session_id"]),
                player_id=UUID(data["player_id"]),
                content_type=data["content_type"],
                content=data["content"],
                context=data.get("context"),
                model_id=data.get("model_id")
            )
            
            # Apply moderation
            response = await self.monitor.moderate_content(request)
            
            # Send response
            if msg.reply:
                await self.nc.publish(
                    msg.reply,
                    json.dumps(response.dict()).encode()
                )
            
            # Track metrics
            if response.allowed:
                logger.debug(
                    f"Content allowed for session {request.session_id} "
                    f"({len(response.applied_filters)} filters applied)"
                )
            else:
                logger.info(
                    f"Content blocked for session {request.session_id}: "
                    f"{len(response.violations)} violations"
                )
            
        except Exception as e:
            logger.error(f"Failed to process moderation request: {e}")
            if msg.reply:
                await self.nc.publish(
                    msg.reply,
                    json.dumps({
                        "error": str(e),
                        "allowed": False
                    }).encode()
                )
    
    async def _handle_validation_request(self, msg: nats.Msg) -> None:
        """
        Handle simple validation request (policy check only).
        
        Request format:
        {
            "session_id": "uuid",
            "categories": ["violence_gore", "language_profanity"],
            "required_levels": {"violence_gore": 2}
        }
        
        Response format:
        {
            "has_policy": true/false,
            "effective_levels": {...},
            "violations": [...]
        }
        """
        try:
            data = json.loads(msg.data.decode())
            session_id = UUID(data["session_id"])
            categories = data.get("categories", [])
            required_levels = data.get("required_levels", {})
            
            # Get policy
            policy = await self.monitor.get_policy_for_session(session_id)
            
            if not policy:
                response = {
                    "has_policy": False,
                    "effective_levels": {},
                    "violations": ["no_policy_found"]
                }
            else:
                # Check required levels
                violations = []
                for category, required in required_levels.items():
                    allowed = policy.effective_levels.get(category, 0)
                    if allowed < required:
                        violations.append({
                            "category": category,
                            "required": required,
                            "allowed": allowed
                        })
                
                response = {
                    "has_policy": True,
                    "effective_levels": {
                        cat: policy.effective_levels.get(cat, 0)
                        for cat in categories
                    },
                    "violations": violations
                }
            
            # Send response
            if msg.reply:
                await self.nc.publish(
                    msg.reply,
                    json.dumps(response).encode()
                )
            
        except Exception as e:
            logger.error(f"Failed to process validation request: {e}")
            if msg.reply:
                await self.nc.publish(
                    msg.reply,
                    json.dumps({"error": str(e)}).encode()
                )

