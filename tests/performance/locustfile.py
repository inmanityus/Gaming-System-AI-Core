"""
Locust load testing configuration for Gaming System APIs.
Tests API endpoints under various load scenarios.
"""
from locust import HttpUser, task, between, events
from locust.env import Environment
from locust.stats import stats_printer, stats_history
import json
import random
import numpy as np
from datetime import datetime, timezone
import base64
import hashlib
import time


def generate_audio_data(duration_seconds=3, sample_rate=48000):
    """Generate synthetic audio data for testing."""
    t = np.linspace(0, duration_seconds, int(sample_rate * duration_seconds))
    # Simple speech-like signal
    f0 = 150 + 50 * np.sin(2 * np.pi * 0.5 * t)
    signal = np.sin(2 * np.pi * f0 * t)
    # Add some noise
    signal += 0.1 * np.random.randn(len(t))
    # Convert to 16-bit PCM
    audio_bytes = (signal * 32767).astype(np.int16).tobytes()
    return base64.b64encode(audio_bytes).decode('utf-8')


class AudioAnalysisUser(HttpUser):
    """User that submits audio for analysis."""
    
    wait_time = between(1, 3)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_id = f"load_test_user_{random.randint(1000, 9999)}"
        self.audio_cache = {}
    
    def on_start(self):
        """Called when user starts."""
        # Pre-generate some audio samples
        self.audio_cache = {
            'short': generate_audio_data(1),
            'medium': generate_audio_data(3),
            'long': generate_audio_data(5)
        }
        
        # Set user preferences
        self.client.put(
            f"/api/v1/users/{self.user_id}/preferences",
            json={
                "language_code": random.choice(["en-US", "ja-JP", "es-ES", "zh-CN"]),
                "audio_settings": {
                    "volume": 0.8,
                    "voice_type": random.choice(["male", "female"])
                }
            },
            name="/api/v1/users/[user_id]/preferences"
        )
    
    @task(3)
    def analyze_intelligibility(self):
        """Submit audio for intelligibility analysis."""
        audio_type = random.choice(['short', 'medium', 'long'])
        
        response = self.client.post(
            "/api/v1/audio/analyze/intelligibility",
            json={
                "audio_data": self.audio_cache[audio_type],
                "sample_rate": 48000,
                "user_id": self.user_id,
                "audio_file_path": f"/test/{audio_type}_audio.wav"
            },
            name="/api/v1/audio/analyze/intelligibility"
        )
        
        if response.status_code == 200:
            result = response.json()
            # Track custom metrics
            events.request_success.fire(
                request_type="AUDIO_SCORE",
                name="intelligibility_score",
                response_time=result.get('score', 0),
                response_length=0
            )
    
    @task(2)
    def analyze_archetype(self):
        """Submit audio for archetype analysis."""
        archetypes = ["vampire_alpha", "human_agent", "corpse_tender", "werewolf_beta"]
        
        response = self.client.post(
            "/api/v1/audio/analyze/archetype",
            json={
                "audio_data": self.audio_cache['medium'],
                "sample_rate": 48000,
                "user_id": self.user_id,
                "expected_archetype": random.choice(archetypes)
            },
            name="/api/v1/audio/analyze/archetype"
        )
    
    @task(1)
    def get_user_metrics(self):
        """Get user's audio metrics."""
        self.client.get(
            f"/api/v1/audio/metrics/user/{self.user_id}",
            name="/api/v1/audio/metrics/user/[user_id]"
        )


class EngagementTrackingUser(HttpUser):
    """User that plays game sessions."""
    
    wait_time = between(2, 5)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_id = f"engagement_user_{random.randint(1000, 9999)}"
        self.session_id = None
        self.session_start = None
    
    def on_start(self):
        """Start a gaming session."""
        self.start_session()
    
    def on_stop(self):
        """End gaming session."""
        if self.session_id:
            self.end_session()
    
    def start_session(self):
        """Start a new gaming session."""
        self.session_start = datetime.now(timezone.utc)
        
        response = self.client.post(
            "/api/v1/engagement/session/start",
            json={
                "user_id": self.user_id,
                "timestamp": self.session_start.isoformat()
            },
            name="/api/v1/engagement/session/start"
        )
        
        if response.status_code == 200:
            self.session_id = response.json().get("session_id")
    
    def end_session(self):
        """End current gaming session."""
        if not self.session_id:
            return
        
        self.client.post(
            f"/api/v1/engagement/session/{self.session_id}/end",
            json={
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "reason": random.choice(["player_quit", "timeout", "completed"])
            },
            name="/api/v1/engagement/session/[session_id]/end"
        )
        
        self.session_id = None
    
    @task(5)
    def send_game_event(self):
        """Send a game event."""
        if not self.session_id:
            self.start_session()
            return
        
        event_types = [
            {"type": "level_start", "level": random.randint(1, 10)},
            {"type": "enemy_killed", "enemy_type": random.choice(["vampire", "zombie", "werewolf"])},
            {"type": "item_collected", "item": random.choice(["health", "ammo", "key"])},
            {"type": "death", "cause": random.choice(["combat", "fall", "trap"])},
            {"type": "checkpoint", "id": random.randint(1, 5)}
        ]
        
        event = random.choice(event_types)
        event["timestamp"] = datetime.now(timezone.utc).isoformat()
        
        self.client.post(
            f"/api/v1/engagement/session/{self.session_id}/event",
            json=event,
            name="/api/v1/engagement/session/[session_id]/event"
        )
    
    @task(1)
    def get_addiction_indicators(self):
        """Check addiction indicators."""
        self.client.get(
            f"/api/v1/engagement/analysis/addiction/{self.user_id}",
            name="/api/v1/engagement/analysis/addiction/[user_id]"
        )
    
    @task(1)
    def restart_session(self):
        """End current session and start new one."""
        if self.session_id and random.random() < 0.3:  # 30% chance
            self.end_session()
            time.sleep(random.uniform(0.5, 2))
            self.start_session()


class LocalizationUser(HttpUser):
    """User that requests localized content."""
    
    wait_time = between(0.5, 2)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.languages = ["en-US", "ja-JP", "es-ES", "zh-CN", "ko-KR", "de-DE", "fr-FR"]
        self.language = random.choice(self.languages)
    
    @task(10)
    def get_ui_content(self):
        """Get UI localized content."""
        ui_keys = [
            "ui.menu.play",
            "ui.menu.settings",
            "ui.button.confirm",
            "ui.button.cancel",
            "ui.settings.audio",
            "ui.settings.video"
        ]
        
        self.client.get(
            "/api/v1/localization/content",
            params={
                "key": random.choice(ui_keys),
                "language": self.language
            },
            name="/api/v1/localization/content"
        )
    
    @task(5)
    def get_dialogue_content(self):
        """Get dialogue content."""
        dialogue_keys = [
            f"dialogue.npc.greeting_{i}" for i in range(1, 20)
        ] + [
            f"dialogue.quest.description_{i}" for i in range(1, 10)
        ]
        
        self.client.get(
            "/api/v1/localization/content",
            params={
                "key": random.choice(dialogue_keys),
                "language": self.language
            },
            name="/api/v1/localization/content"
        )
    
    @task(2)
    def get_language_stats(self):
        """Get language statistics."""
        self.client.get(
            f"/api/v1/localization/languages/{self.language}/stats",
            name="/api/v1/localization/languages/[language]/stats"
        )
    
    @task(1)
    def request_tts(self):
        """Request TTS synthesis."""
        texts = [
            "Welcome to the game!",
            "You have died.",
            "Level complete!",
            "New quest available."
        ]
        
        response = self.client.post(
            "/api/v1/tts/synthesize",
            json={
                "text": random.choice(texts),
                "language": self.language,
                "voice_id": f"{self.language}-Standard-A"
            },
            name="/api/v1/tts/synthesize"
        )


class MixedBehaviorUser(HttpUser):
    """User with mixed behavior patterns."""
    
    wait_time = between(1, 5)
    tasks = [AudioAnalysisUser, EngagementTrackingUser, LocalizationUser]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_id = f"mixed_user_{random.randint(10000, 99999)}"


# Custom event handlers for additional metrics
@events.init.add_listener
def on_locust_init(environment, **kwargs):
    """Initialize custom metrics tracking."""
    if environment.parsed_options and environment.parsed_options.master:
        # Custom stats aggregation for master node
        pass


@events.request_success.add_listener
def on_request_success(request_type, name, response_time, response_length, **kwargs):
    """Track successful requests."""
    # Could add custom metric tracking here
    pass


@events.request_failure.add_listener  
def on_request_failure(request_type, name, response_time, response_length, exception, **kwargs):
    """Track failed requests."""
    # Log failures for analysis
    pass


# Scenario configurations
class QuickLoadTest(HttpUser):
    """Quick load test scenario - 5 minute ramp."""
    wait_time = between(1, 2)
    tasks = [AudioAnalysisUser, LocalizationUser]


class SustainedLoadTest(HttpUser):
    """Sustained load test - 30 minutes steady state."""
    wait_time = between(2, 4)
    tasks = [MixedBehaviorUser]


class StressTest(HttpUser):
    """Stress test - find breaking point."""
    wait_time = between(0.1, 0.5)
    
    @task
    def hammer_endpoints(self):
        """Rapidly hit various endpoints."""
        endpoints = [
            ("/api/v1/audio/analyze/intelligibility", "POST"),
            ("/api/v1/engagement/session/start", "POST"),
            ("/api/v1/localization/content?key=ui.test&language=en-US", "GET"),
        ]
        
        endpoint, method = random.choice(endpoints)
        
        if method == "GET":
            self.client.get(endpoint)
        else:
            # Minimal valid payload
            self.client.post(endpoint, json={"user_id": "stress_test"})


# Load patterns for different scenarios
"""
Quick Smoke Test:
locust -f locustfile.py --host=http://localhost:8000 --users 10 --spawn-rate 2 --run-time 5m

Standard Load Test:
locust -f locustfile.py --host=http://localhost:8000 --users 100 --spawn-rate 5 --run-time 30m

Stress Test:
locust -f locustfile.py --host=http://localhost:8000 --users 1000 --spawn-rate 50 --run-time 15m

Spike Test:
locust -f locustfile.py --host=http://localhost:8000 --users 10 --spawn-rate 1
# Then manually spike to 500 users via UI

Soak Test:
locust -f locustfile.py --host=http://localhost:8000 --users 200 --spawn-rate 10 --run-time 2h
"""
