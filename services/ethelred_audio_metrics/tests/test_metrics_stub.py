"""
Unit tests for audio metrics service stub implementation
"""
import asyncio
import numpy as np
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock
import tempfile

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from metrics_service import AudioMetricsAnalyzer, AudioMetricsService

# Import protobuf
sys.path.append(str(Path(__file__).parent.parent.parent))
from services.ethelred_audio.compile_proto import compile_proto
compile_proto()
from services.ethelred_audio.generated import ethelred_audio_pb2 as audio_pb2


def generate_test_audio(duration: float = 1.0, 
                       sample_rate: int = 48000,
                       amplitude: float = 0.5) -> np.ndarray:
    """Generate test audio signal."""
    t = np.linspace(0, duration, int(duration * sample_rate))
    # Mix of frequencies for more realistic audio
    signal = amplitude * (
        0.5 * np.sin(2 * np.pi * 440 * t) +  # A4
        0.3 * np.sin(2 * np.pi * 554 * t) +  # C#5
        0.2 * np.sin(2 * np.pi * 659 * t)    # E5
    )
    return signal.astype(np.float32)


async def test_analyzer_intelligibility():
    """Test intelligibility analysis."""
    analyzer = AudioMetricsAnalyzer()
    
    # Test normal audio
    audio = generate_test_audio(amplitude=0.5)
    score, band = await analyzer.analyze_intelligibility(audio, 48000, "en-US")
    assert 0.0 <= score <= 1.0
    assert band in ["acceptable", "degraded", "unacceptable"]
    
    # Test quiet audio
    quiet_audio = generate_test_audio(amplitude=0.005)
    score, band = await analyzer.analyze_intelligibility(quiet_audio, 48000, "en-US")
    assert score < 0.5  # Should be low
    assert band == "unacceptable"
    
    # Test clipped audio
    clipped_audio = generate_test_audio(amplitude=2.0)
    clipped_audio = np.clip(clipped_audio, -1.0, 1.0)
    score, band = await analyzer.analyze_intelligibility(clipped_audio, 48000, "en-US")
    assert band == "degraded"  # Clipping detected
    
    print("✓ Intelligibility analysis test passed")


async def test_analyzer_naturalness():
    """Test naturalness analysis."""
    analyzer = AudioMetricsAnalyzer()
    
    # Test normal audio
    audio = generate_test_audio()
    score, band = await analyzer.analyze_naturalness(audio, 48000)
    assert 0.0 <= score <= 1.0
    assert band in ["ok", "robotic", "monotone"]
    
    print("✓ Naturalness analysis test passed")


async def test_analyzer_archetype():
    """Test archetype conformity analysis."""
    analyzer = AudioMetricsAnalyzer()
    
    audio = generate_test_audio()
    
    # Test with vampire archetype
    score, band = await analyzer.analyze_archetype_conformity(
        audio, 48000, "vampire_house_alpha"
    )
    assert 0.0 <= score <= 1.0
    assert band in ["on_profile", "too_clean", "too_flat", "misaligned"]
    
    # Test with zombie archetype
    score2, band2 = await analyzer.analyze_archetype_conformity(
        audio, 48000, "zombie_horde"
    )
    assert 0.0 <= score2 <= 1.0
    
    # Test without archetype
    score3, band3 = await analyzer.analyze_archetype_conformity(
        audio, 48000, None
    )
    assert score3 == 1.0
    assert band3 == "on_profile"
    
    print("✓ Archetype conformity analysis test passed")


async def test_analyzer_simulator():
    """Test simulator stability analysis."""
    analyzer = AudioMetricsAnalyzer()
    
    # Test stable audio
    audio = generate_test_audio()
    score, band = await analyzer.analyze_simulator_stability(
        audio, 48000, True
    )
    assert score > 0.8
    assert band == "stable"
    
    # Test with discontinuity
    audio_with_glitch = audio.copy()
    audio_with_glitch[len(audio)//2] = 0.9  # Add spike
    score2, band2 = await analyzer.analyze_simulator_stability(
        audio_with_glitch, 48000, True
    )
    assert score2 < 0.8
    assert band2 == "unstable"
    
    # Test without simulator
    score3, band3 = await analyzer.analyze_simulator_stability(
        audio, 48000, False
    )
    assert score3 == 1.0
    assert band3 == "stable"
    
    print("✓ Simulator stability analysis test passed")


async def test_analyzer_mix_quality():
    """Test mix quality analysis."""
    analyzer = AudioMetricsAnalyzer()
    
    # Test normal mix
    audio = generate_test_audio(amplitude=0.3)
    score, band = await analyzer.analyze_mix_quality(audio, 48000)
    assert 0.0 <= score <= 1.0
    assert band in ["ok", "noisy", "clipping", "unbalanced"]
    
    # Test quiet mix
    quiet = generate_test_audio(amplitude=0.02)
    score2, band2 = await analyzer.analyze_mix_quality(quiet, 48000)
    assert score2 < score  # Should be lower
    assert band2 == "unbalanced"
    
    # Test loud mix
    loud = generate_test_audio(amplitude=0.95)
    score3, band3 = await analyzer.analyze_mix_quality(loud, 48000)
    assert band3 == "clipping"
    
    print("✓ Mix quality analysis test passed")


class MockPostgresPool:
    """Mock PostgreSQL pool."""
    def __init__(self):
        self.executed = []
    
    async def execute(self, query, *args):
        self.executed.append((query, args))


class MockNATSClient:
    """Mock NATS client."""
    def __init__(self):
        self.published = []
        self.callbacks = {}
    
    async def subscribe(self, subject, cb=None, queue=None):
        self.callbacks[subject] = cb
    
    async def publish(self, subject, data):
        self.published.append((subject, data))
    
    async def close(self):
        pass


async def test_metrics_service_flow():
    """Test complete metrics service flow."""
    # Setup mocks
    postgres = MockPostgresPool()
    nats = MockNATSClient()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test audio file
        audio_data = generate_test_audio()
        media_uri = f"redalert://media/audio/test/segment-001.wav"
        
        # Mock media storage
        from services.ethelred_audio_capture.media_storage import MediaStorageHandler
        media_storage = MediaStorageHandler(base_path=temp_dir)
        
        # Store test audio
        import wave
        test_file = Path(temp_dir) / "test" / "segment-001.wav"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        
        with wave.open(str(test_file), 'wb') as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(48000)
            wav.writeframes((audio_data * 32767).astype(np.int16).tobytes())
        
        # Override retrieve method to return our test file
        async def mock_retrieve(uri):
            if uri == media_uri:
                return audio_data, 48000
            return None
        
        media_storage.retrieve_segment = mock_retrieve
        
        # Create service
        service = AudioMetricsService(postgres, nats, media_storage)
        await service.start(num_workers=1)
        
        # Create test event
        event = audio_pb2.SegmentCreatedEvent()
        event.envelope.trace_id = "test-trace"
        event.envelope.domain = "Audio"
        event.envelope.build_id = "test-build"
        event.segment_id = "segment-001"
        event.segment_type = audio_pb2.SEGMENT_TYPE_DIALOGUE
        event.media_uri = media_uri
        event.language_code = "en-US"
        event.speaker.speaker_id = "test-speaker"
        event.speaker.archetype_id = "vampire_house_alpha"
        event.simulator_applied = True
        
        # Simulate NATS message
        class MockMessage:
            def __init__(self, data):
                self.data = data
        
        await nats.callbacks['svc.ethelred.audio.v1.segment_created'](
            MockMessage(event.SerializeToString())
        )
        
        # Wait for processing
        await asyncio.sleep(0.5)
        
        # Verify database insert
        assert len(postgres.executed) > 0
        query, args = postgres.executed[0]
        assert "INSERT INTO audio_scores" in query
        assert args[0] == "segment-001"  # segment_id
        
        # Verify NATS publish
        assert len(nats.published) > 0
        subject, data = nats.published[0]
        assert subject == 'events.ethelred.audio.v1.scores'
        
        # Parse published event
        scores_event = audio_pb2.AudioScoresEvent()
        scores_event.ParseFromString(data)
        
        assert scores_event.segment_id == "segment-001"
        assert 0.0 <= scores_event.scores.intelligibility <= 1.0
        assert scores_event.bands.intelligibility != audio_pb2.INTELLIGIBILITY_UNSPECIFIED
        
        await service.stop()
    
    print("✓ Metrics service flow test passed")


async def test_error_handling():
    """Test error handling in metrics service."""
    postgres = MockPostgresPool()
    nats = MockNATSClient()
    
    # Mock media storage that fails
    media_storage = MagicMock()
    media_storage.retrieve_segment = AsyncMock(return_value=None)
    
    service = AudioMetricsService(postgres, nats, media_storage)
    await service.start(num_workers=1)
    
    # Send event with unretrievable audio
    event = audio_pb2.SegmentCreatedEvent()
    event.segment_id = "bad-segment"
    event.media_uri = "invalid://uri"
    
    await nats.callbacks['svc.ethelred.audio.v1.segment_created'](
        MockMessage(event.SerializeToString())
    )
    
    await asyncio.sleep(0.1)
    
    # Should handle error gracefully
    # No scores should be stored or published
    assert len(postgres.executed) == 0
    assert len(nats.published) == 0
    
    await service.stop()
    
    print("✓ Error handling test passed")


async def main():
    """Run all tests."""
    print("Running audio metrics stub tests...")
    
    await test_analyzer_intelligibility()
    await test_analyzer_naturalness()
    await test_analyzer_archetype()
    await test_analyzer_simulator()
    await test_analyzer_mix_quality()
    await test_metrics_service_flow()
    await test_error_handling()
    
    print("\nAll metrics stub tests passed! ✅")


# Helper class for mock message
class MockMessage:
    def __init__(self, data):
        self.data = data


if __name__ == "__main__":
    asyncio.run(main())

