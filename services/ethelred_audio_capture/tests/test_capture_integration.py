"""
Integration tests for audio capture service
"""
import asyncio
import numpy as np
import uuid
import json
from datetime import datetime
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
import tempfile

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from capture_service import AudioCaptureService
from segment_processor import AudioMetadata
from media_storage import MediaStorageHandler

# Mock protobuf imports
sys.path.append(str(Path(__file__).parent.parent.parent))
from services.ethelred_audio.compile_proto import compile_proto
compile_proto()
from services.ethelred_audio.generated import ethelred_audio_pb2 as audio_pb2


def generate_test_audio(duration: float, sample_rate: int = 48000) -> np.ndarray:
    """Generate test audio."""
    t = np.linspace(0, duration, int(duration * sample_rate), False)
    return (np.sin(2 * np.pi * 440 * t) * 0.5).astype(np.float32)


class MockNATSClient:
    """Mock NATS client for testing."""
    def __init__(self):
        self.published_messages = []
    
    async def publish(self, subject: str, data: bytes):
        self.published_messages.append((subject, data))


class MockPostgresPool:
    """Mock PostgreSQL pool for testing."""
    def __init__(self):
        self.executed_queries = []
    
    async def execute(self, query: str, *args):
        self.executed_queries.append((query, args))
    
    async def fetch(self, query: str, *args):
        return []
    
    async def fetchrow(self, query: str, *args):
        return None


async def test_capture_service_lifecycle():
    """Test service start/stop lifecycle."""
    # Setup mocks
    postgres_pool = MockPostgresPool()
    nats_client = MockNATSClient()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        media_storage = MediaStorageHandler(base_path=temp_dir)
        
        service = AudioCaptureService(
            postgres_pool,
            nats_client,
            media_storage,
            "test-build-001"
        )
        
        # Start service
        await service.start()
        
        # Create a stream
        metadata = AudioMetadata(
            speaker_id="test-npc",
            language_code="en-US",
            bus_name="dialogue_bus"
        )
        
        stream_id = await service.create_audio_stream(
            "dialogue_bus",
            48000,
            metadata
        )
        
        assert stream_id in service.active_streams
        
        # Close stream
        await service.close_stream(stream_id)
        assert stream_id not in service.active_streams
        
        # Stop service
        await service.stop()
    
    print("✓ Service lifecycle test passed")


async def test_dialogue_capture_flow():
    """Test full dialogue capture flow."""
    postgres_pool = MockPostgresPool()
    nats_client = MockNATSClient()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        media_storage = MediaStorageHandler(base_path=temp_dir)
        
        service = AudioCaptureService(
            postgres_pool,
            nats_client,
            media_storage,
            "test-build-001"
        )
        
        await service.start()
        
        # Create dialogue stream
        metadata = AudioMetadata(
            speaker_id="npc-vampire-01",
            speaker_role="npc",
            archetype_id="vampire_house_alpha",
            language_code="en-US",
            scene_id="castle_entrance",
            bus_name="dialogue_bus",
            simulator_applied=True
        )
        
        stream_id = await service.create_audio_stream(
            "dialogue_bus",
            48000,
            metadata
        )
        
        # Feed audio data with game context
        audio_data = generate_test_audio(2.0, 48000)  # 2 seconds
        game_context = {
            "line_id": "vampire_greeting_01",
            "emotional_context": "menacing",
            "experience_id": "castle_exploration"
        }
        
        await service.feed_audio_data(stream_id, audio_data, game_context)
        
        # Close stream to process remaining
        await service.close_stream(stream_id, game_context)
        
        # Verify database calls
        assert len(postgres_pool.executed_queries) > 0
        db_query, db_args = postgres_pool.executed_queries[0]
        assert "INSERT INTO audio_segments" in db_query
        
        # Verify NATS messages
        assert len(nats_client.published_messages) > 0
        subject, data = nats_client.published_messages[0]
        assert subject == 'svc.ethelred.audio.v1.segment_created'
        
        # Parse protobuf message
        event = audio_pb2.SegmentCreatedEvent()
        event.ParseFromString(data)
        
        assert event.envelope.domain == "Audio"
        assert event.segment_type == audio_pb2.SEGMENT_TYPE_DIALOGUE
        assert event.speaker.archetype_id == "vampire_house_alpha"
        assert event.context.line_id == "vampire_greeting_01"
        assert event.simulator_applied == True
        
        # Verify media file was created
        media_files = list(Path(temp_dir).rglob("*.wav"))
        assert len(media_files) > 0
        
        await service.stop()
    
    print("✓ Dialogue capture flow test passed")


async def test_ambient_capture():
    """Test ambient audio capture."""
    postgres_pool = MockPostgresPool()
    nats_client = MockNATSClient()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        media_storage = MediaStorageHandler(base_path=temp_dir)
        
        service = AudioCaptureService(
            postgres_pool,
            nats_client,
            media_storage,
            "test-build-001"
        )
        
        await service.start()
        
        # Create ambient stream
        metadata = AudioMetadata(
            scene_id="dark_forest",
            environment_type="forest_night",
            bus_name="ambient_bus"
        )
        
        stream_id = await service.create_audio_stream(
            "ambient_bus",
            48000,
            metadata
        )
        
        # Feed 6 seconds of ambient audio
        audio_data = generate_test_audio(6.0, 48000)
        await service.feed_audio_data(stream_id, audio_data)
        
        await service.close_stream(stream_id)
        
        # Should create multiple fixed-window segments
        assert len(nats_client.published_messages) > 1
        
        # Check first segment
        event = audio_pb2.SegmentCreatedEvent()
        event.ParseFromString(nats_client.published_messages[0][1])
        assert event.segment_type == audio_pb2.SEGMENT_TYPE_AMBIENT
        assert event.context.environment_type == "forest_night"
        
        await service.stop()
    
    print("✓ Ambient capture test passed")


async def test_monster_vocalization_capture():
    """Test monster vocalization capture."""
    postgres_pool = MockPostgresPool()
    nats_client = MockNATSClient()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        media_storage = MediaStorageHandler(base_path=temp_dir)
        
        service = AudioCaptureService(
            postgres_pool,
            nats_client,
            media_storage,
            "test-build-001"
        )
        
        await service.start()
        
        # Create vocals stream
        metadata = AudioMetadata(
            speaker_id="zombie-01",
            speaker_role="npc",
            archetype_id="zombie_horde",
            bus_name="vocals_bus",
            simulator_applied=True
        )
        
        stream_id = await service.create_audio_stream(
            "vocals_bus",
            48000,
            metadata
        )
        
        # Create vocalization with silence gaps
        sample_rate = 48000
        vocalization = []
        
        # Short growl
        t = np.linspace(0, 0.3, int(0.3 * sample_rate))
        growl = np.sin(2 * np.pi * 60 * t) * np.exp(-t * 3)
        vocalization.append(growl.astype(np.float32))
        
        # Silence
        vocalization.append(np.zeros(int(0.5 * sample_rate), dtype=np.float32))
        
        # Roar
        t = np.linspace(0, 0.5, int(0.5 * sample_rate))
        roar = np.sin(2 * np.pi * 80 * t) * (1 - t/0.5)
        vocalization.append(roar.astype(np.float32))
        
        audio_data = np.concatenate(vocalization)
        
        await service.feed_audio_data(stream_id, audio_data)
        await service.close_stream(stream_id)
        
        # Should create vocalization segments
        assert len(nats_client.published_messages) >= 1
        
        event = audio_pb2.SegmentCreatedEvent()
        event.ParseFromString(nats_client.published_messages[0][1])
        assert event.segment_type == audio_pb2.SEGMENT_TYPE_MONSTER_VOCALIZATION
        assert event.speaker.archetype_id == "zombie_horde"
        
        await service.stop()
    
    print("✓ Monster vocalization capture test passed")


async def test_error_handling():
    """Test error handling in capture service."""
    postgres_pool = MockPostgresPool()
    nats_client = MockNATSClient()
    
    # Mock storage to fail
    media_storage = MediaStorageHandler(base_path="/invalid/path/that/doesnt/exist")
    
    service = AudioCaptureService(
        postgres_pool,
        nats_client,
        media_storage,
        "test-build-001"
    )
    
    await service.start()
    
    # Feed audio to non-existent stream
    audio_data = generate_test_audio(1.0)
    await service.feed_audio_data("invalid-stream-id", audio_data)
    # Should handle gracefully without crashing
    
    # Create stream and feed invalid audio
    stream_id = await service.create_audio_stream(
        "test_bus",
        48000,
        AudioMetadata()
    )
    
    # Feed audio that will fail to store
    await service.feed_audio_data(stream_id, audio_data)
    await service.close_stream(stream_id)
    
    # Should handle storage failure gracefully
    # No segments should be published if storage failed
    assert len(nats_client.published_messages) == 0
    
    await service.stop()
    
    print("✓ Error handling test passed")


async def test_metadata_persistence():
    """Test that all metadata is correctly persisted."""
    postgres_pool = MockPostgresPool()
    nats_client = MockNATSClient()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        media_storage = MediaStorageHandler(base_path=temp_dir)
        
        service = AudioCaptureService(
            postgres_pool,
            nats_client,
            media_storage,
            "test-build-001"
        )
        
        await service.start()
        
        # Create stream with full metadata
        metadata = AudioMetadata(
            speaker_id="npc-complex",
            speaker_role="npc",
            archetype_id="vampire_elder",
            language_code="en-GB",
            scene_id="throne_room",
            experience_id="boss_encounter",
            line_id="boss_monologue_01",
            emotional_tag="rage",
            environment_type="gothic_chamber",
            bus_name="dialogue_bus",
            simulator_applied=True,
            additional={
                "quest_id": "defeat_vampire_lord",
                "player_level": "25"
            }
        )
        
        stream_id = await service.create_audio_stream(
            "dialogue_bus",
            48000,
            metadata
        )
        
        audio_data = generate_test_audio(1.5)
        await service.feed_audio_data(stream_id, audio_data)
        await service.close_stream(stream_id)
        
        # Check database insert
        assert len(postgres_pool.executed_queries) > 0
        query, args = postgres_pool.executed_queries[0]
        
        # Verify all fields are in the insert
        assert args[4] == "npc"  # speaker_role
        assert args[5] == "vampire_elder"  # archetype_id
        assert args[6] == "en-GB"  # language_code
        assert args[10] == "rage"  # emotional_tag
        
        # Check additional metadata
        additional_json = json.loads(args[21])
        assert additional_json["quest_id"] == "defeat_vampire_lord"
        assert additional_json["player_level"] == "25"
        
        await service.stop()
    
    print("✓ Metadata persistence test passed")


async def main():
    """Run all integration tests."""
    print("Running capture service integration tests...")
    
    await test_capture_service_lifecycle()
    await test_dialogue_capture_flow()
    await test_ambient_capture()
    await test_monster_vocalization_capture()
    await test_error_handling()
    await test_metadata_persistence()
    
    print("\nAll integration tests passed! ✅")


if __name__ == "__main__":
    asyncio.run(main())

