"""
Tests for 4D Vision Coverage Analytics Job (T4D-11).
"""

import pytest
import json
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import asyncpg

from services.ethelred_4d_coverage.coverage_job import (
    CoverageAnalyzer, CoverageJob
)


class TestCoverageAnalyzer:
    """Test coverage analytics logic."""
    
    @pytest.mark.asyncio
    async def test_calculate_build_coverage(self):
        """Test build coverage calculation."""
        # Mock postgres connection
        mock_conn = AsyncMock()
        mock_pool = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        # Mock segment data
        mock_conn.fetch.side_effect = [
            # Segments query
            [
                {
                    'segment_id': 'seg1',
                    'level_name': 'horror_basement',
                    'scene_type': 'combat',
                    'duration_seconds': 30.0,
                    'created_at': datetime.utcnow()
                },
                {
                    'segment_id': 'seg2',
                    'level_name': 'dark_corridor',
                    'scene_type': 'exploration',
                    'duration_seconds': 45.0,
                    'created_at': datetime.utcnow()
                }
            ],
            # Issues query
            [
                {
                    'issue_type': 't_pose',
                    'severity': 0.8,
                    'count': 5,
                    'avg_confidence': 0.85
                },
                {
                    'issue_type': 'clipping',
                    'severity': 0.5,
                    'count': 3,
                    'avg_confidence': 0.9
                }
            ]
        ]
        
        analyzer = CoverageAnalyzer(mock_pool)
        result = await analyzer.calculate_build_coverage('build-123', datetime.utcnow())
        
        # Verify structure
        assert result['build_id'] == 'build-123'
        assert 'coverage' in result
        assert 'issues' in result
        assert 'quality_score' in result
        
        # Verify coverage data
        assert result['coverage']['total_segments'] == 2
        assert result['coverage']['total_duration_seconds'] == 75.0
        assert result['coverage']['scene_count'] == 2
        assert set(result['coverage']['scenes_covered']) == {'horror_basement', 'dark_corridor'}
        
        # Verify issue data
        assert result['issues']['total_count'] == 8
        assert 't_pose' in result['issues']['by_type']
        assert result['issues']['by_type']['t_pose']['count'] == 5
    
    @pytest.mark.asyncio
    async def test_calculate_scene_coverage(self):
        """Test scene-specific coverage calculation."""
        mock_conn = AsyncMock()
        mock_pool = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        # Mock data
        mock_conn.fetch.side_effect = [
            # Segments query
            [
                {
                    'segment_id': 'seg1',
                    'duration_seconds': 30.0,
                    'performance_metrics': {'avg_fps': 45, 'min_fps': 30},
                    'created_at': datetime.utcnow()
                }
            ],
            # Issues query
            [
                {
                    'issue_type': 'fps_drop',
                    'severity': 0.7,
                    'detector_type': 'performance',
                    'affected_goals': ['G-IMMERSION']
                }
            ]
        ]
        
        analyzer = CoverageAnalyzer(mock_pool)
        result = await analyzer.calculate_scene_coverage('build-123', 'horror_basement')
        
        assert result['scene_name'] == 'horror_basement'
        assert result['coverage']['segment_count'] == 1
        assert result['performance']['avg_fps'] == 45
        assert result['goal_impacts']['G-IMMERSION'] == 1
    
    @pytest.mark.asyncio
    async def test_calculate_trends(self):
        """Test trend calculation across builds."""
        mock_conn = AsyncMock()
        mock_pool = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        # Mock trend data
        mock_conn.fetch.side_effect = [
            # Issue trends
            [
                {'build_id': 'build-1', 'issue_type': 't_pose', 'count': 10, 'avg_severity': 0.8},
                {'build_id': 'build-1', 'issue_type': 'clipping', 'count': 5, 'avg_severity': 0.5},
                {'build_id': 'build-2', 'issue_type': 't_pose', 'count': 7, 'avg_severity': 0.7},
                {'build_id': 'build-2', 'issue_type': 'clipping', 'count': 8, 'avg_severity': 0.6}
            ],
            # Coverage trends
            [
                {
                    'build_id': 'build-1',
                    'scenes_tested': 5,
                    'total_segments': 100,
                    'total_duration': 3000,
                    'first_test': datetime.utcnow() - timedelta(hours=2),
                    'last_test': datetime.utcnow() - timedelta(hours=1)
                },
                {
                    'build_id': 'build-2',
                    'scenes_tested': 7,
                    'total_segments': 120,
                    'total_duration': 3600,
                    'first_test': datetime.utcnow() - timedelta(minutes=30),
                    'last_test': datetime.utcnow()
                }
            ]
        ]
        
        analyzer = CoverageAnalyzer(mock_pool)
        result = await analyzer.calculate_trends(['build-1', 'build-2'], 24)
        
        # Verify structure
        assert result['builds_analyzed'] == ['build-1', 'build-2']
        assert 'by_build' in result
        assert 'deltas' in result
        assert 'summary' in result
        
        # Verify trend data
        assert 'build-1' in result['by_build']
        assert 'build-2' in result['by_build']
        
        # Verify delta calculation (15 -> 15 issues, no change)
        assert len(result['deltas']) == 1
        delta = result['deltas'][0]
        assert delta['from_build'] == 'build-1'
        assert delta['to_build'] == 'build-2'
        assert delta['issue_delta'] == 0  # 15 -> 15
        assert delta['coverage_delta']['scenes'] == 2  # 5 -> 7
    
    def test_quality_score_calculation(self):
        """Test quality score calculation logic."""
        mock_pool = AsyncMock()
        analyzer = CoverageAnalyzer(mock_pool)
        
        # Test with no issues - perfect score
        score1 = analyzer._calculate_quality_score(
            segments=10,
            severity_counts={"low": 0, "medium": 0, "high": 0, "critical": 0},
            duration=600  # 10 minutes
        )
        assert score1 == 1.0
        
        # Test with some issues
        score2 = analyzer._calculate_quality_score(
            segments=10,
            severity_counts={"low": 10, "medium": 5, "high": 2, "critical": 1},
            duration=600
        )
        assert 0 < score2 < 1.0
        
        # Test with many critical issues - low score
        score3 = analyzer._calculate_quality_score(
            segments=10,
            severity_counts={"low": 0, "medium": 0, "high": 0, "critical": 20},
            duration=600
        )
        assert score3 < 0.3


class TestCoverageJob:
    """Test coverage job orchestration."""
    
    @pytest.mark.asyncio
    async def test_job_lifecycle(self):
        """Test job start/stop."""
        mock_pool = AsyncMock()
        mock_nats = AsyncMock()
        
        job = CoverageJob(mock_pool, mock_nats, {
            "interval_seconds": 1  # Fast for testing
        })
        
        # Start job
        await job.start()
        assert job._running is True
        assert job._task is not None
        
        # Let it run briefly
        await asyncio.sleep(0.1)
        
        # Stop job
        await job.stop()
        assert job._running is False
    
    @pytest.mark.asyncio
    async def test_analysis_run(self):
        """Test complete analysis run."""
        mock_pool = AsyncMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        mock_nats = AsyncMock()
        
        job = CoverageJob(mock_pool, mock_nats)
        
        # Mock get_recent_builds
        job._get_recent_builds = AsyncMock(return_value=['build-1', 'build-2'])
        
        # Mock analyzer methods
        job.analyzer.calculate_build_coverage = AsyncMock(return_value={
            'build_id': 'build-1',
            'coverage': {
                'scenes_covered': ['scene1', 'scene2'],
                'total_segments': 10
            },
            'issues': {'total_count': 5}
        })
        job.analyzer.calculate_scene_coverage = AsyncMock(return_value={
            'scene_name': 'scene1',
            'coverage': {'segment_count': 5}
        })
        job.analyzer.calculate_trends = AsyncMock(return_value={
            'builds_analyzed': ['build-1', 'build-2'],
            'summary': {'improving': 1}
        })
        
        # Mock store_coverage_summary
        job._store_coverage_summary = AsyncMock()
        
        # Run analysis
        await job._run_analysis()
        
        # Verify calls
        job._get_recent_builds.assert_called_once()
        assert job.analyzer.calculate_build_coverage.call_count >= 1
        assert mock_nats.publish.call_count >= 3  # Coverage, scene, trends
        job._store_coverage_summary.assert_called_once()
    
    @pytest.mark.asyncio 
    async def test_event_emission(self):
        """Test NATS event emission."""
        mock_pool = AsyncMock()
        mock_nats = AsyncMock()
        
        job = CoverageJob(mock_pool, mock_nats)
        
        # Test coverage event
        await job._emit_coverage_event({
            'build_id': 'test-build',
            'coverage': {'total_segments': 10}
        })
        
        # Verify NATS publish
        mock_nats.publish.assert_called_once()
        call_args = mock_nats.publish.call_args
        assert call_args[0][0] == "VISION.COVERAGE"
        
        # Verify event structure
        event_data = json.loads(call_args[0][1])
        assert 'event_id' in event_data
        assert 'timestamp' in event_data
        assert event_data['event_type'] == 'coverage_report'
        assert event_data['data']['build_id'] == 'test-build'
    
    @pytest.mark.asyncio
    async def test_idempotent_behavior(self):
        """Test that job is idempotent when rerun."""
        mock_pool = AsyncMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        
        mock_nats = AsyncMock()
        
        job = CoverageJob(mock_pool, mock_nats)
        
        # Setup mocks for empty data
        job._get_recent_builds = AsyncMock(return_value=['build-1'])
        job.analyzer.calculate_build_coverage = AsyncMock(return_value={
            'build_id': 'build-1',
            'coverage': {'scenes_covered': [], 'total_segments': 0},
            'issues': {'total_count': 0}
        })
        mock_conn.execute = AsyncMock()  # For store_coverage_summary
        mock_conn.fetchrow = AsyncMock(return_value={
            'builds_analyzed': 1,
            'unique_scenes': 0,
            'total_segments': 0,
            'total_duration': 0,
            'total_issues': 0
        })
        
        # Run twice
        await job._run_analysis()
        await job._run_analysis()
        
        # Should handle gracefully with no duplicates or errors
        assert job.analyzer.calculate_build_coverage.call_count == 2
