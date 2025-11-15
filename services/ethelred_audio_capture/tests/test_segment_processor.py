"""
Unit tests for audio segment processor
"""
import asyncio
import numpy as np
from datetime import datetime
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from segment_processor import (
    SegmentProcessor, AudioSegment, AudioMetadata, AudioBuffer
)


def generate_test_audio(duration: float, sample_rate: int = 48000, frequency: float = 440.0) -> np.ndarray:
    """Generate test audio signal (sine wave)."""
    t = np.linspace(0, duration, int(duration * sample_rate), False)
    return np.sin(2 * np.pi * frequency * t).astype(np.float32)


def generate_silence(duration: float, sample_rate: int = 48000) -> np.ndarray:
    """Generate silence."""
    return np.zeros(int(duration * sample_rate), dtype=np.float32)


async def test_silence_detection():
    """Test silence detection in audio."""
    processor = SegmentProcessor(min_silence_duration=0.2)
    
    # Create audio with speech and silence
    sample_rate = 48000
    speech1 = generate_test_audio(0.5, sample_rate, 440)  # 0.5s speech
    silence1 = generate_silence(0.3, sample_rate)  # 0.3s silence
    speech2 = generate_test_audio(0.8, sample_rate, 880)  # 0.8s speech
    silence2 = generate_silence(0.5, sample_rate)  # 0.5s silence
    speech3 = generate_test_audio(0.3, sample_rate, 660)  # 0.3s speech
    
    audio_data = np.concatenate([speech1, silence1, speech2, silence2, speech3])
    
    # Detect silence
    silence_regions = processor.detect_silence(audio_data, sample_rate)
    
    # Should detect 2 silence regions (≥0.2s)
    assert len(silence_regions) == 2
    
    # Verify approximate positions
    # First silence around 0.5s
    assert abs(silence_regions[0][0] / sample_rate - 0.5) < 0.1
    # Second silence around 1.6s
    assert abs(silence_regions[1][0] / sample_rate - 1.6) < 0.1
    
    print("✓ Silence detection test passed")


async def test_dialogue_segmentation():
    """Test dialogue stream segmentation."""
    processor = SegmentProcessor()
    
    # Create dialogue-like audio
    sample_rate = 48000
    dialogue = []
    
    # Three utterances separated by silence
    dialogue.append(generate_test_audio(1.0, sample_rate, 200))  # "Hello"
    dialogue.append(generate_silence(0.5, sample_rate))
    dialogue.append(generate_test_audio(1.5, sample_rate, 250))  # "How are you?"
    dialogue.append(generate_silence(0.4, sample_rate))
    dialogue.append(generate_test_audio(0.8, sample_rate, 300))  # "Good!"
    
    audio_data = np.concatenate(dialogue)
    
    metadata = AudioMetadata(
        speaker_id="npc-test",
        speaker_role="npc",
        language_code="en-US",
        scene_id="test-scene"
    )
    
    # Process
    segments = await processor.process_dialogue_stream(
        audio_data, sample_rate, metadata
    )
    
    # Should get 3 dialogue segments
    assert len(segments) == 3
    
    # Verify segment properties
    assert all(s.segment_type == 'dialogue' for s in segments)
    assert all(s.metadata.speaker_id == "npc-test" for s in segments)
    
    # Check durations (approximate)
    assert abs(segments[0].duration_seconds - 1.0) < 0.1
    assert abs(segments[1].duration_seconds - 1.5) < 0.1
    assert abs(segments[2].duration_seconds - 0.8) < 0.1
    
    print("✓ Dialogue segmentation test passed")


async def test_ambient_segmentation():
    """Test ambient audio fixed-window segmentation."""
    processor = SegmentProcessor(fixed_window_duration=2.0)
    
    # Create 7 seconds of ambient audio
    sample_rate = 48000
    audio_data = generate_test_audio(7.0, sample_rate, 100)
    
    metadata = AudioMetadata(
        scene_id="forest",
        environment_type="dark_forest",
        bus_name="ambient_bus"
    )
    
    segments = await processor.process_ambient_stream(
        audio_data, sample_rate, metadata
    )
    
    # Should get 3 complete 2-second windows
    assert len(segments) == 3
    assert all(s.segment_type == 'ambient' for s in segments)
    assert all(abs(s.duration_seconds - 2.0) < 0.01 for s in segments)
    
    print("✓ Ambient segmentation test passed")


async def test_vocalization_segmentation():
    """Test monster vocalization segmentation."""
    processor = SegmentProcessor()
    
    sample_rate = 48000
    vocalization = []
    
    # Short bursts typical of monster sounds
    vocalization.append(generate_test_audio(0.2, sample_rate, 80))  # Growl
    vocalization.append(generate_silence(0.1, sample_rate))
    vocalization.append(generate_test_audio(0.3, sample_rate, 60))  # Roar
    vocalization.append(generate_silence(0.4, sample_rate))
    vocalization.append(generate_test_audio(0.1, sample_rate, 100))  # Hiss
    
    audio_data = np.concatenate(vocalization)
    
    metadata = AudioMetadata(
        speaker_id="monster-zombie-01",
        archetype_id="zombie_horde",
        simulator_applied=True
    )
    
    segments = await processor.process_vocalization_stream(
        audio_data, sample_rate, metadata
    )
    
    # Should get 3 vocalization segments
    assert len(segments) == 3
    assert all(s.segment_type == 'monster_vocalization' for s in segments)
    assert all(s.metadata.simulator_applied for s in segments)
    
    print("✓ Vocalization segmentation test passed")


async def test_metadata_enrichment():
    """Test metadata enrichment with game context."""
    processor = SegmentProcessor()
    
    # Create a simple segment
    segment = AudioSegment(
        segment_id="test-seg-001",
        segment_type="dialogue",
        audio_data=generate_test_audio(1.0),
        sample_rate=48000,
        timestamp_start=datetime.utcnow(),
        timestamp_end=datetime.utcnow(),
        metadata=AudioMetadata()
    )
    
    # Game context
    game_context = {
        "scene_id": "castle_throne_room",
        "line_id": "vampire_lord_intro_01",
        "speaker_info": {
            "id": "npc-vampire-lord",
            "role": "npc",
            "archetype_id": "vampire_house_alpha"
        },
        "emotional_context": "menacing",
        "current_quest": "find_the_artifact",
        "time_of_day": "midnight"
    }
    
    # Enrich
    enriched = await processor.enrich_metadata(segment, game_context)
    
    # Verify enrichment
    assert enriched.metadata.scene_id == "castle_throne_room"
    assert enriched.metadata.line_id == "vampire_lord_intro_01"
    assert enriched.metadata.speaker_id == "npc-vampire-lord"
    assert enriched.metadata.archetype_id == "vampire_house_alpha"
    assert enriched.metadata.emotional_tag == "menacing"
    assert enriched.metadata.additional["current_quest"] == "find_the_artifact"
    assert enriched.metadata.additional["time_of_day"] == "midnight"
    
    print("✓ Metadata enrichment test passed")


def test_audio_buffer():
    """Test audio buffer functionality."""
    sample_rate = 48000
    buffer = AudioBuffer(sample_rate, max_buffer_duration=5.0)
    
    # Add some audio
    chunk1 = generate_test_audio(1.0, sample_rate)
    chunk2 = generate_test_audio(2.0, sample_rate)
    chunk3 = generate_test_audio(3.0, sample_rate)  # This will exceed max
    
    buffer.add(chunk1)
    assert abs(buffer.get_duration() - 1.0) < 0.01
    
    buffer.add(chunk2)
    assert abs(buffer.get_duration() - 3.0) < 0.01
    
    buffer.add(chunk3)
    # Should have trimmed to stay under 5 seconds
    assert buffer.get_duration() <= 5.0
    assert buffer.get_duration() >= 4.9  # Should keep most recent data
    
    # Get all data
    all_data = buffer.get_all()
    assert all_data is not None
    assert len(all_data) == buffer.total_samples
    
    # Clear
    buffer.clear()
    assert buffer.get_duration() == 0.0
    assert buffer.get_all() is None
    
    print("✓ Audio buffer test passed")


async def test_stereo_audio():
    """Test handling of stereo audio."""
    processor = SegmentProcessor()
    
    sample_rate = 48000
    # Create stereo audio (2 channels)
    duration = 2.0
    t = np.linspace(0, duration, int(duration * sample_rate), False)
    left_channel = np.sin(2 * np.pi * 440 * t)  # 440 Hz
    right_channel = np.sin(2 * np.pi * 880 * t)  # 880 Hz
    stereo_audio = np.column_stack((left_channel, right_channel)).astype(np.float32)
    
    # Add silence in the middle
    silence_stereo = np.zeros((int(0.5 * sample_rate), 2), dtype=np.float32)
    audio_with_silence = np.vstack([
        stereo_audio[:int(0.8 * sample_rate)],
        silence_stereo,
        stereo_audio[int(0.8 * sample_rate):]
    ])
    
    metadata = AudioMetadata()
    segments = await processor.process_dialogue_stream(
        audio_with_silence, sample_rate, metadata
    )
    
    # Should handle stereo properly
    assert len(segments) >= 1
    for segment in segments:
        assert segment.channels == 2
    
    print("✓ Stereo audio test passed")


async def main():
    """Run all tests."""
    print("Running segment processor tests...")
    
    await test_silence_detection()
    await test_dialogue_segmentation()
    await test_ambient_segmentation()
    await test_vocalization_segmentation()
    await test_metadata_enrichment()
    test_audio_buffer()
    await test_stereo_audio()
    
    print("\nAll segment processor tests passed! ✅")


if __name__ == "__main__":
    asyncio.run(main())
