"""
End-to-end test for complete audio pipeline: capture → metrics → scores
"""
import asyncio
import sys
import tempfile
import logging
from pathlib import Path
from typing import List
import asyncpg

# Add parent directories to path
sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent))

# Import services
from services.ethelred_audio_capture.capture_service import AudioCaptureService
from services.ethelred_audio_capture.media_storage import MediaStorageHandler
from services.ethelred_audio_capture.ue5_integration_harness import UE5AudioSimulator
from metrics_service import AudioMetricsService

# Import protobuf
from services.ethelred_audio.compile_proto import compile_proto
compile_proto()
from services.ethelred_audio.generated import ethelred_audio_pb2 as audio_pb2

logger = logging.getLogger(__name__)


class PipelineTestHarness:
    """Test harness for complete audio pipeline."""
    
    def __init__(self, postgres_pool: asyncpg.Pool, temp_dir: str):
        self.postgres = postgres_pool
        self.temp_dir = temp_dir
        
        # Track events
        self.segment_events: List[audio_pb2.SegmentCreatedEvent] = []
        self.score_events: List[audio_pb2.AudioScoresEvent] = []
        
        # Mock NATS
        self.nats = MockNATSPipeline()
        self.nats.on_segment_created = self._handle_segment_created
        self.nats.on_scores = self._handle_scores
        
        # Services
        self.media_storage = MediaStorageHandler(base_path=temp_dir)
        self.capture_service = None
        self.metrics_service = None
    
    async def _handle_segment_created(self, event: audio_pb2.SegmentCreatedEvent):
        """Handle segment created events."""
        self.segment_events.append(event)
    
    async def _handle_scores(self, event: audio_pb2.AudioScoresEvent):
        """Handle score events."""
        self.score_events.append(event)
    
    async def start_services(self):
        """Start capture and metrics services."""
        # Start capture service
        self.capture_service = AudioCaptureService(
            self.postgres,
            self.nats,
            self.media_storage,
            "test-pipeline"
        )
        await self.capture_service.start()
        
        # Start metrics service
        self.metrics_service = AudioMetricsService(
            self.postgres,
            self.nats,
            self.media_storage
        )
        await self.metrics_service.start(num_workers=2)
        
        # Start mock API servers
        import uvicorn
        from services.ethelred_audio_capture.capture_service import app as capture_app
        import services.ethelred_audio_capture.capture_service as capture_module
        capture_module.capture_service = self.capture_service
        
        config = uvicorn.Config(capture_app, host="127.0.0.1", port=8089, log_level="error")
        server = uvicorn.Server(config)
        self.api_task = asyncio.create_task(server.serve())
        
        await asyncio.sleep(1)  # Let services start
    
    async def stop_services(self):
        """Stop all services."""
        if hasattr(self, 'api_task'):
            # Stop API server
            self.api_task.cancel()
            try:
                await self.api_task
            except asyncio.CancelledError:
                pass
        
        if self.capture_service:
            await self.capture_service.stop()
        
        if self.metrics_service:
            await self.metrics_service.stop()
    
    async def run_test_scenario(self, scene_name: str):
        """Run a test scenario through the pipeline."""
        # Clear events
        self.segment_events.clear()
        self.score_events.clear()
        
        # Create UE5 simulator
        simulator = UE5AudioSimulator("http://localhost:8089")
        
        try:
            await simulator.connect()
            await simulator.run_scene(scene_name)
            
            # Wait for processing
            await asyncio.sleep(3)
            
        finally:
            await simulator.disconnect()
    
    def verify_pipeline(self) -> bool:
        """Verify pipeline processed correctly."""
        # Check we got segments
        if not self.segment_events:
            logger.error("No segment events received")
            return False
        
        # Check we got scores for each segment
        segment_ids = {e.segment_id for e in self.segment_events}
        score_ids = {e.segment_id for e in self.score_events}
        
        missing_scores = segment_ids - score_ids
        if missing_scores:
            logger.error(f"Missing scores for segments: {missing_scores}")
            return False
        
        # Verify score quality
        for score_event in self.score_events:
            # Check all scores are in valid range
            scores = score_event.scores
            if not (0 <= scores.intelligibility <= 1):
                logger.error(f"Invalid intelligibility score: {scores.intelligibility}")
                return False
            if not (0 <= scores.naturalness <= 1):
                logger.error(f"Invalid naturalness score: {scores.naturalness}")
                return False
            
            # Check bands are set
            if score_event.bands.intelligibility == audio_pb2.INTELLIGIBILITY_UNSPECIFIED:
                logger.error("Intelligibility band not set")
                return False
        
        return True


class MockNATSPipeline:
    """Mock NATS that connects services in pipeline."""
    
    def __init__(self):
        self.callbacks = {}
        self.on_segment_created = None
        self.on_scores = None
    
    async def subscribe(self, subject: str, cb=None, queue=None):
        self.callbacks[subject] = cb
    
    async def publish(self, subject: str, data: bytes):
        # Route events appropriately
        if subject == 'svc.ethelred.audio.v1.segment_created':
            event = audio_pb2.SegmentCreatedEvent()
            event.ParseFromString(data)
            
            # Notify test harness
            if self.on_segment_created:
                await self.on_segment_created(event)
            
            # Route to metrics service
            if subject in self.callbacks:
                class MockMsg:
                    def __init__(self, data):
                        self.data = data
                await self.callbacks[subject](MockMsg(data))
        
        elif subject == 'events.ethelred.audio.v1.scores':
            event = audio_pb2.AudioScoresEvent()
            event.ParseFromString(data)
            
            # Notify test harness
            if self.on_scores:
                await self.on_scores(event)
    
    async def close(self):
        pass


async def setup_test_database():
    """Setup test database."""
    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        user='postgres',
        password='postgres',
        database='postgres'
    )
    
    try:
        await conn.execute('DROP DATABASE IF EXISTS test_pipeline')
        await conn.execute('CREATE DATABASE test_pipeline')
    except Exception as e:
        logger.warning(f"Database setup warning: {e}")
    finally:
        await conn.close()
    
    # Connect to test database and apply migration
    conn = await asyncpg.connect(
        host='localhost',
        port=5432,
        user='postgres',
        password='postgres',
        database='test_pipeline'
    )
    
    try:
        migration_path = Path(__file__).parent.parent.parent.parent / 'database' / 'migrations' / '014_audio_authentication.sql'
        with open(migration_path, 'r') as f:
            await conn.execute(f.read())
    finally:
        await conn.close()
    
    # Return pool
    return await asyncpg.create_pool(
        host='localhost',
        port=5432,
        user='postgres',
        password='postgres',
        database='test_pipeline',
        min_size=2,
        max_size=10
    )


async def test_dialogue_pipeline():
    """Test dialogue capture through scoring pipeline."""
    postgres = await setup_test_database()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        harness = PipelineTestHarness(postgres, temp_dir)
        
        try:
            await harness.start_services()
            
            # Run castle entrance scene
            await harness.run_test_scenario("castle_entrance")
            
            # Verify pipeline
            assert harness.verify_pipeline(), "Pipeline verification failed"
            
            # Check specific results
            dialogue_segments = [
                e for e in harness.segment_events
                if e.segment_type == audio_pb2.SEGMENT_TYPE_DIALOGUE
            ]
            assert len(dialogue_segments) >= 3, f"Expected at least 3 dialogue segments, got {len(dialogue_segments)}"
            
            # Check vampire lord segments
            vampire_scores = [
                e for e in harness.score_events
                if e.speaker.archetype_id == "vampire_house_alpha"
            ]
            assert len(vampire_scores) >= 2, "Expected vampire lord scores"
            
            # Verify archetype scores
            for score in vampire_scores:
                assert score.scores.archetype_conformity > 0.6, "Vampire archetype score too low"
                assert score.simulator_applied == True
            
            # Check database persistence
            async with postgres.acquire() as conn:
                # Check segments
                segment_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM audio_segments WHERE build_id = $1",
                    "test-pipeline"
                )
                assert segment_count == len(harness.segment_events)
                
                # Check scores
                score_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM audio_scores"
                )
                assert score_count == len(harness.score_events)
                
                # Check specific score
                vampire_score_row = await conn.fetchrow(
                    """
                    SELECT s.*, seg.archetype_id 
                    FROM audio_scores s
                    JOIN audio_segments seg ON s.segment_id = seg.segment_id
                    WHERE seg.archetype_id = $1
                    LIMIT 1
                    """,
                    "vampire_house_alpha"
                )
                assert vampire_score_row is not None
                assert vampire_score_row['archetype_band'] == "on_profile"
            
            logger.info("✓ Dialogue pipeline test passed")
            
        finally:
            await harness.stop_services()
    
    await postgres.close()


async def test_multi_archetype_pipeline():
    """Test pipeline with multiple archetypes."""
    postgres = await setup_test_database()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        harness = PipelineTestHarness(postgres, temp_dir)
        
        try:
            await harness.start_services()
            
            # Run zombie encounter
            await harness.run_test_scenario("zombie_encounter")
            
            # Verify pipeline
            assert harness.verify_pipeline(), "Pipeline verification failed"
            
            # Check zombie scores
            zombie_scores = [
                e for e in harness.score_events
                if e.speaker.archetype_id == "zombie_horde"
            ]
            assert len(zombie_scores) >= 2, "Expected zombie scores"
            
            # Zombie scores might be slightly lower than vampire
            for score in zombie_scores:
                assert 0.5 < score.scores.archetype_conformity < 0.95
            
            logger.info("✓ Multi-archetype pipeline test passed")
            
        finally:
            await harness.stop_services()
    
    await postgres.close()


async def test_pipeline_resilience():
    """Test pipeline handles errors gracefully."""
    postgres = await setup_test_database()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        harness = PipelineTestHarness(postgres, temp_dir)
        
        try:
            await harness.start_services()
            
            # Inject some bad data
            bad_event = audio_pb2.SegmentCreatedEvent()
            bad_event.segment_id = "bad-segment"
            bad_event.media_uri = "invalid://does-not-exist"
            
            await harness.nats.publish(
                'svc.ethelred.audio.v1.segment_created',
                bad_event.SerializeToString()
            )
            
            # Should handle gracefully - no crash
            await asyncio.sleep(1)
            
            # Now run normal scenario
            await harness.run_test_scenario("castle_entrance")
            
            # Should still process good segments
            assert len(harness.score_events) > 0, "No scores after error recovery"
            
            logger.info("✓ Pipeline resilience test passed")
            
        finally:
            await harness.stop_services()
    
    await postgres.close()


async def main():
    """Run all pipeline E2E tests."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("Running audio pipeline E2E tests...")
    print("Note: Requires local PostgreSQL on port 5432")
    
    try:
        await test_dialogue_pipeline()
        await test_multi_archetype_pipeline()
        await test_pipeline_resilience()
        
        print("\nAll pipeline E2E tests passed! ✅")
        print("\nMilestone 1-2 Complete:")
        print("- ✅ Audio protobuf messages defined")
        print("- ✅ Database schema implemented")
        print("- ✅ Capture service scaffolded")
        print("- ✅ Virtual routing spec defined")
        print("- ✅ UE5 integration harness created")
        print("- ✅ Metrics service with stub scoring")
        print("- ✅ End-to-end pipeline validated")
        
    except Exception as e:
        logger.error(f"Pipeline test failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())

