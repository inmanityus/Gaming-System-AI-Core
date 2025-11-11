#!/usr/bin/env python3
"""Test Python bindings for vocal_synthesis library"""

import numpy as np
import vocal_synthesis as vs

def test_audio_buffer():
    """Test AudioBuffer basics"""
    buf = vs.AudioBuffer(48000, 1)
    buf.resize(1000)
    assert buf.size() == 1000
    assert buf.num_frames() == 1000
    print("✓ AudioBuffer basic operations")

def test_archetypes():
    """Test archetype presets"""
    human = vs.AberrationParams.create_human()
    vampire = vs.AberrationParams.create_vampire()
    zombie = vs.AberrationParams.create_zombie()
    werewolf = vs.AberrationParams.create_werewolf()
    wraith = vs.AberrationParams.create_wraith()
    
    print(f"✓ Human archetype: {human.get_archetype()}")
    print(f"✓ Vampire archetype: {vampire.get_archetype()}")
    print(f"✓ Zombie archetype: {zombie.get_archetype()}")
    print(f"✓ Werewolf archetype: {werewolf.get_archetype()}")
    print(f"✓ Wraith archetype: {wraith.get_archetype()}")

def test_glottal_incoherence():
    """Test Glottal Incoherence (Zombie)"""
    effect = vs.GlottalIncoherence(48000, 42)
    
    # Test dynamic intensity
    effect.set_dynamic_intensity(0.6, 0.8, 0.7)  # base, proximity, environment
    
    # Generate test audio
    audio = np.sin(2 * np.pi * 440 * np.arange(48000) / 48000).astype(np.float32)
    effect.process_in_place(audio)
    
    print("✓ GlottalIncoherence with dynamic intensity")

def test_subharmonic_generator():
    """Test Subharmonic Generator (Werewolf)"""
    effect = vs.SubharmonicGenerator(48000)
    effect.set_intensity(0.7)
    effect.set_chaos(0.5)
    effect.set_transformation_struggle(0.6)
    
    # Generate test audio
    audio = np.sin(2 * np.pi * 440 * np.arange(48000) / 48000).astype(np.float32)
    effect.process_in_place(audio)
    
    print("✓ SubharmonicGenerator with transformation struggle")

def test_subliminal_audio():
    """Test Subliminal Audio (Vampire)"""
    effect = vs.SubliminalAudio(48000)
    effect.set_layer(vs.SubliminalLayerType.HEARTBEAT, 0.08)
    effect.set_layer(vs.SubliminalLayerType.BLOOD_FLOW, 0.05)
    effect.set_heartbeat_rate(72.0)
    
    # Generate test audio
    audio = np.sin(2 * np.pi * 440 * np.arange(48000) / 48000).astype(np.float32)
    effect.process_in_place(audio)
    
    print("✓ SubliminalAudio with heartbeat and blood flow")

def test_emotion_system():
    """Test emotion modulation"""
    fear = vs.EmotionState.from_named(vs.NamedEmotion.FEAR)
    anger = vs.EmotionState.from_named(vs.NamedEmotion.ANGER)
    
    base_params = vs.AberrationParams.create_zombie()
    fearful_zombie = fear.apply_to(base_params)
    angry_zombie = anger.apply_to(base_params)
    
    print("✓ Emotion modulation (Fear + Anger on Zombie)")

if __name__ == "__main__":
    print("Testing Vocal Synthesis Python Bindings...")
    print()
    
    test_audio_buffer()
    test_archetypes()
    test_glottal_incoherence()
    test_subharmonic_generator()
    test_subliminal_audio()
    test_emotion_system()
    
    print()
    print("✅ All Python binding tests passed!")

