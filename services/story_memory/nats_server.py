"""
Story Memory NATS Server
"""
import asyncio
import json
import os
import signal
import sys
from datetime import datetime
from typing import Optional
from uuid import UUID

import asyncpg
from loguru import logger
from nats.aio.client import Client as NATS

# Import SDK components
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from sdk.nats_client import get_nats_client
from sdk.health_endpoint import HealthEndpoint

from services.story_memory.story_state_manager import StoryStateManager
from services.story_memory.drift_detector import DriftDetector
from services.story_memory.event_ingestor import EventIngestor
from services.story_memory.story_schemas import (
    StorySnapshot, DriftMetrics, ArcRole, ProgressState
)


class StoryMemoryNATSService:
    """NATS-based Story Memory service."""
    
    def __init__(self):
        self.nc: Optional[NATS] = None
        self.postgres_pool: Optional[asyncpg.Pool] = None
        self.story_manager: Optional[StoryStateManager] = None
        self.drift_detector: Optional[DriftDetector] = None
        self.event_ingestor: Optional[EventIngestor] = None
        self.health_endpoint: Optional[HealthEndpoint] = None
        self._running = True
        
    async def start(self):
        """Start the service."""
        try:
            # Create PostgreSQL pool
            self.postgres_pool = await asyncpg.create_pool(
                host=os.getenv('DB_HOST', 'localhost'),
                port=int(os.getenv('DB_PORT', 5432)),
                database=os.getenv('DB_NAME', 'gaming_system'),
                user=os.getenv('DB_USER', 'postgres'),
                password=os.getenv('DB_PASSWORD'),
                min_size=5,
                max_size=20
            )
            logger.info("PostgreSQL pool created")
            
            # Connect to NATS
            self.nc = await get_nats_client()
            logger.info("Connected to NATS")
            
            # Initialize components
            self.story_manager = StoryStateManager(self.postgres_pool)
            self.drift_detector = DriftDetector(self.nc, self.story_manager, self.postgres_pool)
            self.event_ingestor = EventIngestor(self.nc, self.story_manager, self.postgres_pool)
            
            # Start health endpoint
            self.health_endpoint = HealthEndpoint(port=8099)
            await self.health_endpoint.start()
            
            # Subscribe to NATS subjects
            await self._setup_subscriptions()
            
            # Start background tasks
            await self.event_ingestor.start()
            await self.drift_detector.start()
            
            logger.info("Story Memory NATS Service started successfully")
            
            # Keep running
            while self._running:
                await asyncio.sleep(1)
                
        except Exception as e:
            logger.error(f"Failed to start service: {e}")
            raise
        finally:
            await self.stop()
    
    async def stop(self):
        """Stop the service."""
        logger.info("Stopping Story Memory NATS Service")
        self._running = False
        
        if self.health_endpoint:
            await self.health_endpoint.stop()
            
        if self.nc:
            await self.nc.close()
            
        if self.postgres_pool:
            await self.postgres_pool.close()
            
        logger.info("Story Memory NATS Service stopped")
    
    async def _setup_subscriptions(self):
        """Set up NATS subscriptions."""
        # Story snapshot requests
        await self.nc.subscribe("story.get.snapshot", self._handle_get_snapshot)
        await self.nc.subscribe("story.get.arc_progress", self._handle_get_arc_progress)
        await self.nc.subscribe("story.get.relationships", self._handle_get_relationships)
        await self.nc.subscribe("story.get.dark_world_standings", self._handle_get_standings)
        
        # Drift check requests
        await self.nc.subscribe("story.check.drift", self._handle_check_drift)
        
        # Updates (in addition to event ingestor subscriptions)
        await self.nc.subscribe("story.update.arc_progress", self._handle_update_arc_progress)
        await self.nc.subscribe("story.update.relationship", self._handle_update_relationship)
        await self.nc.subscribe("story.update.dark_world_standing", self._handle_update_standing)
        
        logger.info("NATS subscriptions established")
    
    async def _handle_get_snapshot(self, msg):
        """Handle story snapshot requests."""
        try:
            data = json.loads(msg.data.decode())
            player_id = UUID(data['player_id'])
            
            snapshot = await self.story_manager.get_story_snapshot(player_id)
            
            # Convert to dict for JSON serialization
            response = {
                'success': True,
                'snapshot': snapshot.dict()
            }
            
            await self.nc.publish(msg.reply, json.dumps(response).encode())
            
        except Exception as e:
            logger.error(f"Error handling get snapshot: {e}")
            error_response = {
                'success': False,
                'error': str(e)
            }
            await self.nc.publish(msg.reply, json.dumps(error_response).encode())
    
    async def _handle_get_arc_progress(self, msg):
        """Handle arc progress requests."""
        try:
            data = json.loads(msg.data.decode())
            player_id = UUID(data['player_id'])
            arc_id = data.get('arc_id')
            
            snapshot = await self.story_manager.get_story_snapshot(player_id)
            
            if arc_id:
                # Find specific arc
                progress = None
                for arc in snapshot.arc_progress:
                    if arc.arc_id == arc_id:
                        progress = arc
                        break
                        
                if not progress:
                    raise ValueError(f"Arc {arc_id} not found")
                    
                response = {
                    'success': True,
                    'arc_progress': progress.dict()
                }
            else:
                # Return all arcs
                response = {
                    'success': True,
                    'arc_progress': [arc.dict() for arc in snapshot.arc_progress]
                }
            
            await self.nc.publish(msg.reply, json.dumps(response).encode())
            
        except Exception as e:
            logger.error(f"Error handling get arc progress: {e}")
            error_response = {
                'success': False,
                'error': str(e)
            }
            await self.nc.publish(msg.reply, json.dumps(error_response).encode())
    
    async def _handle_get_relationships(self, msg):
        """Handle relationship requests."""
        try:
            data = json.loads(msg.data.decode())
            player_id = UUID(data['player_id'])
            entity_id = data.get('entity_id')
            
            snapshot = await self.story_manager.get_story_snapshot(player_id)
            
            if entity_id:
                # Find specific relationship
                relationship = None
                for rel in snapshot.relationships:
                    if rel.entity_id == entity_id:
                        relationship = rel
                        break
                        
                if not relationship:
                    raise ValueError(f"No relationship found with {entity_id}")
                    
                response = {
                    'success': True,
                    'relationship': relationship.dict()
                }
            else:
                # Return all relationships
                response = {
                    'success': True,
                    'relationships': [rel.dict() for rel in snapshot.relationships]
                }
            
            await self.nc.publish(msg.reply, json.dumps(response).encode())
            
        except Exception as e:
            logger.error(f"Error handling get relationships: {e}")
            error_response = {
                'success': False,
                'error': str(e)
            }
            await self.nc.publish(msg.reply, json.dumps(error_response).encode())
    
    async def _handle_get_standings(self, msg):
        """Handle Dark World standings requests."""
        try:
            data = json.loads(msg.data.decode())
            player_id = UUID(data['player_id'])
            
            snapshot = await self.story_manager.get_story_snapshot(player_id)
            
            response = {
                'success': True,
                'standings': [standing.dict() for standing in snapshot.dark_world_standings]
            }
            
            await self.nc.publish(msg.reply, json.dumps(response).encode())
            
        except Exception as e:
            logger.error(f"Error handling get standings: {e}")
            error_response = {
                'success': False,
                'error': str(e)
            }
            await self.nc.publish(msg.reply, json.dumps(error_response).encode())
    
    async def _handle_check_drift(self, msg):
        """Handle drift check requests."""
        try:
            data = json.loads(msg.data.decode())
            player_id = UUID(data['player_id'])
            window_hours = data.get('window_hours', 3)
            
            metrics = await self.drift_detector.check_drift(
                player_id=player_id,
                window_hours=window_hours,
                force=True
            )
            
            if not metrics:
                response = {
                    'success': True,
                    'drift_detected': False,
                    'canonical_theme_reminder': "Core loop: Kill → Harvest → Negotiate → Get Drugs → Build Empire"
                }
            else:
                response = {
                    'success': True,
                    'drift_detected': True,
                    'drift_score': metrics.drift_score,
                    'severity': metrics.severity.value,
                    'details': {
                        'quest_allocation': metrics.quest_allocation,
                        'time_allocation': metrics.time_allocation,
                        'theme_consistency': metrics.theme_consistency
                    },
                    'recommended_remediation': metrics.recommended_correction,
                    'canonical_theme_reminder': metrics.canonical_reminder
                }
            
            await self.nc.publish(msg.reply, json.dumps(response).encode())
            
        except Exception as e:
            logger.error(f"Error handling drift check: {e}")
            error_response = {
                'success': False,
                'error': str(e)
            }
            await self.nc.publish(msg.reply, json.dumps(error_response).encode())
    
    async def _handle_update_arc_progress(self, msg):
        """Handle arc progress updates."""
        try:
            data = json.loads(msg.data.decode())
            
            await self.story_manager.update_arc_progress(
                player_id=UUID(data['player_id']),
                arc_id=data['arc_id'],
                arc_role=ArcRole(data['arc_role']),
                progress_state=ProgressState(data['progress_state']),
                last_beat_id=data.get('last_beat_id')
            )
            
            response = {'success': True}
            await self.nc.publish(msg.reply, json.dumps(response).encode())
            
        except Exception as e:
            logger.error(f"Error handling arc progress update: {e}")
            error_response = {
                'success': False,
                'error': str(e)
            }
            await self.nc.publish(msg.reply, json.dumps(error_response).encode())
    
    async def _handle_update_relationship(self, msg):
        """Handle relationship updates."""
        try:
            data = json.loads(msg.data.decode())
            
            relationship = await self.story_manager.update_relationship(
                player_id=UUID(data['player_id']),
                entity_id=data['entity_id'],
                entity_type=data['entity_type'],
                score_delta=data.get('score_delta'),
                new_flags=data.get('new_flags'),
                interaction=data.get('interaction')
            )
            
            response = {
                'success': True,
                'relationship': relationship.dict()
            }
            await self.nc.publish(msg.reply, json.dumps(response).encode())
            
        except Exception as e:
            logger.error(f"Error handling relationship update: {e}")
            error_response = {
                'success': False,
                'error': str(e)
            }
            await self.nc.publish(msg.reply, json.dumps(error_response).encode())
    
    async def _handle_update_standing(self, msg):
        """Handle Dark World standing updates."""
        try:
            data = json.loads(msg.data.decode())
            
            from services.story_memory.story_schemas import DarkWorldFamily
            
            standing = await self.story_manager.update_dark_world_standing(
                player_id=UUID(data['player_id']),
                family=DarkWorldFamily(data['family']),
                standing_delta=data.get('standing_delta'),
                favor_delta=data.get('favor_delta'),
                debt_delta=data.get('debt_delta'),
                betrayal=data.get('betrayal', False),
                special_status=data.get('special_status')
            )
            
            response = {
                'success': True,
                'standing': standing.dict()
            }
            await self.nc.publish(msg.reply, json.dumps(response).encode())
            
        except Exception as e:
            logger.error(f"Error handling standing update: {e}")
            error_response = {
                'success': False,
                'error': str(e)
            }
            await self.nc.publish(msg.reply, json.dumps(error_response).encode())


def handle_shutdown(signum, frame):
    """Handle shutdown signals."""
    logger.info(f"Received signal {signum}, shutting down...")
    if hasattr(handle_shutdown, 'service'):
        asyncio.create_task(handle_shutdown.service.stop())


async def main():
    """Main entry point."""
    # Configure logging
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level="INFO"
    )
    
    # Create and start service
    service = StoryMemoryNATSService()
    handle_shutdown.service = service
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)
    
    try:
        await service.start()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Service failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

