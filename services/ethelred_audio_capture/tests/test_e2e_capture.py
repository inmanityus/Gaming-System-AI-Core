"""
End-to-end test for audio capture pipeline
"""
import asyncio
import sys
import os
from pathlib import Path
import tempfile
import asyncpg
import logging

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent))

from ue5_integration_harness import UE5AudioSimulator
from capture_service import AudioCaptureService
from media_storage import MediaStorageHandler

# Import shared modules
from shared.nats_client import get_nats_client
from shared.database import get_postgres_pool

# Import protobuf
from services.ethelred_audio.compile_proto import compile_proto
compile_proto()
from services.ethelred_audio.generated import ethelred_audio_pb2 as audio_pb2


logger = logging.getLogger(__name__)


class MockNATSClient:
    """Mock NATS client that captures messages."""
    def __init__(self):
        self.messages = []
        self.callbacks = {}
    
    async def connect(self, *args, **kwargs):
        pass
    
    async def publish(self, subject: str, data: bytes):
        self.messages.append((subject, data))
        # Trigger any callbacks
        if subject in self.callbacks:
            for cb in self.callbacks[subject]:
                await cb(subject, data)
    
    async def subscribe(self, subject: str, cb=None, **kwargs):
        if subject not in self.callbacks:
            self.callbacks[subject] = []
        if cb:
            self.callbacks[subject].append(cb)
    
    async def close(self):
        pass


async def setup_test_database():
    """Setup test database with schema."""
    # Connect to default postgres database
    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        user='postgres',
        password='postgres',
        database='postgres'
    )
    
    try:
        # Create test database
        try:
            await conn.execute('DROP DATABASE IF EXISTS test_audio_e2e')
            await conn.execute('CREATE DATABASE test_audio_e2e')
        except Exception as e:
            logger.warning(f"Database setup warning: {e}")
    finally:
        await conn.close()
    
    # Connect to test database
    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        user='postgres', 
        password='postgres',
        database='test_audio_e2e'
    )
    
    try:
        # Apply migration
        migration_path = Path(__file__).parent.parent.parent.parent / 'database' / 'migrations' / '014_audio_authentication.sql'
        with open(migration_path, 'r') as f:
            await conn.execute(f.read())
    finally:
        await conn.close()
    
    # Return connection pool
    return await asyncpg.create_pool(
        host='localhost',
        port=5432,
        user='postgres',
        password='postgres',
        database='test_audio_e2e',
        min_size=1,
        max_size=5
    )


async def test_dialogue_capture_e2e():
    """Test complete dialogue capture flow."""
    postgres_pool = await setup_test_database()
    nats_client = MockNATSClient()
    
    # Track received events
    received_events = []
    
    async def event_handler(subject: str, data: bytes):
        event = audio_pb2.SegmentCreatedEvent()
        event.ParseFromString(data)
        received_events.append(event)
    
    await nats_client.subscribe('svc.ethelred.audio.v1.segment_created', event_handler)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Start capture service
        media_storage = MediaStorageHandler(base_path=temp_dir)
        capture_service = AudioCaptureService(
            postgres_pool,
            nats_client,
            media_storage,
            "test-build-e2e"
        )
        
        # Create service task
        import uvicorn
        from capture_service import app, capture_service as global_service
        
        # Set global service instance
        import capture_service as capture_module
        capture_module.capture_service = capture_service
        
        # Start service
        await capture_service.start()
        
        # Run FastAPI in background
        config = uvicorn.Config(app, host="127.0.0.1", port=8089, log_level="error")
        server = uvicorn.Server(config)
        
        api_task = asyncio.create_task(server.serve())
        await asyncio.sleep(1)  # Let server start
        
        # Initialize UE5 simulator
        simulator = UE5AudioSimulator("http://localhost:8089")
        
        try:
            await simulator.connect()
            
            # Run a simple scene
            await simulator.run_scene("castle_entrance")
            
            # Wait for processing
            await asyncio.sleep(2)
            
            # Verify results
            assert len(received_events) > 0, "No events received"
            
            # Check first event
            first_event = received_events[0]
            assert first_event.envelope.domain == "Audio"
            assert first_event.envelope.build_id == "test-build-e2e"
            assert first_event.segment_type in [
                audio_pb2.SEGMENT_TYPE_DIALOGUE,
                audio_pb2.SEGMENT_TYPE_AMBIENT
            ]
            
            # Check dialogue events specifically
            dialogue_events = [
                e for e in received_events 
                if e.segment_type == audio_pb2.SEGMENT_TYPE_DIALOGUE
            ]
            
            assert len(dialogue_events) >= 3, f"Expected at least 3 dialogue events, got {len(dialogue_events)}"
            
            # Verify vampire lord dialogue
            vampire_events = [
                e for e in dialogue_events
                if e.speaker.speaker_id == "npc_vampire_lord"
            ]
            assert len(vampire_events) >= 2
            assert vampire_events[0].speaker.archetype_id == "vampire_house_alpha"
            assert vampire_events[0].context.emotional_tag in ["menacing", "anger"]
            
            # Check database storage
            async with postgres_pool.acquire() as conn:
                segment_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM audio_segments WHERE build_id = $1",
                    "test-build-e2e"
                )
                assert segment_count == len(received_events)
                
                # Check specific segment
                vampire_segment = await conn.fetchrow(
                    """
                    SELECT * FROM audio_segments 
                    WHERE speaker_id = $1 AND segment_type = $2
                    LIMIT 1
                    """,
                    "npc_vampire_lord", "dialogue"
                )
                assert vampire_segment is not None
                assert vampire_segment['archetype_id'] == "vampire_house_alpha"
                assert vampire_segment['language_code'] == "en-US"
            
            # Check media files
            media_files = list(Path(temp_dir).rglob("*.wav"))
            assert len(media_files) == len(received_events)
            
            logger.info(f"✓ E2E test passed: {len(received_events)} segments captured")
            
        finally:
            # Cleanup
            await simulator.disconnect()
            server.should_exit = True
            await api_task
            await capture_service.stop()
    
    await postgres_pool.close()


async def test_vocal_simulator_flow():
    """Test vocal simulator pre/post capture."""
    postgres_pool = await setup_test_database()
    nats_client = MockNATSClient()
    
    vocal_pre_events = []
    vocal_post_events = []
    
    async def event_handler(subject: str, data: bytes):
        event = audio_pb2.SegmentCreatedEvent()
        event.ParseFromString(data)
        
        if event.bus_name == "vocal_pre":
            vocal_pre_events.append(event)
        elif event.bus_name == "vocal_post":
            vocal_post_events.append(event)
    
    await nats_client.subscribe('svc.ethelred.audio.v1.segment_created', event_handler)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Setup service
        media_storage = MediaStorageHandler(base_path=temp_dir)
        capture_service = AudioCaptureService(
            postgres_pool,
            nats_client,
            media_storage,
            "test-build-vocal"
        )
        
        import capture_service as capture_module
        capture_module.capture_service = capture_service
        
        await capture_service.start()
        
        # Start API
        from capture_service import app
        config = uvicorn.Config(app, host="127.0.0.1", port=8089, log_level="error")
        server = uvicorn.Server(config)
        api_task = asyncio.create_task(server.serve())
        await asyncio.sleep(1)
        
        # Run zombie scene (uses vocal simulator)
        simulator = UE5AudioSimulator("http://localhost:8089")
        
        try:
            await simulator.connect()
            await simulator.run_scene("zombie_encounter")
            await asyncio.sleep(2)
            
            # Verify pre/post capture
            assert len(vocal_pre_events) > 0, "No pre-simulator events"
            assert len(vocal_post_events) > 0, "No post-simulator events"
            
            # Compare pre/post for same speaker
            pre_zombie = next(
                (e for e in vocal_pre_events if "zombie" in e.speaker.speaker_id),
                None
            )
            post_zombie = next(
                (e for e in vocal_post_events if "zombie" in e.speaker.speaker_id),
                None
            )
            
            assert pre_zombie is not None
            assert post_zombie is not None
            
            # Post should have simulator_applied flag
            assert post_zombie.simulator_applied == True
            assert pre_zombie.simulator_applied == False
            
            # Same speaker/archetype
            assert pre_zombie.speaker.speaker_id == post_zombie.speaker.speaker_id
            assert pre_zombie.speaker.archetype_id == post_zombie.speaker.archetype_id
            
            logger.info("✓ Vocal simulator flow test passed")
            
        finally:
            await simulator.disconnect()
            server.should_exit = True
            await api_task
            await capture_service.stop()
    
    await postgres_pool.close()


async def test_multi_bus_sync():
    """Test multiple audio buses capturing simultaneously."""
    postgres_pool = await setup_test_database()
    nats_client = MockNATSClient()
    
    events_by_bus = {}
    
    async def event_handler(subject: str, data: bytes):
        event = audio_pb2.SegmentCreatedEvent()
        event.ParseFromString(data)
        
        bus = event.bus_name
        if bus not in events_by_bus:
            events_by_bus[bus] = []
        events_by_bus[bus].append(event)
    
    await nats_client.subscribe('svc.ethelred.audio.v1.segment_created', event_handler)
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Setup service
        media_storage = MediaStorageHandler(base_path=temp_dir)
        capture_service = AudioCaptureService(
            postgres_pool,
            nats_client,
            media_storage,
            "test-build-multipass"
        )
        
        import capture_service as capture_module
        capture_module.capture_service = capture_service
        
        await capture_service.start()
        
        # Start API
        from capture_service import app
        config = uvicorn.Config(app, host="127.0.0.1", port=8089, log_level="error")
        server = uvicorn.Server(config)
        api_task = asyncio.create_task(server.serve())
        await asyncio.sleep(1)
        
        simulator = UE5AudioSimulator("http://localhost:8089")
        
        try:
            await simulator.connect()
            await simulator.run_scene("castle_entrance")
            await asyncio.sleep(2)
            
            # Should have events from multiple buses
            assert len(events_by_bus) >= 2, f"Expected multiple buses, got {list(events_by_bus.keys())}"
            
            # Check expected buses
            assert "dialogue" in events_by_bus or "dialogue_bus" in events_by_bus
            assert "ambient" in events_by_bus or "ambient_bus" in events_by_bus
            
            # Ambient should have multiple segments (fixed windows)
            ambient_events = events_by_bus.get("ambient", events_by_bus.get("ambient_bus", []))
            assert len(ambient_events) > 1, "Expected multiple ambient segments"
            
            logger.info(f"✓ Multi-bus sync test passed: {list(events_by_bus.keys())}")
            
        finally:
            await simulator.disconnect()
            server.should_exit = True
            await api_task
            await capture_service.stop()
    
    await postgres_pool.close()


async def main():
    """Run all E2E tests."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("Running audio capture E2E tests...")
    print("Note: Requires local PostgreSQL on port 5432")
    
    try:
        await test_dialogue_capture_e2e()
        await test_vocal_simulator_flow()
        await test_multi_bus_sync()
        
        print("\nAll E2E tests passed! ✅")
    except Exception as e:
        logger.error(f"E2E test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())

