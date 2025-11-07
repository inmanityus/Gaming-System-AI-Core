"""
Tests for ModeManager.
"""

import pytest
import time
from services.performance_mode.mode_manager import (
    ModeManager,
    PerformanceMode,
    ModePreset,
    RenderingConfig,
)


class TestRenderingConfig:
    """Tests for RenderingConfig."""
    
    def test_default_config(self):
        """Test default configuration."""
        config = RenderingConfig()
        assert config.lumen_enabled is False
        assert config.nanite_enabled is True
        assert config.volumetrics_enabled is False
    
    def test_config_to_dict(self):
        """Test configuration serialization."""
        config = RenderingConfig(
            lumen_enabled=True,
            nanite_enabled=False,
            detail_density=0.8
        )
        data = config.to_dict()
        assert data["lumen_enabled"] is True
        assert data["nanite_enabled"] is False
        assert data["detail_density"] == 0.8
    
    def test_config_from_dict(self):
        """Test configuration deserialization."""
        data = {
            "lumen_enabled": True,
            "nanite_enabled": False,
            "detail_density": 0.8,
            "lumen_quality": "high",
            "nanite_max_pixels_per_edge": 2,
            "volumetrics_enabled": False,
            "volumetric_fog_density": 0.0,
            "shadow_quality": "low",
            "max_shadow_casting_lights": 1,
            "shadow_resolution": 512,
            "post_processing_enabled": True,
            "post_processing_quality": "low",
            "audio_virtualization_enabled": False,
            "audio_quality": "low",
            "ai_update_rate_hz": 10.0,
            "max_active_npcs": 50,
            "environmental_storytelling_enabled": False,
            "culling_aggressiveness": 0.9,
            "lod_bias": 2.0,
            "upscaling_enabled": True,
            "upscaling_method": "fsr",
            "upscaling_quality": "ultra_performance",
            "internal_resolution_scale": 0.5,
        }
        config = RenderingConfig.from_dict(data)
        assert config.lumen_enabled is True
        assert config.nanite_enabled is False
        assert config.detail_density == 0.8


class TestModeManager:
    """Tests for ModeManager."""
    
    def test_initial_mode(self):
        """Test initial mode is Immersive."""
        manager = ModeManager()
        assert manager.get_current_mode() == PerformanceMode.IMMERSIVE
        assert manager.get_current_preset() == ModePreset.MEDIUM
    
    def test_set_mode(self):
        """Test mode switching."""
        manager = ModeManager()
        success = manager.set_mode(PerformanceMode.COMPETITIVE)
        assert success is True
        assert manager.get_current_mode() == PerformanceMode.COMPETITIVE
    
    def test_set_mode_cooldown(self):
        """Test mode switch cooldown."""
        manager = ModeManager()
        manager.set_mode(PerformanceMode.COMPETITIVE)
        
        # Immediate switch should be blocked
        success = manager.set_mode(PerformanceMode.IMMERSIVE)
        assert success is False
        
        # Force switch should work
        success = manager.set_mode(PerformanceMode.IMMERSIVE, force=True)
        assert success is True
    
    def test_get_config_immersive(self):
        """Test Immersive mode configuration."""
        manager = ModeManager()
        config = manager.get_config(PerformanceMode.IMMERSIVE)
        assert config.lumen_enabled is True
        assert config.environmental_storytelling_enabled is True
        assert config.detail_density == 1.0
    
    def test_get_config_competitive(self):
        """Test Competitive mode configuration."""
        manager = ModeManager()
        config = manager.get_config(PerformanceMode.COMPETITIVE)
        assert config.lumen_enabled is False
        assert config.environmental_storytelling_enabled is False
        assert config.upscaling_enabled is True
        assert config.detail_density == 0.3
    
    def test_set_preset(self):
        """Test preset switching."""
        manager = ModeManager()
        manager.set_preset(ModePreset.COMPETITIVE)
        assert manager.get_current_mode() == PerformanceMode.COMPETITIVE
        assert manager.get_current_preset() == ModePreset.COMPETITIVE
    
    def test_set_preset_immersive(self):
        """Test Immersive preset switching."""
        manager = ModeManager()
        manager.set_preset(ModePreset.LOW)
        assert manager.get_current_mode() == PerformanceMode.IMMERSIVE
        assert manager.get_current_preset() == ModePreset.LOW
    
    def test_detect_hardware_preset_low_fps(self):
        """Test preset detection when FPS is low."""
        manager = ModeManager()
        manager.set_preset(ModePreset.ULTRA)
        
        # FPS significantly below target (90 FPS for Immersive)
        recommended = manager.detect_hardware_preset(50.0, 90.0)
        assert recommended == ModePreset.HIGH
    
    def test_detect_hardware_preset_high_fps(self):
        """Test preset detection when FPS is high."""
        manager = ModeManager()
        manager.set_preset(ModePreset.LOW)
        
        # FPS significantly above target
        recommended = manager.detect_hardware_preset(150.0, 90.0)
        assert recommended == ModePreset.MEDIUM
    
    def test_get_target_fps(self):
        """Test target FPS retrieval."""
        manager = ModeManager()
        assert manager.get_target_fps() == 90.0  # Immersive default
        
        manager.set_mode(PerformanceMode.COMPETITIVE)
        assert manager.get_target_fps() == 300.0
    
    def test_get_status(self):
        """Test status retrieval."""
        manager = ModeManager()
        status = manager.get_status()
        assert "mode" in status
        assert "preset" in status
        assert "target_fps" in status
        assert "config" in status
        assert status["mode"] == "immersive"
        assert status["target_fps"] == 90.0


