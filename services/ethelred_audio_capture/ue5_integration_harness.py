"""
UE5 Integration Test Harness
Simulates audio routing from UE5 for development and testing
"""
import asyncio
import numpy as np
import aiohttp
import base64
import json
import logging
from datetime import datetime
from typing import Optional, Dict, List
from pathlib import Path
import wave


logger = logging.getLogger(__name__)


class DialogueLine:
    """Represents a dialogue line with timing."""
    def __init__(self, line_id: str, speaker_id: str, archetype_id: str,
                 text: str, audio_file: Optional[str] = None,
                 duration: float = 2.0, emotional_tag: str = "neutral"):
        self.line_id = line_id
        self.speaker_id = speaker_id
        self.archetype_id = archetype_id
        self.text = text
        self.audio_file = audio_file
        self.duration = duration
        self.emotional_tag = emotional_tag


class UE5AudioSimulator:
    """Simulates UE5 audio routing for testing."""
    
    def __init__(self, capture_service_url: str = "http://localhost:8089"):
        self.capture_service_url = capture_service_url
        self.session = None
        self.active_streams = {}
        
        # Test scenario data
        self.test_scenes = self._create_test_scenes()
    
    def _create_test_scenes(self) -> Dict[str, List[DialogueLine]]:
        """Create test dialogue scenarios."""
        return {
            "castle_entrance": [
                DialogueLine(
                    "castle_intro_01",
                    "npc_vampire_lord",
                    "vampire_house_alpha",
                    "Welcome to my domain, mortal...",
                    duration=3.0,
                    emotional_tag="menacing"
                ),
                DialogueLine(
                    "castle_intro_02",
                    "npc_vampire_lord",
                    "vampire_house_alpha",
                    "You dare enter uninvited?",
                    duration=2.5,
                    emotional_tag="anger"
                ),
                DialogueLine(
                    "castle_intro_03",
                    "narrator",
                    None,
                    "The ancient vampire's eyes glow with an otherworldly light.",
                    duration=3.5,
                    emotional_tag="ominous"
                )
            ],
            "zombie_encounter": [
                DialogueLine(
                    "zombie_growl_01",
                    "zombie_01",
                    "zombie_horde",
                    "*growling sounds*",
                    duration=1.5,
                    emotional_tag="aggressive"
                ),
                DialogueLine(
                    "zombie_growl_02",
                    "zombie_02",
                    "zombie_horde",
                    "*moaning sounds*",
                    duration=2.0,
                    emotional_tag="hungry"
                )
            ]
        }
    
    async def connect(self):
        """Connect to the capture service."""
        self.session = aiohttp.ClientSession()
        
        # Test connection
        try:
            async with self.session.get(f"{self.capture_service_url}/health") as resp:
                if resp.status == 200:
                    logger.info("Connected to audio capture service")
                else:
                    logger.error(f"Failed to connect: {resp.status}")
        except Exception as e:
            logger.error(f"Connection error: {e}")
            raise
    
    async def create_audio_bus(self, bus_name: str, scene_id: str) -> str:
        """Create an audio stream for a bus."""
        data = {
            "bus_name": bus_name,
            "sample_rate": 48000,
            "scene_id": scene_id
        }
        
        async with self.session.post(
            f"{self.capture_service_url}/streams/create",
            json=data
        ) as resp:
            result = await resp.json()
            stream_id = result["stream_id"]
            self.active_streams[bus_name] = stream_id
            logger.info(f"Created stream {stream_id} for bus {bus_name}")
            return stream_id
    
    def generate_dialogue_audio(self, duration: float, speaker_type: str) -> np.ndarray:
        """Generate simulated dialogue audio based on speaker type."""
        sample_rate = 48000
        t = np.linspace(0, duration, int(duration * sample_rate))
        
        if speaker_type == "vampire":
            # Deep, resonant voice
            base_freq = 90
            harmonics = [1.0, 0.5, 0.3, 0.2]
        elif speaker_type == "zombie":
            # Rough, low growl
            base_freq = 60
            harmonics = [1.0, 0.8, 0.6, 0.9]
        elif speaker_type == "narrator":
            # Clear, mid-range voice
            base_freq = 150
            harmonics = [1.0, 0.3, 0.1, 0.05]
        else:
            # Default human voice
            base_freq = 120
            harmonics = [1.0, 0.4, 0.2, 0.1]
        
        # Generate harmonics
        audio = np.zeros_like(t)
        for i, h in enumerate(harmonics):
            audio += h * np.sin(2 * np.pi * base_freq * (i + 1) * t)
        
        # Add some envelope
        envelope = np.exp(-0.5 * t) * (1 - t / duration)
        audio *= envelope
        
        # Add slight noise for realism
        audio += 0.01 * np.random.randn(len(t))
        
        # Normalize
        audio = audio / np.max(np.abs(audio)) * 0.8
        
        return audio.astype(np.float32)
    
    def generate_ambient_audio(self, duration: float, environment: str) -> np.ndarray:
        """Generate ambient environment audio."""
        sample_rate = 48000
        samples = int(duration * sample_rate)
        
        if environment == "castle":
            # Low frequency rumble + occasional high frequency
            rumble = 0.1 * np.random.randn(samples)
            rumble = np.convolve(rumble, np.ones(100)/100, mode='same')  # Low-pass
            
            # Add occasional creaks
            creaks = np.zeros(samples)
            for _ in range(int(duration * 2)):  # 2 creaks per second
                pos = np.random.randint(0, samples - 1000)
                t = np.linspace(0, 0.02, 1000)
                creak = 0.05 * np.sin(2 * np.pi * np.random.uniform(2000, 4000) * t) * np.exp(-50 * t)
                creaks[pos:pos + 1000] += creak
            
            audio = rumble + creaks
            
        elif environment == "graveyard":
            # Wind-like noise
            wind = 0.15 * np.random.randn(samples)
            wind = np.convolve(wind, np.ones(500)/500, mode='same')  # Heavy low-pass
            
            # Occasional howls
            howls = np.zeros(samples)
            for _ in range(int(duration * 0.5)):  # 0.5 howls per second
                pos = np.random.randint(0, samples - 10000)
                t = np.linspace(0, 0.2, 10000)
                howl = 0.1 * np.sin(2 * np.pi * np.random.uniform(300, 500) * t) * np.exp(-5 * t)
                howls[pos:pos + 10000] += howl
            
            audio = wind + howls
            
        else:
            # Generic ambient noise
            audio = 0.05 * np.random.randn(samples)
            audio = np.convolve(audio, np.ones(200)/200, mode='same')
        
        return audio.astype(np.float32)
    
    async def send_audio_data(self, stream_id: str, audio_data: np.ndarray,
                            game_context: Optional[Dict] = None):
        """Send audio data to capture service."""
        # Convert to base64
        audio_bytes = (audio_data * 32767).astype(np.int16).tobytes()
        audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
        
        data = {
            "stream_id": stream_id,
            "audio_data_base64": audio_base64,
            "game_context": game_context or {}
        }
        
        async with self.session.post(
            f"{self.capture_service_url}/streams/feed",
            json=data
        ) as resp:
            if resp.status != 200:
                logger.error(f"Failed to send audio: {resp.status}")
    
    async def play_dialogue_line(self, line: DialogueLine, scene_id: str):
        """Simulate playing a dialogue line."""
        logger.info(f"Playing line: {line.line_id} - '{line.text}'")
        
        # Determine speaker type for audio generation
        if "vampire" in line.speaker_id:
            speaker_type = "vampire"
        elif "zombie" in line.speaker_id:
            speaker_type = "zombie"
        elif line.speaker_id == "narrator":
            speaker_type = "narrator"
        else:
            speaker_type = "human"
        
        # Generate audio
        audio_data = self.generate_dialogue_audio(line.duration, speaker_type)
        
        # Send pre-roll marker (100ms before audio)
        await asyncio.sleep(0.1)
        
        # Send audio with context
        context = {
            "line_id": line.line_id,
            "speaker_info": {
                "id": line.speaker_id,
                "role": "narrator" if line.speaker_id == "narrator" else "npc",
                "archetype_id": line.archetype_id
            },
            "emotional_context": line.emotional_tag,
            "scene_id": scene_id,
            "experience_id": "test_experience",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # If simulator should be applied
        if line.archetype_id in ["vampire_house_alpha", "zombie_horde"]:
            # Send to pre-simulator bus
            if "vocal_pre" in self.active_streams:
                await self.send_audio_data(
                    self.active_streams["vocal_pre"],
                    audio_data,
                    context
                )
            
            # Simulate vocal processing
            processed_audio = self.apply_vocal_simulator(audio_data, line.archetype_id)
            
            # Send to post-simulator bus
            if "vocal_post" in self.active_streams:
                context["simulator_applied"] = True
                await self.send_audio_data(
                    self.active_streams["vocal_post"],
                    processed_audio,
                    context
                )
        
        # Always send to dialogue bus
        if "dialogue" in self.active_streams:
            await self.send_audio_data(
                self.active_streams["dialogue"],
                audio_data,
                context
            )
        
        # Simulate playback time
        await asyncio.sleep(line.duration)
        
        # Post-roll (300ms after audio)
        await asyncio.sleep(0.3)
    
    def apply_vocal_simulator(self, audio: np.ndarray, archetype: str) -> np.ndarray:
        """Simulate vocal cord processing for monsters."""
        if archetype == "vampire_house_alpha":
            # Add slight pitch shift and reverb
            processed = audio * 0.8
            # Simple echo effect
            delay_samples = int(0.05 * 48000)  # 50ms delay
            echo = np.zeros(len(audio) + delay_samples)
            echo[:len(audio)] = processed
            echo[delay_samples:] += processed * 0.3
            return echo[:len(audio)]
        
        elif archetype == "zombie_horde":
            # Add distortion and roughness
            processed = np.tanh(audio * 3) * 0.7  # Soft clipping
            # Add low frequency modulation
            t = np.arange(len(audio)) / 48000
            modulation = 1 + 0.3 * np.sin(2 * np.pi * 5 * t)  # 5 Hz tremolo
            return processed * modulation
        
        return audio
    
    async def run_scene(self, scene_name: str):
        """Run a complete scene with dialogue."""
        if scene_name not in self.test_scenes:
            logger.error(f"Unknown scene: {scene_name}")
            return
        
        logger.info(f"Starting scene: {scene_name}")
        
        # Create audio buses
        await self.create_audio_bus("dialogue", scene_name)
        await self.create_audio_bus("vocal_pre", scene_name)
        await self.create_audio_bus("vocal_post", scene_name)
        await self.create_audio_bus("ambient", scene_name)
        await self.create_audio_bus("main_mix", scene_name)
        
        # Start ambient audio
        environment = "castle" if "castle" in scene_name else "graveyard"
        ambient_task = asyncio.create_task(
            self.play_ambient_loop(environment, scene_name)
        )
        
        # Play dialogue lines
        lines = self.test_scenes[scene_name]
        for line in lines:
            await self.play_dialogue_line(line, scene_name)
            await asyncio.sleep(0.5)  # Pause between lines
        
        # Stop ambient
        ambient_task.cancel()
        try:
            await ambient_task
        except asyncio.CancelledError:
            pass
        
        # Close streams
        await self.close_all_streams()
        
        logger.info(f"Scene complete: {scene_name}")
    
    async def play_ambient_loop(self, environment: str, scene_id: str):
        """Play continuous ambient audio."""
        stream_id = self.active_streams.get("ambient")
        if not stream_id:
            return
        
        context = {
            "scene_id": scene_id,
            "environment_type": environment
        }
        
        try:
            while True:
                # Generate 5 seconds of ambient audio
                audio = self.generate_ambient_audio(5.0, environment)
                await self.send_audio_data(stream_id, audio, context)
                await asyncio.sleep(4.9)  # Small overlap
        except asyncio.CancelledError:
            pass
    
    async def close_all_streams(self):
        """Close all active streams."""
        for bus_name, stream_id in self.active_streams.items():
            async with self.session.post(
                f"{self.capture_service_url}/streams/{stream_id}/close"
            ) as resp:
                if resp.status == 200:
                    logger.info(f"Closed stream for {bus_name}")
        
        self.active_streams.clear()
    
    async def disconnect(self):
        """Disconnect from capture service."""
        if self.session:
            await self.session.close()


async def main():
    """Run test scenarios."""
    # Initialize simulator
    simulator = UE5AudioSimulator()
    
    try:
        await simulator.connect()
        
        # Run test scenes
        logger.info("Running castle entrance scene...")
        await simulator.run_scene("castle_entrance")
        
        await asyncio.sleep(2)
        
        logger.info("Running zombie encounter scene...")
        await simulator.run_scene("zombie_encounter")
        
    finally:
        await simulator.disconnect()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    asyncio.run(main())

