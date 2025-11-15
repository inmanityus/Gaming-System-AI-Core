"""
4D Vision Ingest Service
========================

Receives 4D segment descriptors from UE5/test harnesses,
normalizes metadata, persists to database, and publishes
analysis requests.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID, uuid4
import asyncpg
from nats.aio.client import Client as NATS
from loguru import logger
from prometheus_client import start_http_server

from .segment_validator import SegmentValidator
from ..shared.nats_client import get_nats_client
from ..shared.postgres import get_postgres_pool
from .metrics import (
    IngestMetricsCollector, track_ingest_metrics, track_validation_metrics,
    ingest_segments_total, segment_duration_summary, ingest_queue_size,
    validation_failures_total
)


class VisionIngestService:
    """
    Main service for ingesting 4D vision segments.
    """
    
    def __init__(
        self,
        postgres_pool: asyncpg.Pool,
        nats_client: Optional[NATS] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        self.postgres = postgres_pool
        self.nats = nats_client
        self.validator = SegmentValidator()
        self.config = config or {}
        self.metrics = IngestMetricsCollector()
        
        # NATS subjects
        self.ingest_subject = "vision.ingest.segment"
        self.analyze_subject = "vision.analyze.request"
        self.health_subject = "vision.health.ingest"
        
        self._running = False
        self._health_task: Optional[asyncio.Task] = None
        self._queue_size = 0
    
    async def start(self):
        """Start the ingest service."""
        logger.info("Starting 4D Vision Ingest Service")
        
        if not self.nats:
            self.nats = await get_nats_client()
        
        # Subscribe to ingest requests
        await self.nats.subscribe(
            self.ingest_subject,
            cb=self._handle_segment_ingest
        )
        
        self._running = True
        self._health_task = asyncio.create_task(self._publish_health())
        
        logger.info(f"Subscribed to {self.ingest_subject}")
    
    async def stop(self):
        """Stop the ingest service."""
        logger.info("Stopping 4D Vision Ingest Service")
        self._running = False
        
        if self._health_task:
            self._health_task.cancel()
            try:
                await self._health_task
            except asyncio.CancelledError:
                pass
        
        if self.nats and self.nats.is_connected:
            await self.nats.drain()
    
    @track_ingest_metrics
    async def ingest_segment(self, segment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ingest a 4D segment descriptor.
        
        Returns:
            Dict with segment_id and status
        """
        # Update queue metrics
        self._queue_size += 1
        self.metrics.update_queue_size(self._queue_size)
        
        # Validate segment
        is_valid, errors, normalized = self.validator.validate_segment(segment_data)
        
        if not is_valid:
            logger.error(f"Invalid segment: {errors}")
            for error in errors:
                validation_failures_total.labels(failure_reason=error).inc()
            return {
                "status": "error",
                "errors": errors
            }
        
        # Generate segment ID
        segment_id = normalized.get("segment_id") or str(uuid4())
        normalized["segment_id"] = segment_id
        
        # Record segment metrics
        self.metrics.record_segment_ingested(normalized)
        
        try:
            # Store in database
            await self._store_segment(segment_id, normalized)
            
            # Publish analysis request
            await self._publish_analysis_request(segment_id, normalized)
            
            logger.info(f"Ingested segment {segment_id} for scene {normalized['scene_id']}")
            
            return {
                "status": "success",
                "segment_id": segment_id,
                "scene_id": normalized["scene_id"],
                "duration": normalized["duration_seconds"]
            }
            
        except Exception as e:
            logger.error(f"Failed to ingest segment: {e}")
            return {
                "status": "error",
                "errors": [str(e)]
            }
        finally:
            # Update queue size
            self._queue_size = max(0, self._queue_size - 1)
            self.metrics.update_queue_size(self._queue_size)
    
    async def _handle_segment_ingest(self, msg):
        """Handle segment ingest from NATS."""
        try:
            # Parse message
            data = json.loads(msg.data.decode())
            
            # Ingest segment
            result = await self.ingest_segment(data)
            
            # Reply if requested
            if msg.reply:
                await self.nats.publish(
                    msg.reply,
                    json.dumps(result).encode()
                )
                
        except Exception as e:
            logger.error(f"Error handling ingest message: {e}")
            
            if msg.reply:
                error_response = {
                    "status": "error",
                    "errors": [str(e)]
                }
                await self.nats.publish(
                    msg.reply,
                    json.dumps(error_response).encode()
                )
    
    async def _store_segment(self, segment_id: str, data: Dict[str, Any]):
        """Store segment in database."""
        async with self.postgres.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO vision_segments (
                    segment_id, build_id, scene_id, level_name, test_scenario,
                    start_timestamp, end_timestamp, duration_seconds, frame_count,
                    sampling_mode, camera_configs, media_uris, depth_uris,
                    performance_metrics, gameplay_events, metadata,
                    analysis_status
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17)
                """,
                UUID(segment_id),
                data["build_id"],
                data["scene_id"],
                data["level_name"],
                data.get("test_scenario"),
                data["start_timestamp"],
                data["end_timestamp"],
                data["duration_seconds"],
                data.get("frame_count", 0),
                data["sampling_mode"],
                json.dumps(data.get("camera_configs", [])),
                json.dumps(data.get("media_uris", {})),
                json.dumps(data.get("depth_uris", {})),
                json.dumps(data.get("performance_metrics", {})),
                json.dumps(data.get("gameplay_events", [])),
                json.dumps(data.get("metadata", {})),
                "pending"
            )
            
            # Add to analysis queue
            detector_types = data.get("detector_types", [
                "animation", "physics", "rendering", 
                "lighting", "performance", "flow"
            ])
            
            await conn.execute(
                """
                INSERT INTO vision_analysis_queue (
                    segment_id, priority, detector_types, analysis_params, status
                ) VALUES ($1, $2, $3, $4, $5)
                """,
                UUID(segment_id),
                data.get("priority", 5),
                detector_types,
                json.dumps(data.get("analysis_params", {})),
                "pending"
            )
    
    async def _publish_analysis_request(self, segment_id: str, data: Dict[str, Any]):
        """Publish analysis request to NATS."""
        if not self.nats:
            return
        
        # Create analysis request message
        request = {
            "segment_id": segment_id,
            "build_id": data["build_id"],
            "scene_id": data["scene_id"],
            "duration": data["duration_seconds"],
            "detector_types": data.get("detector_types", [
                "animation", "physics", "rendering",
                "lighting", "performance", "flow"
            ]),
            "priority": data.get("priority", 5),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        await self.nats.publish(
            self.analyze_subject,
            json.dumps(request).encode()
        )
        
        logger.debug(f"Published analysis request for segment {segment_id}")
    
    async def _publish_health(self):
        """Periodically publish health status."""
        while self._running:
            try:
                # Check database connectivity
                db_healthy = await self._check_db_health()
                
                health = {
                    "service": "vision_ingest",
                    "status": "healthy" if db_healthy else "degraded",
                    "timestamp": datetime.utcnow().isoformat(),
                    "details": {
                        "database": "connected" if db_healthy else "disconnected",
                        "nats": "connected" if self.nats and self.nats.is_connected else "disconnected"
                    }
                }
                
                if self.nats:
                    await self.nats.publish(
                        self.health_subject,
                        json.dumps(health).encode()
                    )
                
                await asyncio.sleep(30)  # Health check every 30s
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error publishing health: {e}")
                await asyncio.sleep(30)
    
    async def _check_db_health(self) -> bool:
        """Check database connectivity."""
        try:
            async with self.postgres.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception:
            return False


async def main():
    """Main entry point for the service."""
    # Start metrics server
    start_http_server(8091)
    logger.info("Metrics server started on port 8091")
    
    # Initialize resources
    postgres_pool = await get_postgres_pool()
    nats_client = await get_nats_client()
    
    # Create and start service
    service = VisionIngestService(
        postgres_pool=postgres_pool,
        nats_client=nats_client
    )
    
    try:
        await service.start()
        logger.info("4D Vision Ingest Service running. Press Ctrl+C to stop.")
        
        # Keep running
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    finally:
        await service.stop()
        await postgres_pool.close()


if __name__ == "__main__":
    asyncio.run(main())
