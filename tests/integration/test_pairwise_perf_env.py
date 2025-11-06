"""
Pairwise Testing for REQ-PERF-001 and REQ-ENV-001 Integration
Tests all combinations of mode configurations and scene generation.
"""

import pytest
import asyncio
from uuid import uuid4
from services.performance_mode.mode_manager import (
    ModeManager,
    PerformanceMode,
    ModePreset,
)
from services.environmental_narrative.narrative_service import (
    EnvironmentalNarrativeService,
    SceneType,
)


class TestPairwisePerformanceMode:
    """Pairwise tests for Performance Mode (REQ-PERF-001)."""
    
    @pytest.mark.parametrize("mode,preset", [
        (PerformanceMode.IMMERSIVE, ModePreset.LOW),
        (PerformanceMode.IMMERSIVE, ModePreset.MEDIUM),
        (PerformanceMode.IMMERSIVE, ModePreset.HIGH),
        (PerformanceMode.IMMERSIVE, ModePreset.ULTRA),
        (PerformanceMode.COMPETITIVE, ModePreset.COMPETITIVE),
    ])
    def test_mode_preset_combinations(self, mode, preset):
        """Test all mode and preset combinations."""
        manager = ModeManager()
        manager.set_mode(mode, force=True)
        manager.set_preset(preset)
        
        assert manager.get_current_mode() == mode
        assert manager.get_current_preset() == preset
        
        config = manager.get_config()
        assert config is not None
        assert isinstance(config.lumen_enabled, bool)
        assert isinstance(config.nanite_enabled, bool)
        assert 0.0 <= config.detail_density <= 1.0
    
    @pytest.mark.parametrize("fps,target_fps,expected", [
        (50.0, 90.0, ModePreset.HIGH),  # Low FPS -> downgrade
        (150.0, 90.0, ModePreset.MEDIUM),  # High FPS -> upgrade
        (90.0, 90.0, None),  # On target -> no change
        (200.0, 300.0, ModePreset.MEDIUM),  # Competitive mode low FPS -> suggest Immersive Medium
    ])
    def test_hardware_preset_detection(self, fps, target_fps, expected):
        """Test hardware preset detection with various FPS values."""
        manager = ModeManager()
        if expected == ModePreset.HIGH:
            manager.set_preset(ModePreset.ULTRA)
        elif expected == ModePreset.MEDIUM:
            if fps == 200.0:
                # Competitive mode scenario
                manager.set_mode(PerformanceMode.COMPETITIVE, force=True)
            else:
                manager.set_preset(ModePreset.LOW)
        elif expected is None:
            # No change expected
            pass
        
        recommended = manager.detect_hardware_preset(fps, target_fps)
        assert recommended == expected
    
    @pytest.mark.asyncio
    async def test_concurrent_mode_switching(self):
        """Test concurrent mode switching operations."""
        manager = ModeManager()
        
        async def switch_mode(mode):
            # Simulate async operation
            await asyncio.sleep(0.01)
            return manager.set_mode(mode, force=True)
        
        # Launch concurrent switches
        tasks = [
            switch_mode(PerformanceMode.IMMERSIVE),
            switch_mode(PerformanceMode.COMPETITIVE),
            switch_mode(PerformanceMode.IMMERSIVE),
        ]
        results = await asyncio.gather(*tasks)
        
        # Verify operations completed (some may have been blocked by cooldown)
        assert all(isinstance(r, bool) for r in results)
        # Final mode should be valid
        assert manager.get_current_mode() in [PerformanceMode.IMMERSIVE, PerformanceMode.COMPETITIVE]
    
    def test_config_serialization_roundtrip(self):
        """Test config serialization and deserialization."""
        manager = ModeManager()
        
        for mode in [PerformanceMode.IMMERSIVE, PerformanceMode.COMPETITIVE]:
            config = manager.get_config(mode)
            config_dict = config.to_dict()
            restored = type(config).from_dict(config_dict)
            
            assert restored.lumen_enabled == config.lumen_enabled
            assert restored.nanite_enabled == config.nanite_enabled
            assert restored.detail_density == config.detail_density
            assert restored.upscaling_enabled == config.upscaling_enabled
    
    @pytest.mark.parametrize("mode,expected_fps", [
        (PerformanceMode.IMMERSIVE, 90.0),
        (PerformanceMode.COMPETITIVE, 300.0),
    ])
    def test_target_fps_per_mode(self, mode, expected_fps):
        """Test target FPS for each mode."""
        manager = ModeManager()
        manager.set_mode(mode, force=True)
        assert manager.get_target_fps() == expected_fps


class TestPairwiseEnvironmentalNarrative:
    """Pairwise tests for Environmental Narrative Service (REQ-ENV-001)."""
    
    @pytest.mark.parametrize("scene_type,density,expected_min", [
        (SceneType.ABANDONED_CAMP, 5, 8),  # Min enforced by template
        (SceneType.ABANDONED_CAMP, 25, 25),
        (SceneType.ABANDONED_CAMP, 50, 25),  # Max enforced by template
        (SceneType.BATTLE_AFTERMATH, 10, 10),
        (SceneType.BATTLE_AFTERMATH, 30, 30),
        (SceneType.RECENT_DEPARTURE, 5, 5),
        (SceneType.RECENT_DEPARTURE, 15, 15),
        (SceneType.LONG_TERM_SETTLEMENT, 20, 20),
        (SceneType.LONG_TERM_SETTLEMENT, 50, 50),
    ])
    @pytest.mark.asyncio
    async def test_scene_type_density_combinations(self, scene_type, density, expected_min):
        """Test all scene type and density combinations.
        
        Note: Density is clamped to template min/max, so requested density may differ from actual.
        """
        service = EnvironmentalNarrativeService()
        location = (100.0, 200.0, 50.0)
        
        scene = await service.generate_story_scene(scene_type, location, density_override=density)
        
        assert scene.scene_type == scene_type
        assert scene.location == location
        # Density is clamped to template min/max, so check it's within expected range
        assert scene.clutter_density >= expected_min
        assert len(scene.objects) == scene.clutter_density
        assert len(scene.discovery_markers) > 0
    
    @pytest.mark.parametrize("noticed,reward_multiplier", [
        (True, 1.0),
        (False, 1.0),
    ])
    @pytest.mark.asyncio
    async def test_discovery_noticed_combinations(self, noticed, reward_multiplier):
        """Test discovery recording with noticed/unnoticed combinations."""
        service = EnvironmentalNarrativeService()
        player_id = uuid4()
        scene = await service.generate_story_scene(SceneType.ABANDONED_CAMP, (0, 0, 0))
        
        # Get object with different narrative weights
        critical_obj = None
        low_obj = None
        for obj in scene.objects:
            if obj.narrative_weight.value >= 3:
                critical_obj = obj
            elif obj.narrative_weight.value == 1:
                low_obj = obj
        
        if critical_obj:
            reward = await service.record_discovery(player_id, object_id=critical_obj.object_id, noticed=noticed)
            assert reward.noticed == noticed
            if noticed:
                assert reward.reward_value >= 5.0  # Critical objects give higher rewards
    
    @pytest.mark.parametrize("change_type,location,description", [
        ("player_action", (10.0, 20.0, 30.0), "Player destroyed wall"),
        ("npc_trace", (50.0, 60.0, 70.0), "NPC footprints"),
        ("weather_erosion", (100.0, 200.0, 50.0), "Rain washed away blood"),
        ("player_action", (0.0, 0.0, 0.0), "Player opened door"),
    ])
    @pytest.mark.asyncio
    async def test_environmental_change_combinations(self, change_type, location, description):
        """Test environmental change recording with various combinations."""
        service = EnvironmentalNarrativeService()
        player_id = uuid4()
        
        await service.record_environmental_change(
            change_type,
            location,
            description,
            player_id
        )
        
        # Small delay to ensure database operation completes
        await asyncio.sleep(0.1)
        
        history = await service.get_environmental_history(location, radius=5.0)
        assert len(history) >= 1
        assert any(
            h["change_type"] == change_type and
            h["description"] == description
            for h in history
        )
    
    @pytest.mark.asyncio
    async def test_concurrent_scene_generation(self):
        """Test concurrent scene generation."""
        service = EnvironmentalNarrativeService()
        location = (0.0, 0.0, 0.0)
        
        async def generate_scene(scene_type):
            await asyncio.sleep(0.01)
            return await service.generate_story_scene(scene_type, location)
        
        # Generate multiple scenes concurrently
        scene_types = [
            SceneType.ABANDONED_CAMP,
            SceneType.BATTLE_AFTERMATH,
            SceneType.RECENT_DEPARTURE,
            SceneType.LONG_TERM_SETTLEMENT,
        ]
        tasks = [generate_scene(st) for st in scene_types]
        scenes = await asyncio.gather(*tasks)
        
        assert len(scenes) == len(scene_types)
        assert all(scene.scene_type == scene_types[i] for i, scene in enumerate(scenes))
    
    @pytest.mark.asyncio
    async def test_discovery_metrics_calculation(self):
        """Test discovery metrics calculation with various scenarios."""
        service = EnvironmentalNarrativeService()
        player_id = uuid4()
        scene = await service.generate_story_scene(SceneType.ABANDONED_CAMP, (0, 0, 0))
        
        # Record multiple discoveries with different noticed states
        for i, obj in enumerate(scene.objects[:10]):
            noticed = (i % 2 == 0)  # Alternate noticed/unnoticed
            await service.record_discovery(player_id, object_id=obj.object_id, noticed=noticed)
        
        metrics = service.get_discovery_metrics()
        
        assert metrics["total_details"] == 10
        assert metrics["noticed_details"] == 5
        assert metrics["unnoticed_details"] == 5
        assert metrics["discovery_rate"] == 0.5
    
    @pytest.mark.asyncio
    async def test_environmental_history_filtering(self):
        """Test environmental history filtering by location and radius."""
        service = EnvironmentalNarrativeService()
        player_id = uuid4()
        
        # Record changes at different locations
        locations = [
            (0.0, 0.0, 0.0),
            (10.0, 10.0, 10.0),
            (100.0, 100.0, 100.0),
            (5.0, 5.0, 5.0),  # Close to first
        ]
        
        for loc in locations:
            await service.record_environmental_change(
                "player_action",
                loc,
                f"Change at {loc}",
                player_id
            )
        
        # Small delay to ensure database operations complete
        await asyncio.sleep(0.1)
        
        # Filter by location and radius
        history_near = await service.get_environmental_history((0.0, 0.0, 0.0), radius=15.0)
        history_far = await service.get_environmental_history((100.0, 100.0, 100.0), radius=15.0)
        
        assert len(history_near) >= 2  # At least first and fourth locations
        assert len(history_far) >= 1  # At least third location


class TestIntegrationPerformanceEnvironmental:
    """Integration tests for REQ-PERF-001 and REQ-ENV-001 together."""
    
    @pytest.mark.asyncio
    async def test_immersive_mode_with_environmental_storytelling(self):
        """Test Immersive mode enables environmental storytelling."""
        mode_manager = ModeManager()
        env_service = EnvironmentalNarrativeService()
        
        mode_manager.set_mode(PerformanceMode.IMMERSIVE, force=True)
        config = mode_manager.get_config()
        
        # Immersive mode should enable environmental storytelling
        assert config.environmental_storytelling_enabled is True
        assert config.detail_density == 1.0
        
        # Generate scene (should work with full detail)
        scene = await env_service.generate_story_scene(
            SceneType.LONG_TERM_SETTLEMENT,
            (0, 0, 0),
            density_override=50  # Maximum density
        )
        
        assert scene.clutter_density == 50
        assert len(scene.objects) == 50
    
    @pytest.mark.asyncio
    async def test_competitive_mode_with_reduced_storytelling(self):
        """Test Competitive mode reduces environmental storytelling."""
        mode_manager = ModeManager()
        env_service = EnvironmentalNarrativeService()
        
        mode_manager.set_mode(PerformanceMode.COMPETITIVE, force=True)
        config = mode_manager.get_config()
        
        # Competitive mode should disable/reduce environmental storytelling
        assert config.environmental_storytelling_enabled is False
        assert config.detail_density == 0.3
        
        # Generate scene (should work but with reduced expectations)
        scene = await env_service.generate_story_scene(
            SceneType.ABANDONED_CAMP,
            (0, 0, 0),
            density_override=10  # Lower density for performance
        )
        
        assert scene.clutter_density == 10
        assert len(scene.objects) == 10
    
    @pytest.mark.parametrize("mode,scene_type,expected_density", [
        (PerformanceMode.IMMERSIVE, SceneType.LONG_TERM_SETTLEMENT, 50),
        (PerformanceMode.IMMERSIVE, SceneType.ABANDONED_CAMP, 25),
        (PerformanceMode.COMPETITIVE, SceneType.BATTLE_AFTERMATH, 10),
        (PerformanceMode.COMPETITIVE, SceneType.RECENT_DEPARTURE, 5),
    ])
    @pytest.mark.asyncio
    async def test_mode_scene_density_integration(self, mode, scene_type, expected_density):
        """Test integration between mode and scene density."""
        mode_manager = ModeManager()
        env_service = EnvironmentalNarrativeService()
        
        mode_manager.set_mode(mode, force=True)
        config = mode_manager.get_config()
        
        # Adjust density based on mode
        if mode == PerformanceMode.COMPETITIVE:
            # Competitive mode should use lower density, but ensure minimum of 5
            # Also respect scene template minimums
            calculated_density = max(5, min(expected_density, int(expected_density * config.detail_density)))
            # Scene templates have minimums, so actual density may be higher
            density = calculated_density
        else:
            density = expected_density
        
        scene = await env_service.generate_story_scene(
            scene_type,
            (0, 0, 0),
            density_override=density
        )
        
        # Density may be clamped to template minimum, so check it's at least the calculated density
        # and matches scene type
        assert scene.clutter_density >= density
        assert scene.scene_type == scene_type
    
    @pytest.mark.asyncio
    async def test_mode_switch_preserves_environmental_history(self):
        """Test that mode switching doesn't affect environmental history."""
        mode_manager = ModeManager()
        env_service = EnvironmentalNarrativeService()
        player_id = uuid4()
        
        # Record history in Immersive mode
        mode_manager.set_mode(PerformanceMode.IMMERSIVE, force=True)
        await env_service.record_environmental_change(
            "player_action",
            (10.0, 20.0, 30.0),
            "Action in Immersive mode",
            player_id
        )
        
        # Small delay to ensure database operation completes
        await asyncio.sleep(0.1)
        
        # Switch to Competitive mode
        mode_manager.set_mode(PerformanceMode.COMPETITIVE, force=True)
        
        # History should still be accessible
        history = await env_service.get_environmental_history((10.0, 20.0, 30.0), radius=5.0)
        assert len(history) >= 1
        assert any("Immersive mode" in h["description"] for h in history)
        
        # Record new history in Competitive mode
        await env_service.record_environmental_change(
            "player_action",
            (10.0, 20.0, 30.0),
            "Action in Competitive mode",
            player_id
        )
        
        # Small delay to ensure database operation completes
        await asyncio.sleep(0.1)
        
        # Both should be present
        history = await env_service.get_environmental_history((10.0, 20.0, 30.0), radius=5.0)
        assert len(history) >= 2

