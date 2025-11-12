# CROSS-SERVICE IMPORTS DISABLED IN DOCKER CONTAINER
"""
Mode Manager - Core implementation for Dual-Mode Performance Architecture.

Implements REQ-PERF-001: Dual-Mode Performance Architecture.
"""

import logging
import time
import asyncio
from typing import Any, Dict, Optional
from enum import Enum
from dataclasses import dataclass, field
from threading import Lock

# Import PerformanceMode from budget_monitor to avoid duplication
try:
    from services.performance_budget.budget_monitor import PerformanceMode
except ImportError:
    # Fallback if budget_monitor not available
    class PerformanceMode(Enum):
        """Performance mode enumeration."""
        IMMERSIVE = "immersive"      # 60-120 FPS target
        COMPETITIVE = "competitive"   # 300+ FPS target

_logger = logging.getLogger(__name__)


class ModePreset(Enum):
    """Performance preset enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    ULTRA = "ultra"
    COMPETITIVE = "competitive"


@dataclass
class RenderingConfig:
    """Rendering quality configuration for a performance mode."""
    # Lumen (Global Illumination)
    lumen_enabled: bool = False
    lumen_quality: str = "low"  # "low", "medium", "high", "epic"
    
    # Nanite (Virtualized Geometry)
    nanite_enabled: bool = True
    nanite_max_pixels_per_edge: int = 4  # Lower = more aggressive
    
    # Volumetrics
    volumetrics_enabled: bool = False
    volumetric_fog_density: float = 0.0
    
    # Shadows
    shadow_quality: str = "low"  # "low", "medium", "high", "epic"
    max_shadow_casting_lights: int = 1
    shadow_resolution: int = 512  # 512, 1024, 2048
    
    # Post-processing
    post_processing_enabled: bool = True
    post_processing_quality: str = "low"  # "low", "medium", "high", "epic"
    
    # Audio
    audio_virtualization_enabled: bool = False
    audio_quality: str = "low"  # "low", "medium", "high", "epic"
    
    # AI/NPC
    ai_update_rate_hz: float = 10.0  # Higher = more frequent updates
    max_active_npcs: int = 50
    
    # Environmental
    environmental_storytelling_enabled: bool = False
    detail_density: float = 0.3  # 0.0-1.0
    
    # Culling
    culling_aggressiveness: float = 0.9  # 0.0-1.0, higher = more aggressive
    lod_bias: float = 2.0  # Higher = prefer lower LODs
    
    # Upscaling
    upscaling_enabled: bool = True
    upscaling_method: str = "fsr"  # "dlss", "fsr", "xess"
    upscaling_quality: str = "ultra_performance"
    internal_resolution_scale: float = 0.5  # 0.5 = 720p for 1080p output
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "lumen_enabled": self.lumen_enabled,
            "lumen_quality": self.lumen_quality,
            "nanite_enabled": self.nanite_enabled,
            "nanite_max_pixels_per_edge": self.nanite_max_pixels_per_edge,
            "volumetrics_enabled": self.volumetrics_enabled,
            "volumetric_fog_density": self.volumetric_fog_density,
            "shadow_quality": self.shadow_quality,
            "max_shadow_casting_lights": self.max_shadow_casting_lights,
            "shadow_resolution": self.shadow_resolution,
            "post_processing_enabled": self.post_processing_enabled,
            "post_processing_quality": self.post_processing_quality,
            "audio_virtualization_enabled": self.audio_virtualization_enabled,
            "audio_quality": self.audio_quality,
            "ai_update_rate_hz": self.ai_update_rate_hz,
            "max_active_npcs": self.max_active_npcs,
            "environmental_storytelling_enabled": self.environmental_storytelling_enabled,
            "detail_density": self.detail_density,
            "culling_aggressiveness": self.culling_aggressiveness,
            "lod_bias": self.lod_bias,
            "upscaling_enabled": self.upscaling_enabled,
            "upscaling_method": self.upscaling_method,
            "upscaling_quality": self.upscaling_quality,
            "internal_resolution_scale": self.internal_resolution_scale,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RenderingConfig":
        """Create from dictionary."""
        return cls(**data)


class ModeTransitionError(Exception):
    """Raised when mode transition fails."""
    pass


class ModeManager:
    """Manages performance mode switching and configuration."""
    
    def __init__(self):
        self._current_mode: PerformanceMode = PerformanceMode.IMMERSIVE
        self._current_preset: ModePreset = ModePreset.MEDIUM
        self._lock = Lock()  # For sync operations
        self._async_lock = asyncio.Lock()  # For async operations
        self._last_mode_change: float = time.time()
        self._mode_change_cooldown: float = 1.0  # 1 second cooldown
        self._previous_mode: Optional[PerformanceMode] = None  # For rollback
        
        # Immersive mode configuration (60-120 FPS)
        self._immersive_config = RenderingConfig(
            lumen_enabled=True,
            lumen_quality="high",
            nanite_enabled=True,
            nanite_max_pixels_per_edge=2,
            volumetrics_enabled=True,
            volumetric_fog_density=0.5,
            shadow_quality="high",
            max_shadow_casting_lights=4,
            shadow_resolution=2048,
            post_processing_enabled=True,
            post_processing_quality="high",
            audio_virtualization_enabled=True,
            audio_quality="high",
            ai_update_rate_hz=2.0,
            max_active_npcs=100,
            environmental_storytelling_enabled=True,
            detail_density=1.0,
            culling_aggressiveness=0.3,
            lod_bias=0.0,
            upscaling_enabled=False,
            upscaling_method="fsr",
            upscaling_quality="quality",
            internal_resolution_scale=1.0,
        )
        
        # Competitive mode configuration (300+ FPS)
        self._competitive_config = RenderingConfig(
            lumen_enabled=False,
            lumen_quality="low",
            nanite_enabled=True,
            nanite_max_pixels_per_edge=4,
            volumetrics_enabled=False,
            volumetric_fog_density=0.0,
            shadow_quality="low",
            max_shadow_casting_lights=1,
            shadow_resolution=512,
            post_processing_enabled=True,
            post_processing_quality="low",
            audio_virtualization_enabled=False,
            audio_quality="low",
            ai_update_rate_hz=10.0,
            max_active_npcs=50,
            environmental_storytelling_enabled=False,
            detail_density=0.3,
            culling_aggressiveness=0.9,
            lod_bias=2.0,
            upscaling_enabled=True,
            upscaling_method="fsr",
            upscaling_quality="ultra_performance",
            internal_resolution_scale=0.5,
        )
    
    def get_current_mode(self) -> PerformanceMode:
        """Get current performance mode."""
        with self._lock:
            return self._current_mode
    
    def get_current_preset(self) -> ModePreset:
        """Get current performance preset."""
        with self._lock:
            return self._current_preset
    
    def set_mode(self, mode: PerformanceMode, force: bool = False) -> bool:
        """
        Switch to a different performance mode.
        
        Args:
            mode: Target performance mode
            force: Force switch even if cooldown not expired
            
        Returns:
            True if switch was successful, False if blocked by cooldown
            
        Raises:
            ModeTransitionError: If switch fails after attempting
        """
        try:
            with self._lock:
                current_time = time.time()
                time_since_change = current_time - self._last_mode_change
                
                if not force and time_since_change < self._mode_change_cooldown:
                    _logger.warning(
                        f"Mode switch blocked by cooldown: {time_since_change:.2f}s < {self._mode_change_cooldown}s"
                    )
                    return False
                
                if self._current_mode == mode:
                    return True  # Already in target mode
                
                old_mode = self._current_mode
                self._previous_mode = old_mode  # Store for rollback
                
                try:
                    # Apply mode change
                    self._current_mode = mode
                    self._last_mode_change = current_time
                    
                    _logger.info(f"Performance mode changed: {old_mode.value} -> {mode.value}")
                    return True
                    
                except Exception as e:
                    # Rollback on failure
                    _logger.error(f"Mode switch failed, rolling back: {e}", exc_info=True)
                    self._current_mode = self._previous_mode or old_mode
                    raise ModeTransitionError(f"Failed to switch mode: {e}") from e
                    
        except ModeTransitionError:
            raise
        except Exception as e:
            _logger.error(f"Unexpected error in set_mode: {e}", exc_info=True)
            raise ModeTransitionError(f"Unexpected error during mode switch: {e}") from e
    
    async def set_mode_async(self, mode: PerformanceMode, force: bool = False) -> bool:
        """
        Async version of set_mode for async contexts.
        
        Args:
            mode: Target performance mode
            force: Force switch even if cooldown not expired
            
        Returns:
            True if switch was successful, False if blocked by cooldown
            
        Raises:
            ModeTransitionError: If switch fails
        """
        async with self._async_lock:
            # Use sync method but with async lock protection
            return self.set_mode(mode, force=force)
    
    def set_preset(self, preset: ModePreset) -> None:
        """
        Set performance preset (affects mode configuration).
        
        Args:
            preset: Performance preset to apply
        """
        with self._lock:
            self._current_preset = preset
            
            # Map preset to mode
            if preset == ModePreset.COMPETITIVE:
                self._current_mode = PerformanceMode.COMPETITIVE
            else:
                # LOW, MEDIUM, HIGH, ULTRA map to Immersive with different quality
                self._current_mode = PerformanceMode.IMMERSIVE
            
            # Adjust config based on preset
            if preset == ModePreset.LOW:
                self._adjust_config_for_preset(self._immersive_config, 0.3)
            elif preset == ModePreset.MEDIUM:
                self._adjust_config_for_preset(self._immersive_config, 0.5)
            elif preset == ModePreset.HIGH:
                self._adjust_config_for_preset(self._immersive_config, 0.7)
            elif preset == ModePreset.ULTRA:
                self._adjust_config_for_preset(self._immersive_config, 1.0)
            elif preset == ModePreset.COMPETITIVE:
                # Competitive mode uses fixed config
                pass
            
            _logger.info(f"Performance preset changed: {preset.value}")
    
    def _adjust_config_for_preset(self, config: RenderingConfig, quality_factor: float) -> None:
        """Adjust config quality based on preset factor (0.0-1.0)."""
        # Scale detail density
        config.detail_density = quality_factor
        
        # Scale AI update rate (higher quality = lower rate for more complex AI)
        config.ai_update_rate_hz = 2.0 + (quality_factor * 8.0)  # 2-10 Hz
        
        # Scale max NPCs
        config.max_active_npcs = int(30 + (quality_factor * 70))  # 30-100
        
        # Scale culling aggressiveness (lower quality = more aggressive)
        config.culling_aggressiveness = 0.3 + ((1.0 - quality_factor) * 0.6)  # 0.3-0.9
    
    def get_config(self, mode: Optional[PerformanceMode] = None) -> RenderingConfig:
        """
        Get rendering configuration for a mode.
        
        Args:
            mode: Performance mode (defaults to current mode)
            
        Returns:
            RenderingConfig for the specified mode
        """
        if mode is None:
            mode = self.get_current_mode()
        
        if mode == PerformanceMode.IMMERSIVE:
            return RenderingConfig(**self._immersive_config.to_dict())
        else:
            return RenderingConfig(**self._competitive_config.to_dict())
    
    def get_config_dict(self, mode: Optional[PerformanceMode] = None) -> Dict[str, Any]:
        """Get rendering configuration as dictionary."""
        return self.get_config(mode).to_dict()
    
    def detect_hardware_preset(self, fps: float, target_fps: float) -> Optional[ModePreset]:
        """
        Detect appropriate preset based on hardware performance.
        
        Args:
            fps: Current FPS
            target_fps: Target FPS for current mode
            
        Returns:
            Recommended preset or None if no change needed
        """
        fps_ratio = fps / target_fps if target_fps > 0 else 1.0
        
        current_preset = self.get_current_preset()
        current_mode = self.get_current_mode()
        
        # If significantly below target, suggest lower preset
        if fps_ratio < 0.7:
            if current_mode == PerformanceMode.IMMERSIVE:
                if current_preset == ModePreset.ULTRA:
                    return ModePreset.HIGH
                elif current_preset == ModePreset.HIGH:
                    return ModePreset.MEDIUM
                elif current_preset == ModePreset.MEDIUM:
                    return ModePreset.LOW
            elif current_mode == PerformanceMode.COMPETITIVE:
                # Competitive mode already optimized, suggest Immersive mode
                return ModePreset.MEDIUM  # Switch to Immersive Medium
        
        # If significantly above target, suggest higher preset
        elif fps_ratio > 1.3:
            if current_mode == PerformanceMode.IMMERSIVE:
                if current_preset == ModePreset.LOW:
                    return ModePreset.MEDIUM
                elif current_preset == ModePreset.MEDIUM:
                    return ModePreset.HIGH
                elif current_preset == ModePreset.HIGH:
                    return ModePreset.ULTRA
        
        return None
    
    def get_target_fps(self) -> float:
        """Get target FPS for current mode."""
        mode = self.get_current_mode()
        if mode == PerformanceMode.IMMERSIVE:
            return 90.0  # Mid-point of 60-120 FPS range
        else:
            return 300.0  # 300+ FPS target
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status and configuration."""
        with self._lock:
            return {
                "mode": self._current_mode.value,
                "preset": self._current_preset.value,
                "target_fps": self.get_target_fps(),
                "config": self.get_config_dict(),
                "last_mode_change": self._last_mode_change,
            }
