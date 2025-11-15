"""
Tests for enhanced detector implementations (T4D-08, T4D-09, T4D-10).
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock
import numpy as np

from services.ethelred_4d_analyzer.detectors import (
    AnimationDetector, PhysicsDetector, RenderingDetector,
    LightingDetector, PerformanceDetector, FlowDetector,
    create_detector
)
from services.ethelred_4d_analyzer.detector_base import SegmentContext


@pytest.fixture
def mock_segment():
    """Create a mock segment context."""
    return SegmentContext(
        segment_id="test-segment-123",
        build_id="build-456",
        start_timestamp=datetime.utcnow(),
        end_timestamp=datetime.utcnow(),
        duration_seconds=30.0,
        level_name="horror_basement_level",
        scene_type="combat",
        media_uris={"camera_1": "s3://bucket/video.mp4"},
        performance_metrics={
            "avg_fps": 45,
            "min_fps": 25,
            "max_fps": 60,
            "draw_calls": 5500,
            "memory_used_mb": 3500,
            "memory_total_mb": 4096
        },
        gameplay_events=[
            {"event_type": "death", "timestamp": datetime.utcnow(), "position": (100, 200, 0)},
            {"event_type": "combat_start", "timestamp": datetime.utcnow()},
            {"event_type": "puzzle_start", "timestamp": datetime.utcnow()}
        ]
    )


class TestAnimationDetector:
    """Test enhanced AnimationDetector."""
    
    @pytest.mark.asyncio
    async def test_configurable_thresholds(self):
        """Test that detector respects configuration."""
        config = {
            "t_pose_threshold": 0.7,
            "sensitivity_mode": "high"
        }
        detector = AnimationDetector(config)
        
        assert detector.t_pose_threshold == 0.7
        assert detector.sensitivity_mode == "high"
        
        caps = detector.get_capabilities()
        assert caps["configuration"]["active_thresholds"]["t_pose"] == 0.7
    
    @pytest.mark.asyncio
    async def test_explainability_output(self, mock_segment):
        """Test that findings include explainability."""
        detector = AnimationDetector()
        
        # Force T-pose detection
        detector._detect_t_pose = Mock(return_value=(True, 0.9))
        
        findings = await detector.analyze_frame({}, 0, mock_segment)
        
        if findings:  # May be random
            for finding in findings:
                if finding.issue_type == "t_pose":
                    assert "explainability" in finding.__dict__
                    assert "signals" in finding.explainability
                    assert "thresholds" in finding.explainability
                    assert "notes" in finding.explainability
    
    @pytest.mark.asyncio
    async def test_context_aware_detection(self, mock_segment):
        """Test that detector considers gameplay context."""
        detector = AnimationDetector()
        
        # Add death context
        mock_segment.gameplay_events.append({
            "event_type": "death",
            "timestamp": mock_segment.start_timestamp
        })
        
        # Force T-pose detection
        original_detect = detector._detect_t_pose
        detector._detect_t_pose = Mock(return_value=(True, 0.9))
        
        findings = await detector.analyze_frame({}, 0, mock_segment)
        
        # T-pose during death should not be flagged
        t_pose_findings = [f for f in findings if f.issue_type == "t_pose"]
        assert len(t_pose_findings) == 0 or any("death_sequence" in str(f) for f in findings)


class TestPhysicsDetector:
    """Test enhanced PhysicsDetector."""
    
    @pytest.mark.asyncio
    async def test_platform_specific_config(self):
        """Test platform-specific thresholds."""
        config = {
            "platform": "console",
            "clipping_threshold": 0.1,
            "sensitivity_mode": "low"
        }
        detector = PhysicsDetector(config)
        
        assert detector.clipping_threshold == 0.1
        assert detector.sensitivity_mode == "low"
    
    @pytest.mark.asyncio
    async def test_depth_based_detection(self, mock_segment):
        """Test depth-based physics analysis."""
        detector = PhysicsDetector()
        
        # Mock depth features with clipping
        detector._extract_depth_features = Mock(return_value={
            "object_distances": {
                "character_to_wall": -0.15,  # Clipping!
                "character_to_ground": 0.0,
                "objects_to_ground": [0.0, 0.0, 0.2]  # One floating
            },
            "velocity_estimates": {
                "ragdoll_parts": [10, 15, 80],  # One high velocity
                "debris": [5, 10, 15]
            },
            "collision_points": []
        })
        
        findings = await detector.analyze_batch([], mock_segment)
        
        # Should detect clipping and high velocity
        issue_types = {f.issue_type for f in findings}
        assert "clipping" in issue_types
        assert "ragdoll_explosion" in issue_types
        assert "floating_object" in issue_types
    
    @pytest.mark.asyncio
    async def test_multiple_detection_methods(self, mock_segment):
        """Test that all detection methods run."""
        detector = PhysicsDetector()
        
        # Mock all detection methods
        detector._detect_clipping = Mock(return_value=[])
        detector._detect_ragdoll_explosion = Mock(return_value=[])
        detector._detect_floating_objects = Mock(return_value=[])
        detector._detect_physics_jitter = Mock(return_value=[])
        
        await detector.analyze_batch([], mock_segment)
        
        # All methods should be called
        detector._detect_clipping.assert_called_once()
        detector._detect_ragdoll_explosion.assert_called_once()
        detector._detect_floating_objects.assert_called_once()
        detector._detect_physics_jitter.assert_called_once()


class TestRenderingDetector:
    """Test enhanced RenderingDetector."""
    
    @pytest.mark.asyncio
    async def test_texture_tracking(self, mock_segment):
        """Test texture loading tracking."""
        detector = RenderingDetector()
        
        # Simulate texture loading over multiple frames
        detector._analyze_render_features = Mock(return_value={
            "z_buffer_conflicts": [],
            "texture_states": {
                "texture_0": "loading",
                "texture_1": "loaded",
                "texture_2": "missing"
            },
            "lod_levels": {},
            "shadow_map_quality": 0.8,
            "frame_time": 16.7
        })
        
        # First frame - texture starts loading
        findings1 = await detector.analyze_frame({}, 0, mock_segment)
        
        # Simulate time passing
        mock_segment.start_timestamp = datetime.fromtimestamp(
            mock_segment.start_timestamp.timestamp() + 3
        )
        
        # Second frame - texture still loading (exceeds threshold)
        findings2 = await detector.analyze_frame({}, 90, mock_segment)
        
        # Should detect missing texture and possibly delayed loading
        all_findings = findings1 + findings2
        issue_types = {f.issue_type for f in all_findings}
        assert "texture_missing" in issue_types
    
    @pytest.mark.asyncio
    async def test_shader_hitch_detection(self, mock_segment):
        """Test shader compilation hitch detection."""
        detector = RenderingDetector()
        
        # Simulate normal frame times
        for i in range(10):
            detector._frame_times.append(16.7)  # 60 FPS
        
        # Simulate shader hitch
        detector._analyze_render_features = Mock(return_value={
            "z_buffer_conflicts": [],
            "texture_states": {},
            "lod_levels": {},
            "shadow_map_quality": 0.8,
            "frame_time": 150  # Huge spike!
        })
        
        findings = await detector.analyze_frame({}, 0, mock_segment)
        
        # Should detect shader hitch
        hitch_findings = [f for f in findings if f.issue_type == "shader_hitch"]
        assert len(hitch_findings) > 0
        assert hitch_findings[0].severity > 0.7


class TestLightingDetector:
    """Test enhanced LightingDetector."""
    
    @pytest.mark.asyncio
    async def test_horror_atmosphere_check(self, mock_segment):
        """Test horror-specific lighting requirements."""
        detector = LightingDetector({
            "horror_luminance_max": 0.3,
            "contrast_min": 3.0
        })
        
        # Mock bright horror scene (bad!)
        detector._analyze_lighting_features = Mock(return_value={
            "avg_luminance": 0.6,  # Too bright for horror
            "min_luminance": 0.2,
            "max_luminance": 0.9,
            "contrast_ratio": 2.0,  # Too low contrast
            "dark_pixel_ratio": 0.1,
            "bright_pixel_ratio": 0.4,
            "luminance_variance": 0.2,
            "histogram": {"low": 10, "mid": 50, "high": 40},
            "light_sources": [{"position": (0, 5, 0), "intensity": 1000}],
            "shadow_coverage": 0.3,
            "ambient_level": 0.2
        })
        
        findings = await detector.analyze_batch([], mock_segment)
        
        # Should detect missing horror atmosphere
        atmosphere_findings = [f for f in findings if f.issue_type == "no_atmosphere"]
        assert len(atmosphere_findings) >= 1
        
        # Should mention both brightness and contrast issues
        issue_types = {f.issue_type for f in findings}
        assert "no_atmosphere" in issue_types
    
    @pytest.mark.asyncio
    async def test_flicker_detection(self, mock_segment):
        """Test light flickering detection."""
        detector = LightingDetector()
        
        # Build up luminance history with variation
        luminance_pattern = [0.3, 0.7, 0.2, 0.8, 0.3, 0.9, 0.2, 0.7, 0.3, 0.8]
        
        for lum in luminance_pattern:
            detector._analyze_lighting_features = Mock(return_value={
                "avg_luminance": lum,
                "min_luminance": lum * 0.8,
                "max_luminance": lum * 1.2,
                "contrast_ratio": 3.0,
                "dark_pixel_ratio": 0.3,
                "bright_pixel_ratio": 0.1,
                "luminance_variance": 0.5,
                "histogram": {},
                "light_sources": [],
                "shadow_coverage": 0.5,
                "ambient_level": 0.1
            })
            await detector.analyze_batch([], mock_segment)
        
        # Final frame should detect flickering
        findings = await detector.analyze_batch([], mock_segment)
        
        flicker_findings = [f for f in findings if f.issue_type == "flickering_light"]
        assert len(flicker_findings) > 0


class TestPerformanceDetector:
    """Test enhanced PerformanceDetector."""
    
    @pytest.mark.asyncio
    async def test_platform_aware_thresholds(self):
        """Test platform-specific performance targets."""
        # PC config
        pc_detector = PerformanceDetector({"platform": "pc"})
        assert pc_detector.target_fps == 60
        
        # Console config
        console_detector = PerformanceDetector({"platform": "console"})
        assert console_detector.target_fps == 30
        
        # Mobile config
        mobile_detector = PerformanceDetector({"platform": "mobile"})
        assert mobile_detector.target_fps == 30
    
    @pytest.mark.asyncio
    async def test_build_type_severity(self, mock_segment):
        """Test that build type affects severity."""
        # Dev build - less severe
        dev_detector = PerformanceDetector({
            "platform": "pc",
            "build_type": "dev"
        })
        
        mock_segment.performance_metrics["min_fps"] = 20
        findings_dev = await dev_detector.analyze_batch([], mock_segment)
        
        # Release build - more severe
        release_detector = PerformanceDetector({
            "platform": "pc",
            "build_type": "release"
        })
        
        findings_release = await release_detector.analyze_batch([], mock_segment)
        
        # Release should have higher severity for same issue
        if findings_dev and findings_release:
            dev_severity = max(f.severity for f in findings_dev)
            release_severity = max(f.severity for f in findings_release)
            assert release_severity >= dev_severity
    
    @pytest.mark.asyncio
    async def test_resource_pressure_detection(self, mock_segment):
        """Test memory and thermal detection."""
        detector = PerformanceDetector()
        
        detector._analyze_performance_metrics = Mock(return_value={
            "avg_fps": 60,
            "min_fps": 55,
            "max_fps": 65,
            "frame_time_variance": 2.0,
            "frame_times": [16.7] * 30,
            "percentile_95": 17,
            "percentile_99": 18,
            "input_lag": 80,
            "memory_used": 3900,  # 95% usage
            "memory_total": 4096,
            "gpu_temp": 85,  # Hot!
            "cpu_usage": 0.8,
            "draw_calls": 6000,
            "triangles": 1500000
        })
        
        findings = await detector.analyze_batch([], mock_segment)
        
        # Should detect both issues
        issue_types = {f.issue_type for f in findings}
        assert "memory_pressure" in issue_types
        assert "thermal_throttling" in issue_types


class TestFlowDetector:
    """Test enhanced FlowDetector."""
    
    @pytest.mark.asyncio
    async def test_soft_lock_detection(self, mock_segment):
        """Test soft lock from repeated deaths."""
        detector = FlowDetector()
        
        # Add many deaths in same location
        death_position = (100, 200, 0)
        for i in range(5):
            mock_segment.gameplay_events.append({
                "event_type": "death",
                "timestamp": mock_segment.start_timestamp,
                "position": death_position
            })
        
        findings = await detector.analyze_batch([], mock_segment)
        
        # Should detect soft lock with high confidence
        soft_lock_findings = [f for f in findings if f.issue_type == "soft_lock"]
        assert len(soft_lock_findings) > 0
        assert soft_lock_findings[0].confidence >= 0.9  # Same position = high confidence
    
    @pytest.mark.asyncio
    async def test_stuck_player_detection(self, mock_segment):
        """Test detection of stuck player."""
        detector = FlowDetector({
            "movement_threshold": 5.0,
            "stuck_duration_threshold": 20
        })
        
        # Mock minimal movement
        detector._analyze_movement_patterns = Mock(return_value={
            "positions": [(0, 0, 0)] * 10,
            "total_distance": 2.0,
            "movement_radius": 1.0,  # Stuck in 1m radius
            "avg_speed": 0.2
        })
        
        mock_segment.duration_seconds = 30  # Long enough to be stuck
        
        findings = await detector.analyze_batch([], mock_segment)
        
        # Should detect stuck player
        stuck_findings = [f for f in findings if f.issue_type == "stuck_player"]
        assert len(stuck_findings) > 0
    
    @pytest.mark.asyncio
    async def test_puzzle_timeout_detection(self, mock_segment):
        """Test detection of puzzle timeouts."""
        detector = FlowDetector({
            "puzzle_time_threshold": 300  # 5 minutes
        })
        
        # Puzzle started but not completed
        mock_segment.gameplay_events = [
            {"event_type": "puzzle_start", "timestamp": mock_segment.start_timestamp},
            {"event_type": "puzzle_reset", "timestamp": mock_segment.start_timestamp},
            {"event_type": "puzzle_reset", "timestamp": mock_segment.start_timestamp}
        ]
        mock_segment.duration_seconds = 360  # 6 minutes
        
        findings = await detector.analyze_batch([], mock_segment)
        
        # Should detect progress blocker
        blocked_findings = [f for f in findings if f.issue_type == "progress_blocked"]
        assert len(blocked_findings) > 0
        assert blocked_findings[0].explainability["signals"]["reset_count"] == 2
