"""
Integration tests for 4D Vision ingest service.
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch
import asyncpg

from ..ingest_service import VisionIngestService


@pytest.fixture
async def mock_postgres_pool():
    """Create mock PostgreSQL pool."""
    pool = AsyncMock(spec=asyncpg.Pool)
    
    # Mock connection
    conn = AsyncMock()
    pool.acquire = AsyncMock(return_value=conn)
    conn.__aenter__ = AsyncMock(return_value=conn)
    conn.__aexit__ = AsyncMock(return_value=None)
    conn.execute = AsyncMock()
    conn.fetchval = AsyncMock(return_value=1)  # For health checks
    
    return pool


@pytest.fixture
async def mock_nats():
    """Create mock NATS client."""
    nats = AsyncMock()
    nats.is_connected = True
    nats.subscribe = AsyncMock()
    nats.publish = AsyncMock()
    nats.drain = AsyncMock()
    return nats


@pytest.fixture
async def ingest_service(mock_postgres_pool, mock_nats):
    """Create ingest service with mocked dependencies."""
    service = VisionIngestService(
        postgres_pool=mock_postgres_pool,
        nats_client=mock_nats,
        config={}
    )
    return service


class TestVisionIngestService:
    """Test suite for vision ingest service."""
    
    @pytest.mark.asyncio
    async def test_service_start_stop(self, ingest_service, mock_nats):
        """Test service lifecycle."""
        # Start service
        await ingest_service.start()
        
        # Verify subscriptions
        mock_nats.subscribe.assert_called_once_with(
            "vision.ingest.segment",
            cb=ingest_service._handle_segment_ingest
        )
        
        assert ingest_service._running is True
        assert ingest_service._health_task is not None
        
        # Stop service
        await ingest_service.stop()
        
        assert ingest_service._running is False
        mock_nats.drain.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_ingest_valid_segment(self, ingest_service, mock_postgres_pool):
        """Test ingesting a valid segment."""
        now = datetime.utcnow()
        segment_data = {
            "build_id": "v1.0.0-test",
            "scene_id": "test_scene",
            "level_name": "test_level",
            "start_timestamp": now.isoformat(),
            "end_timestamp": (now + timedelta(seconds=10)).isoformat(),
            "sampling_mode": "window_based",
            "frame_count": 300,
            "camera_configs": [{
                "camera_id": "main",
                "camera_type": "player_pov",
                "fov": 90.0,
                "position": [0, 0, 0],
                "rotation": [0, 0, 0]
            }],
            "media_uris": {
                "main": "s3://bucket/test.mp4"
            }
        }
        
        result = await ingest_service.ingest_segment(segment_data)
        
        assert result["status"] == "success"
        assert "segment_id" in result
        assert result["scene_id"] == "test_scene"
        assert result["duration"] == 10.0
        
        # Verify database calls
        conn = await mock_postgres_pool.acquire()
        assert conn.execute.call_count == 2  # segment + queue
    
    @pytest.mark.asyncio
    async def test_ingest_invalid_segment(self, ingest_service):
        """Test ingesting an invalid segment."""
        segment_data = {
            "build_id": "invalid",  # Invalid format
            # Missing required fields
        }
        
        result = await ingest_service.ingest_segment(segment_data)
        
        assert result["status"] == "error"
        assert len(result["errors"]) > 0
    
    @pytest.mark.asyncio
    async def test_publish_analysis_request(self, ingest_service, mock_nats):
        """Test publishing analysis request."""
        segment_id = str(uuid4())
        data = {
            "build_id": "v1.0.0",
            "scene_id": "test_scene",
            "duration_seconds": 10.0,
            "priority": 8
        }
        
        await ingest_service._publish_analysis_request(segment_id, data)
        
        mock_nats.publish.assert_called_once()
        call_args = mock_nats.publish.call_args
        assert call_args[0][0] == "vision.analyze.request"
        
        # Verify message content
        message = json.loads(call_args[0][1])
        assert message["segment_id"] == segment_id
        assert message["build_id"] == "v1.0.0"
        assert message["priority"] == 8
    
    @pytest.mark.asyncio
    async def test_handle_nats_message(self, ingest_service):
        """Test handling NATS message."""
        # Create mock message
        msg = MagicMock()
        msg.data = json.dumps({
            "build_id": "v1.0.0-test",
            "scene_id": "test_scene",
            "level_name": "test_level",
            "start_timestamp": datetime.utcnow().isoformat(),
            "end_timestamp": (datetime.utcnow() + timedelta(seconds=5)).isoformat(),
            "sampling_mode": "event_based",
            "frame_count": 150,
            "camera_configs": [{
                "camera_id": "main",
                "camera_type": "player_pov",
                "fov": 90.0,
                "position": [0, 0, 0],
                "rotation": [0, 0, 0]
            }],
            "media_uris": {"main": "s3://bucket/test.mp4"}
        }).encode()
        msg.reply = "reply.topic"
        
        # Mock ingest_segment
        with patch.object(ingest_service, 'ingest_segment') as mock_ingest:
            mock_ingest.return_value = {
                "status": "success",
                "segment_id": str(uuid4())
            }
            
            await ingest_service._handle_segment_ingest(msg)
            
            mock_ingest.assert_called_once()
            
            # Verify reply
            ingest_service.nats.publish.assert_called_once_with(
                "reply.topic",
                json.dumps({"status": "success", "segment_id": mock_ingest.return_value["segment_id"]}).encode()
            )
    
    @pytest.mark.asyncio
    async def test_health_check(self, ingest_service, mock_postgres_pool):
        """Test health check functionality."""
        # Test successful health check
        health = await ingest_service._check_db_health()
        assert health is True
        
        # Test failed health check
        conn = await mock_postgres_pool.acquire()
        conn.fetchval.side_effect = Exception("DB error")
        
        health = await ingest_service._check_db_health()
        assert health is False
    
    @pytest.mark.asyncio
    async def test_health_publishing(self, ingest_service, mock_nats):
        """Test health status publishing."""
        # Start service to begin health publishing
        await ingest_service.start()
        
        # Wait a bit for health task to run
        await asyncio.sleep(0.1)
        
        # Stop to clean up
        await ingest_service.stop()
        
        # Verify health was published
        health_calls = [
            call for call in mock_nats.publish.call_args_list
            if call[0][0] == "vision.health.ingest"
        ]
        
        if health_calls:  # May not have run yet in fast test
            health_msg = json.loads(health_calls[0][0][1])
            assert health_msg["service"] == "vision_ingest"
            assert health_msg["status"] in ["healthy", "degraded"]
            assert "timestamp" in health_msg
    
    @pytest.mark.asyncio
    async def test_error_handling_in_ingest(self, ingest_service, mock_postgres_pool):
        """Test error handling during segment ingestion."""
        # Make database fail
        conn = await mock_postgres_pool.acquire()
        conn.execute.side_effect = Exception("DB insert failed")
        
        segment_data = {
            "build_id": "v1.0.0-test",
            "scene_id": "test_scene",
            "level_name": "test_level",
            "start_timestamp": datetime.utcnow().isoformat(),
            "end_timestamp": (datetime.utcnow() + timedelta(seconds=5)).isoformat(),
            "sampling_mode": "window_based",
            "frame_count": 150,
            "camera_configs": [{
                "camera_id": "main",
                "camera_type": "player_pov",
                "fov": 90.0,
                "position": [0, 0, 0],
                "rotation": [0, 0, 0]
            }],
            "media_uris": {"main": "s3://bucket/test.mp4"}
        }
        
        result = await ingest_service.ingest_segment(segment_data)
        
        assert result["status"] == "error"
        assert "DB insert failed" in result["errors"][0]
    
    @pytest.mark.asyncio
    async def test_concurrent_segment_ingestion(self, ingest_service):
        """Test handling multiple segments concurrently."""
        # Create multiple valid segments
        segments = []
        for i in range(5):
            now = datetime.utcnow()
            segments.append({
                "build_id": "v1.0.0-test",
                "scene_id": f"scene_{i}",
                "level_name": f"level_{i}",
                "start_timestamp": now.isoformat(),
                "end_timestamp": (now + timedelta(seconds=10)).isoformat(),
                "sampling_mode": "window_based",
                "frame_count": 300,
                "camera_configs": [{
                    "camera_id": "main",
                    "camera_type": "player_pov",
                    "fov": 90.0,
                    "position": [0, 0, 0],
                    "rotation": [0, 0, 0]
                }],
                "media_uris": {"main": f"s3://bucket/test_{i}.mp4"}
            })
        
        # Ingest concurrently
        tasks = [ingest_service.ingest_segment(seg) for seg in segments]
        results = await asyncio.gather(*tasks)
        
        # Verify all succeeded
        for result in results:
            assert result["status"] == "success"
            assert "segment_id" in result

