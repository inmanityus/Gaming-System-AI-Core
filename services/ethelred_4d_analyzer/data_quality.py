"""
Data quality and ambiguous input handling for 4D Vision.
Part of T4D-13 implementation.
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from loguru import logger

from .detector_base import DetectorFinding, SegmentContext


class DataQualityLevel(Enum):
    """Quality levels for input data."""
    GOOD = "good"
    DEGRADED = "degraded"
    POOR = "poor"
    UNUSABLE = "unusable"


@dataclass
class DataQualityAssessment:
    """Assessment of data quality for a segment."""
    overall_quality: DataQualityLevel
    quality_factors: Dict[str, float]  # Factor -> score (0-1)
    missing_data: List[str]
    degraded_data: List[str]
    recommendations: List[str]
    can_analyze: bool
    confidence_adjustment: float  # Multiplier for detector confidence


class DataQualityAnalyzer:
    """Analyzes input data quality and handles degraded inputs."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Quality thresholds
        self.min_frame_count = self.config.get("min_frame_count", 30)
        self.min_resolution = self.config.get("min_resolution", (640, 480))
        self.max_compression_artifacts = self.config.get("max_compression_artifacts", 0.3)
        self.min_depth_coverage = self.config.get("min_depth_coverage", 0.7)
        self.max_frame_drops = self.config.get("max_frame_drops", 0.1)
        
    def assess_segment_quality(self, segment: SegmentContext) -> DataQualityAssessment:
        """Perform comprehensive quality assessment of a segment."""
        quality_factors = {}
        missing_data = []
        degraded_data = []
        recommendations = []
        
        # Check media availability
        media_score = self._assess_media_availability(segment, missing_data)
        quality_factors["media_availability"] = media_score
        
        # Check depth data
        depth_score = self._assess_depth_quality(segment, missing_data, degraded_data)
        quality_factors["depth_quality"] = depth_score
        
        # Check performance metrics
        perf_score = self._assess_performance_quality(segment, degraded_data)
        quality_factors["performance_data"] = perf_score
        
        # Check temporal consistency
        temporal_score = self._assess_temporal_quality(segment, degraded_data)
        quality_factors["temporal_consistency"] = temporal_score
        
        # Check metadata completeness
        metadata_score = self._assess_metadata_quality(segment, missing_data)
        quality_factors["metadata_completeness"] = metadata_score
        
        # Calculate overall quality
        overall_score = sum(quality_factors.values()) / len(quality_factors)
        overall_quality = self._score_to_quality_level(overall_score)
        
        # Determine if analysis can proceed
        can_analyze = overall_quality != DataQualityLevel.UNUSABLE
        
        # Calculate confidence adjustment
        confidence_adjustment = self._calculate_confidence_adjustment(
            overall_score, quality_factors
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            quality_factors, missing_data, degraded_data
        )
        
        return DataQualityAssessment(
            overall_quality=overall_quality,
            quality_factors=quality_factors,
            missing_data=missing_data,
            degraded_data=degraded_data,
            recommendations=recommendations,
            can_analyze=can_analyze,
            confidence_adjustment=confidence_adjustment
        )
    
    def _assess_media_availability(
        self, segment: SegmentContext, missing_data: List[str]
    ) -> float:
        """Assess availability of media files."""
        if not segment.media_uris:
            missing_data.append("No media URIs provided")
            return 0.0
        
        available_count = 0
        total_count = len(segment.media_uris)
        
        for camera_id, uri in segment.media_uris.items():
            # In production, would check if URI is accessible
            if uri:
                available_count += 1
            else:
                missing_data.append(f"Media URI missing for {camera_id}")
        
        return available_count / total_count if total_count > 0 else 0.0
    
    def _assess_depth_quality(
        self, segment: SegmentContext, 
        missing_data: List[str], 
        degraded_data: List[str]
    ) -> float:
        """Assess depth data quality."""
        # Check if any depth data exists
        if not hasattr(segment, 'depth_available') or not segment.depth_available:
            missing_data.append("Depth data not available")
            return 0.0
        
        # In production, would analyze depth map quality
        # For now, simulate based on metadata
        if segment.metadata.get("depth_sensor_type") == "estimated":
            degraded_data.append("Depth data is estimated, not measured")
            return 0.6
        elif segment.metadata.get("depth_sensor_type") == "lidar":
            return 1.0
        else:
            return 0.8
    
    def _assess_performance_quality(
        self, segment: SegmentContext, degraded_data: List[str]
    ) -> float:
        """Assess performance data quality."""
        if not segment.performance_metrics:
            return 0.5  # Can still analyze but with reduced confidence
        
        score = 1.0
        perf = segment.performance_metrics
        
        # Check for missing metrics
        required_metrics = ["avg_fps", "min_fps", "max_fps"]
        for metric in required_metrics:
            if metric not in perf:
                score -= 0.2
        
        # Check for anomalies
        if perf.get("min_fps", 30) < 10:
            degraded_data.append("Extremely low FPS may affect analysis accuracy")
            score -= 0.3
        
        return max(0.0, score)
    
    def _assess_temporal_quality(
        self, segment: SegmentContext, degraded_data: List[str]
    ) -> float:
        """Assess temporal consistency of the segment."""
        score = 1.0
        
        # Check duration
        if segment.duration_seconds < 1.0:
            degraded_data.append("Segment too short for reliable analysis")
            score -= 0.5
        elif segment.duration_seconds > 300:  # 5 minutes
            degraded_data.append("Segment very long, may have varying conditions")
            score -= 0.2
        
        # Check for gaps in gameplay events
        if segment.gameplay_events:
            # Sort events by timestamp
            sorted_events = sorted(
                segment.gameplay_events, 
                key=lambda e: e.get("timestamp", segment.start_timestamp)
            )
            
            # Look for large gaps
            for i in range(1, len(sorted_events)):
                prev_time = sorted_events[i-1].get("timestamp", segment.start_timestamp)
                curr_time = sorted_events[i].get("timestamp", segment.start_timestamp)
                gap = (curr_time - prev_time).total_seconds()
                
                if gap > 30:  # 30 second gap
                    degraded_data.append(f"Large gap ({gap}s) in gameplay events")
                    score -= 0.1
        
        return max(0.0, score)
    
    def _assess_metadata_quality(
        self, segment: SegmentContext, missing_data: List[str]
    ) -> float:
        """Assess metadata completeness."""
        required_fields = ["build_id", "level_name", "scene_type"]
        optional_fields = ["player_id", "session_id", "test_scenario"]
        
        score = 1.0
        
        # Check required fields
        for field in required_fields:
            if not getattr(segment, field, None):
                missing_data.append(f"Required field '{field}' is missing")
                score -= 0.3
        
        # Check optional fields (less penalty)
        for field in optional_fields:
            if not getattr(segment, field, None) and field not in segment.metadata:
                score -= 0.1
        
        return max(0.0, score)
    
    def _score_to_quality_level(self, score: float) -> DataQualityLevel:
        """Convert numeric score to quality level."""
        if score >= 0.9:
            return DataQualityLevel.GOOD
        elif score >= 0.7:
            return DataQualityLevel.DEGRADED
        elif score >= 0.4:
            return DataQualityLevel.POOR
        else:
            return DataQualityLevel.UNUSABLE
    
    def _calculate_confidence_adjustment(
        self, overall_score: float, quality_factors: Dict[str, float]
    ) -> float:
        """Calculate confidence adjustment based on quality."""
        # Base adjustment on overall score
        base_adjustment = overall_score
        
        # Apply additional penalties for critical factors
        if quality_factors.get("media_availability", 1.0) < 0.5:
            base_adjustment *= 0.7
        if quality_factors.get("temporal_consistency", 1.0) < 0.5:
            base_adjustment *= 0.8
        
        return max(0.1, base_adjustment)  # Never reduce confidence below 10%
    
    def _generate_recommendations(
        self, quality_factors: Dict[str, float],
        missing_data: List[str],
        degraded_data: List[str]
    ) -> List[str]:
        """Generate recommendations for improving data quality."""
        recommendations = []
        
        # Media recommendations
        if quality_factors.get("media_availability", 1.0) < 0.8:
            recommendations.append(
                "Ensure all camera views are properly captured and uploaded"
            )
        
        # Depth recommendations
        if quality_factors.get("depth_quality", 1.0) < 0.7:
            recommendations.append(
                "Consider using hardware depth sensors for better accuracy"
            )
        
        # Performance recommendations
        if quality_factors.get("performance_data", 1.0) < 0.7:
            recommendations.append(
                "Enable comprehensive performance metrics collection"
            )
        
        # Temporal recommendations
        if quality_factors.get("temporal_consistency", 1.0) < 0.8:
            recommendations.append(
                "Use consistent segment durations (30-120 seconds recommended)"
            )
        
        return recommendations
    
    def create_data_quality_finding(
        self, segment: SegmentContext, assessment: DataQualityAssessment
    ) -> Optional[DetectorFinding]:
        """Create a finding for data quality issues."""
        if assessment.overall_quality == DataQualityLevel.GOOD:
            return None
        
        severity = {
            DataQualityLevel.DEGRADED: 0.3,
            DataQualityLevel.POOR: 0.6,
            DataQualityLevel.UNUSABLE: 0.9
        }.get(assessment.overall_quality, 0.5)
        
        return DetectorFinding(
            detector_type="data_quality",
            issue_id=f"quality_{segment.segment_id}",
            issue_type="data_quality",
            severity=severity,
            confidence=0.95,  # High confidence in quality assessment
            timestamp=segment.start_timestamp,
            description=f"Input data quality is {assessment.overall_quality.value}",
            explainability={
                "quality_factors": assessment.quality_factors,
                "missing_data": assessment.missing_data,
                "degraded_data": assessment.degraded_data,
                "recommendations": assessment.recommendations
            },
            metrics={
                "overall_quality_score": sum(assessment.quality_factors.values()) / 
                                       len(assessment.quality_factors),
                "can_analyze": assessment.can_analyze
            },
            affected_goals=["G-RELIABILITY"],
            player_impact=0.0  # Data quality doesn't directly impact player
        )


def handle_degraded_input(
    findings: List[DetectorFinding], 
    quality_assessment: DataQualityAssessment
) -> List[DetectorFinding]:
    """
    Adjust detector findings based on data quality.
    
    This function:
    1. Reduces confidence scores for findings from degraded data
    2. Adds quality warnings to descriptions
    3. Filters out findings that are likely false positives
    """
    if quality_assessment.overall_quality == DataQualityLevel.GOOD:
        return findings
    
    adjusted_findings = []
    
    for finding in findings:
        # Skip findings that are unreliable with poor data
        if (quality_assessment.overall_quality == DataQualityLevel.POOR and 
            finding.confidence < 0.7):
            logger.debug(f"Filtering out low-confidence finding due to poor data quality: {finding.issue_id}")
            continue
        
        # Adjust confidence
        adjusted_confidence = finding.confidence * quality_assessment.confidence_adjustment
        
        # Add quality warning to description
        quality_warning = f" (Note: {quality_assessment.overall_quality.value} data quality)"
        adjusted_description = finding.description + quality_warning
        
        # Create adjusted finding
        adjusted_finding = DetectorFinding(
            detector_type=finding.detector_type,
            issue_id=finding.issue_id,
            issue_type=finding.issue_type,
            severity=finding.severity,
            confidence=adjusted_confidence,
            timestamp=finding.timestamp,
            camera_id=finding.camera_id,
            screen_coords=finding.screen_coords,
            world_coords=finding.world_coords,
            description=adjusted_description,
            explainability={
                **finding.explainability,
                "data_quality": quality_assessment.overall_quality.value,
                "confidence_adjusted": True
            },
            metrics=finding.metrics,
            affected_goals=finding.affected_goals,
            player_impact=finding.player_impact
        )
        
        adjusted_findings.append(adjusted_finding)
    
    return adjusted_findings
