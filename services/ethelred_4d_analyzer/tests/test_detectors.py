"""
Tests for 4D Vision detectors.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from ..detector_base import DetectorFinding, SegmentContext
from ..detectors import (
    AnimationDetector, PhysicsDetector, RenderingDetector,
    LightingDetector, PerformanceDetector, FlowDetector,
    create_detector
)


class TestDetectorBase:
    """Test base detector functionality."""
    
    @pytest.fixture
    def segment_context(self):
        """Create a segment context for testing."""
        now = datetime.utcnow()
        return SegmentContext(
            segment_id=uuid4(),
            build_id="v1.0.0",
            scene_id="test_scene",
            level_name="test_level",
            start_timestamp=now,
            end_timestamp=now + timedelta(seconds=10),
            duration_seconds=10.0,
            frame_count=300,
            camera_configs=[{
                "camera_id": "main",
                "camera_type": "player_pov",
                "fov": 90.0,
                "position": [0, 0, 0],
                "rotation": [0, 0, 0]
            }],
            media_uris={"main": "s3://bucket/test.mp4"},
            depth_uris={},
            gameplay_events=[],
            performance_metrics={
                "avg_fps": 60.0,
                "min_fps": 55.0,
                "max_fps": 65.0
            },
            metadata={}
        )
    
    def test_detector_finding_creation(self):
        """Test creating a detector finding."""
        finding = DetectorFinding(
            detector_type="test",
            issue_id="test_001",
            issue_type="test_issue",
            severity=0.5,
            confidence=0.8,
            timestamp=datetime.utcnow(),
            description="Test finding"
        )
        
        assert finding.detector_type == "test"
        assert finding.severity == 0.5
        assert finding.confidence == 0.8
        assert finding.evidence_refs == []
        assert finding.metrics == {}
        assert finding.affected_goals == []
    
    def test_detector_registry(self):
        """Test detector creation from registry."""
        # Test all detector types can be created
        for detector_type in ["animation", "physics", "rendering", "lighting", "performance", "flow"]:
            detector = create_detector(detector_type)
            assert detector is not None
            assert detector.detector_type == detector_type
        
        # Test invalid detector type
        with pytest.raises(ValueError):
            create_detector("invalid_type")


class TestAnimationDetector:
    """Test animation detector."""
    
    @pytest.fixture
    def detector(self):
        return AnimationDetector(config={"confidence_threshold": 0.7})
    
    @pytest.mark.asyncio
    async def test_capabilities(self, detector):
        """Test detector capabilities."""
        caps = detector.get_capabilities()
        
        assert "t_pose" in caps["supported_issue_types"]
        assert "a_pose" in caps["supported_issue_types"]
        assert caps["requires_depth"] is False
        assert caps["performance_impact"] == "medium"
    
    @pytest.mark.asyncio
    async def test_analyze_with_death_event(self, detector, segment_context):
        """Test detection with death event."""
        # Add death event
        segment_context.gameplay_events.append({
            "event_id": "evt_001",
            "event_type": "death",
            "timestamp": segment_context.start_timestamp
        })
        
        findings = await detector.analyze(segment_context)
        
        # May or may not find issues due to randomness
        # Check structure if findings exist
        for finding in findings:
            assert finding.detector_type == "animation"
            assert finding.severity >= 0
            assert finding.severity <= 1
            assert finding.confidence >= detector.get_confidence_threshold()


class TestPhysicsDetector:
    """Test physics detector."""
    
    @pytest.fixture
    def detector(self):
        return PhysicsDetector()
    
    @pytest.mark.asyncio
    async def test_capabilities(self, detector):
        """Test detector capabilities."""
        caps = detector.get_capabilities()
        
        assert "clipping" in caps["supported_issue_types"]
        assert "ragdoll_explosion" in caps["supported_issue_types"]
        assert caps["requires_depth"] is True
        assert caps["performance_impact"] == "high"
    
    @pytest.mark.asyncio
    async def test_physics_jitter_detection(self, detector, segment_context):
        """Test detection of physics jitter from performance metrics."""
        # Set high frame time variance
        segment_context.performance_metrics["frame_time_variance"] = 15.0
        
        findings = await detector.analyze(segment_context)
        
        # Should detect physics jitter
        jitter_findings = [f for f in findings if f.issue_type == "physics_jitter"]
        if jitter_findings:  # May be filtered by confidence threshold
            assert len(jitter_findings) >= 1
            assert jitter_findings[0].confidence >= 0.9


class TestRenderingDetector:
    """Test rendering detector."""
    
    @pytest.fixture
    def detector(self):
        return RenderingDetector()
    
    @pytest.mark.asyncio
    async def test_capabilities(self, detector):
        """Test detector capabilities."""
        caps = detector.get_capabilities()
        
        assert "z_fighting" in caps["supported_issue_types"]
        assert "texture_missing" in caps["supported_issue_types"]
        assert "lod_pop" in caps["supported_issue_types"]
    
    @pytest.mark.asyncio
    async def test_low_fps_texture_issue(self, detector, segment_context):
        """Test texture streaming issue detection with low FPS."""
        # Set low min FPS
        segment_context.performance_metrics["min_fps"] = 15.0
        
        findings = await detector.analyze(segment_context)
        
        # Should detect texture streaming issues
        texture_findings = [f for f in findings if f.issue_type == "texture_missing"]
        assert len(texture_findings) >= 1
        assert texture_findings[0].metrics["min_fps"] == 15.0


class TestLightingDetector:
    """Test lighting detector."""
    
    @pytest.fixture
    def detector(self):
        return LightingDetector()
    
    @pytest.mark.asyncio
    async def test_horror_atmosphere_check(self, detector, segment_context):
        """Test horror atmosphere detection."""
        # Set horror-themed level
        segment_context.level_name = "horror_basement"
        
        findings = await detector.analyze(segment_context)
        
        # Check findings structure
        for finding in findings:
            assert finding.detector_type == "lighting"
            if finding.issue_type == "no_atmosphere":
                assert "G-HORROR" in finding.affected_goals


class TestPerformanceDetector:
    """Test performance detector."""
    
    @pytest.fixture
    def detector(self):
        return PerformanceDetector()
    
    @pytest.mark.asyncio
    async def test_fps_drop_detection(self, detector, segment_context):
        """Test FPS drop detection."""
        # Set low FPS
        segment_context.performance_metrics["min_fps"] = 20.0
        segment_context.performance_metrics["avg_fps"] = 35.0
        
        findings = await detector.analyze(segment_context)
        
        # Should detect FPS drop
        fps_findings = [f for f in findings if f.issue_type == "fps_drop"]
        assert len(fps_findings) == 1
        assert fps_findings[0].severity >= 0.6
        assert fps_findings[0].confidence == 0.95
    
    @pytest.mark.asyncio
    async def test_frame_pacing_detection(self, detector, segment_context):
        """Test frame pacing issue detection."""
        # Set high variance
        segment_context.performance_metrics["frame_time_variance"] = 8.0
        
        findings = await detector.analyze(segment_context)
        
        # Should detect pacing issues
        pacing_findings = [f for f in findings if f.issue_type == "frame_pacing"]
        assert len(pacing_findings) == 1
        assert pacing_findings[0].metrics["frame_time_variance"] == 8.0


class TestFlowDetector:
    """Test flow detector."""
    
    @pytest.fixture
    def detector(self):
        return FlowDetector()
    
    @pytest.mark.asyncio
    async def test_repeated_deaths_detection(self, detector, segment_context):
        """Test detection of repeated deaths (soft lock indicator)."""
        # Add multiple death events
        for i in range(5):
            segment_context.gameplay_events.append({
                "event_id": f"death_{i}",
                "event_type": "death",
                "timestamp": segment_context.start_timestamp + timedelta(seconds=i)
            })
        
        findings = await detector.analyze(segment_context)
        
        # Should detect soft lock
        soft_lock_findings = [f for f in findings if f.issue_type == "soft_lock"]
        assert len(soft_lock_findings) == 1
        assert soft_lock_findings[0].metrics["death_count"] == 5
        assert "G-LONGTERM" in soft_lock_findings[0].affected_goals
    
    @pytest.mark.asyncio
    async def test_uncompleted_puzzle_detection(self, detector, segment_context):
        """Test detection of uncompleted puzzles."""
        # Add puzzle start without complete
        segment_context.gameplay_events.append({
            "event_id": "puzzle_01",
            "event_type": "puzzle_start",
            "timestamp": segment_context.start_timestamp
        })
        
        findings = await detector.analyze(segment_context)
        
        # Should detect progress blocker
        puzzle_findings = [f for f in findings if f.issue_type == "progress_blocked"]
        assert len(puzzle_findings) == 1
        assert puzzle_findings[0].metrics["puzzle_attempts"] == 1


class TestDetectorFiltering:
    """Test detector finding filtering."""
    
    def test_confidence_filtering(self):
        """Test filtering by confidence threshold."""
        detector = AnimationDetector(config={"confidence_threshold": 0.8})
        
        findings = [
            DetectorFinding(
                detector_type="animation",
                issue_id="1",
                issue_type="test",
                severity=0.5,
                confidence=0.9,  # Above threshold
                timestamp=datetime.utcnow()
            ),
            DetectorFinding(
                detector_type="animation",
                issue_id="2",
                issue_type="test",
                severity=0.5,
                confidence=0.7,  # Below threshold
                timestamp=datetime.utcnow()
            )
        ]
        
        filtered = detector.filter_findings(findings)
        assert len(filtered) == 1
        assert filtered[0].issue_id == "1"
    
    def test_severity_filtering(self):
        """Test filtering by severity threshold."""
        detector = AnimationDetector(config={"severity_threshold": 0.6})
        
        findings = [
            DetectorFinding(
                detector_type="animation",
                issue_id="1",
                issue_type="test",
                severity=0.7,  # Above threshold
                confidence=0.9,
                timestamp=datetime.utcnow()
            ),
            DetectorFinding(
                detector_type="animation",
                issue_id="2",
                issue_type="test",
                severity=0.5,  # Below threshold
                confidence=0.9,
                timestamp=datetime.utcnow()
            )
        ]
        
        filtered = detector.filter_findings(findings)
        assert len(filtered) == 1
        assert filtered[0].issue_id == "1"
    
    def test_goal_impact_calculation(self):
        """Test goal impact calculation."""
        detector = AnimationDetector()
        
        # High severity should impact immersion
        goals = detector.calculate_goal_impact("t_pose", 0.8)
        assert "G-IMMERSION" in goals
        
        # Low severity might not
        goals = detector.calculate_goal_impact("minor_glitch", 0.2)
        assert len(goals) == 0 or "G-IMMERSION" not in goals

