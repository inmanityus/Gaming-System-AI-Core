"""
Base classes and interfaces for 4D Vision detectors.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from uuid import UUID


@dataclass
class DetectorFinding:
    """A finding from a detector analysis."""
    
    detector_type: str  # animation, physics, rendering, lighting, performance, flow
    issue_id: str
    issue_type: str  # e.g., t_pose, clipping, z_fighting
    
    severity: float  # 0.0-1.0
    confidence: float  # 0.0-1.0
    
    # Location in 4D space
    timestamp: datetime
    camera_id: Optional[str] = None
    screen_coords: Optional[Tuple[float, float]] = None  # normalized 0-1
    world_coords: Optional[Tuple[float, float, float]] = None  # game world
    
    # Evidence
    description: str = ""
    evidence_refs: List[str] = None  # URIs to specific frames/clips
    metrics: Dict[str, float] = None  # Detector-specific measurements
    
    # Impact
    affected_goals: List[str] = None  # G-IMMERSION, G-HORROR, etc.
    player_impact: float = 0.0  # Estimated impact on player experience
    
    def __post_init__(self):
        if self.evidence_refs is None:
            self.evidence_refs = []
        if self.metrics is None:
            self.metrics = {}
        if self.affected_goals is None:
            self.affected_goals = []


@dataclass 
class SegmentContext:
    """Context information for analyzing a segment."""
    
    segment_id: UUID
    build_id: str
    scene_id: str
    level_name: str
    
    start_timestamp: datetime
    end_timestamp: datetime
    duration_seconds: float
    frame_count: int
    
    camera_configs: List[Dict[str, Any]]
    media_uris: Dict[str, str]  # camera_id -> URI
    depth_uris: Dict[str, str]  # camera_id -> depth URI
    
    gameplay_events: List[Dict[str, Any]]
    performance_metrics: Dict[str, float]
    
    metadata: Dict[str, Any]


class VisionDetector(ABC):
    """
    Abstract base class for all 4D Vision detectors.
    
    Each detector analyzes a specific aspect of the 4D capture
    (animation, physics, rendering, etc.) and returns findings.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.detector_type = self.__class__.__name__.replace("Detector", "").lower()
    
    @abstractmethod
    async def analyze(self, segment: SegmentContext) -> List[DetectorFinding]:
        """
        Analyze a segment and return findings.
        
        Args:
            segment: The segment context with metadata and media references
            
        Returns:
            List of detector findings (can be empty)
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get detector capabilities and configuration.
        
        Returns:
            Dict with:
                - supported_issue_types: List of issue types this detector can find
                - requires_depth: Whether depth data is required
                - performance_impact: Expected performance impact (low/medium/high)
                - configuration: Current configuration parameters
        """
        pass
    
    def get_confidence_threshold(self) -> float:
        """Get minimum confidence threshold for reporting issues."""
        return self.config.get("confidence_threshold", 0.7)
    
    def get_severity_threshold(self) -> float:
        """Get minimum severity threshold for reporting issues."""
        return self.config.get("severity_threshold", 0.3)
    
    def filter_findings(self, findings: List[DetectorFinding]) -> List[DetectorFinding]:
        """Filter findings based on confidence and severity thresholds."""
        confidence_threshold = self.get_confidence_threshold()
        severity_threshold = self.get_severity_threshold()
        
        return [
            f for f in findings
            if f.confidence >= confidence_threshold and f.severity >= severity_threshold
        ]
    
    def calculate_goal_impact(self, issue_type: str, severity: float) -> List[str]:
        """
        Calculate which game goals are impacted by an issue.
        
        Override in subclasses for detector-specific logic.
        """
        affected_goals = []
        
        # Default logic - can be overridden
        if severity >= 0.7:
            affected_goals.append("G-IMMERSION")
        
        return affected_goals
    
    def calculate_player_impact(self, finding: DetectorFinding) -> float:
        """
        Calculate estimated player impact (0.0-1.0).
        
        Override in subclasses for detector-specific logic.
        """
        # Default: weighted average of severity and confidence
        return (finding.severity * 0.7 + finding.confidence * 0.3)


class BatchDetector(VisionDetector):
    """
    Base class for detectors that analyze multiple frames at once.
    """
    
    @abstractmethod
    async def analyze_batch(
        self, 
        frames: List[Dict[str, Any]], 
        segment: SegmentContext
    ) -> List[DetectorFinding]:
        """Analyze a batch of frames."""
        pass
    
    async def analyze(self, segment: SegmentContext) -> List[DetectorFinding]:
        """Default implementation loads frames and calls analyze_batch."""
        # In real implementation, would load frames from media_uris
        # For now, return empty findings
        frames = []  # Would load from storage
        
        if not frames:
            return []
        
        findings = await self.analyze_batch(frames, segment)
        return self.filter_findings(findings)


class StreamingDetector(VisionDetector):
    """
    Base class for detectors that analyze frames in a streaming fashion.
    """
    
    @abstractmethod
    async def analyze_frame(
        self,
        frame: Dict[str, Any],
        frame_index: int,
        segment: SegmentContext
    ) -> List[DetectorFinding]:
        """Analyze a single frame."""
        pass
    
    async def analyze(self, segment: SegmentContext) -> List[DetectorFinding]:
        """Default implementation processes frames one by one."""
        all_findings = []
        
        # In real implementation, would stream frames from media_uris
        # For now, return empty findings
        frame_count = segment.frame_count
        
        for i in range(min(frame_count, 1)):  # Process at least one frame for skeleton
            # Would load frame from storage
            frame = {"index": i, "data": None}
            
            findings = await self.analyze_frame(frame, i, segment)
            all_findings.extend(findings)
        
        return self.filter_findings(all_findings)
