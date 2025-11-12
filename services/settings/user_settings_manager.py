"""
User Settings Manager
====================

Manages user-facing settings (audio, video, controls, accessibility).
Extends the existing ConfigManager for game configuration.
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List
from pathlib import Path

from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


@dataclass
class AudioSettings:
    """Audio settings configuration."""
    master_volume: float = 1.0
    music_volume: float = 0.8
    sfx_volume: float = 1.0
    voice_volume: float = 1.0
    audio_quality: str = "medium"  # low, medium, high
    subtitle_language: str = "common"
    show_original_language: bool = False
    
    @validator('master_volume', 'music_volume', 'sfx_volume', 'voice_volume')
    def validate_volume(cls, v):
        """Validate volume is between 0.0 and 1.0."""
        return max(0.0, min(1.0, v))


@dataclass
class VideoSettings:
    """Video settings configuration."""
    resolution_x: int = 1920
    resolution_y: int = 1080
    quality_preset: str = "medium"  # low, medium, high, ultra
    window_mode: str = "fullscreen"  # windowed, fullscreen, borderless
    vsync: bool = True
    frame_rate_limit: int = 60  # 30, 60, 120, 0 (unlimited)
    lumen_enabled: bool = True
    nanite_enabled: bool = True
    ray_tracing_enabled: bool = False
    shadow_quality: str = "medium"
    texture_quality: str = "medium"
    post_processing: bool = True


@dataclass
class ControlsSettings:
    """Controls settings configuration."""
    mouse_sensitivity: float = 1.0
    mouse_smoothing: bool = False
    invert_y_axis: bool = False
    key_bindings: Dict[str, str] = field(default_factory=dict)
    controller_enabled: bool = False


@dataclass
class AccessibilitySettings:
    """Accessibility settings configuration."""
    screen_reader_enabled: bool = False
    high_contrast_mode: bool = False
    text_scaling: float = 1.0
    color_blind_mode: str = "none"  # none, protanopia, deuteranopia, tritanopia
    motion_sensitivity: float = 1.0
    subtitles_enabled: bool = True
    subtitles_always_on: bool = False


class UserSettingsManager:
    """Manages user-facing settings."""
    
    def __init__(self, settings_path: str = "config/user_settings.json"):
        """Initialize user settings manager."""
        self.settings_path = Path(settings_path)
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.audio_settings = AudioSettings()
        self.video_settings = VideoSettings()
        self.controls_settings = ControlsSettings()
        self.accessibility_settings = AccessibilitySettings()
        
        self._load_settings()
    
    def _load_settings(self):
        """Load settings from file."""
        if self.settings_path.exists():
            try:
                with open(self.settings_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    if "audio" in data:
                        self.audio_settings = AudioSettings(**data["audio"])
                    if "video" in data:
                        self.video_settings = VideoSettings(**data["video"])
                    if "controls" in data:
                        self.controls_settings = ControlsSettings(**data["controls"])
                    if "accessibility" in data:
                        self.accessibility_settings = AccessibilitySettings(**data["accessibility"])
            except Exception as e:
                logger.error(f"Error loading settings: {e}")
                # Use defaults
    
    def save_settings(self):
        """Save settings to file."""
        data = {
            "audio": asdict(self.audio_settings),
            "video": asdict(self.video_settings),
            "controls": asdict(self.controls_settings),
            "accessibility": asdict(self.accessibility_settings),
        }
        
        try:
            with open(self.settings_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            logger.info("Settings saved successfully")
            return True
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            return False
    
    def apply_audio_settings(self, settings: Dict[str, Any]):
        """Apply audio settings."""
        for key, value in settings.items():
            if hasattr(self.audio_settings, key):
                setattr(self.audio_settings, key, value)
        self.save_settings()
    
    def apply_video_settings(self, settings: Dict[str, Any]):
        """Apply video settings."""
        for key, value in settings.items():
            if hasattr(self.video_settings, key):
                setattr(self.video_settings, key, value)
        self.save_settings()
    
    def apply_controls_settings(self, settings: Dict[str, Any]):
        """Apply controls settings."""
        for key, value in settings.items():
            if hasattr(self.controls_settings, key):
                setattr(self.controls_settings, key, value)
        self.save_settings()
    
    def apply_accessibility_settings(self, settings: Dict[str, Any]):
        """Apply accessibility settings."""
        for key, value in settings.items():
            if hasattr(self.accessibility_settings, key):
                setattr(self.accessibility_settings, key, value)
        self.save_settings()
    
    def reset_to_defaults(self, category: Optional[str] = None):
        """Reset settings to defaults."""
        if category is None or category == "audio":
            self.audio_settings = AudioSettings()
        if category is None or category == "video":
            self.video_settings = VideoSettings()
        if category is None or category == "controls":
            self.controls_settings = ControlsSettings()
        if category is None or category == "accessibility":
            self.accessibility_settings = AccessibilitySettings()
        
        self.save_settings()
    
    def get_settings_dict(self) -> Dict[str, Any]:
        """Get all settings as dictionary."""
        return {
            "audio": asdict(self.audio_settings),
            "video": asdict(self.video_settings),
            "controls": asdict(self.controls_settings),
            "accessibility": asdict(self.accessibility_settings),
        }






