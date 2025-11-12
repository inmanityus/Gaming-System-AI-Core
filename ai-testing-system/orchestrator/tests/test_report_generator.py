#!/usr/bin/env python3
"""
Test Suite for Report Generator
TEST-1: Comprehensive testing for 100/100 quality
"""

import pytest
import asyncio
from datetime import datetime
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.report import (
    ReportData, ReportMetadata, ReportSummary, IssuesSummary,
    CostBreakdown, PerformanceMetrics, ReportFormat
)
from services.report_generator import ReportGenerator


@pytest.fixture
def sample_report_data():
    """Sample report data for testing."""
    return ReportData(
        metadata=ReportMetadata(
            report_id="rep_test_001",
            test_run_id="test_run_001",
            game_title="Test Game",
            test_environment="Test Environment",
            timestamp_generated_utc=datetime.utcnow(),
            status="PASS"
        ),
        summary=ReportSummary(
            total_screenshots=10,
            screenshots_with_issues=0,
            screenshots_passed=10,
            pass_rate=100.0,
            issues_by_severity=IssuesSummary(),
            total_analysis_time_seconds=60.0
        ),
        consensus_issues=[],
        test_results=[],
        costs=CostBreakdown(total_cost_usd=0.01),
        performance=PerformanceMetrics(
            total_processing_time_seconds=60.0,
            average_time_per_screenshot_seconds=6.0
        )
    )


@pytest.fixture
def report_generator():
    """Report generator instance."""
    return ReportGenerator()


class TestReportGenerator:
    """Test report generation functionality."""
    
    def test_json_generation(self, report_generator, sample_report_data):
        """Test JSON report generation."""
        json_output = report_generator.generate_json(sample_report_data)
        
        assert json_output is not None
        assert isinstance(json_output, str)
        assert len(json_output) > 0
        assert "rep_test_001" in json_output
        assert "Test Game" in json_output
        assert "100.0" in json_output
    
    def test_html_generation(self, report_generator, sample_report_data):
        """Test HTML report generation."""
        html_output = report_generator.generate_html(sample_report_data)
        
        assert html_output is not None
        assert isinstance(html_output, str)
        assert len(html_output) > 0
        assert "<!DOCTYPE html>" in html_output
        assert "rep_test_001" in html_output
        assert "Test Game" in html_output
    
    @pytest.mark.asyncio
    async def test_pdf_generation_graceful_failure(self, report_generator, sample_report_data):
        """Test PDF generation handles missing GTK gracefully."""
        try:
            pdf_output = await report_generator.generate_pdf(sample_report_data)
            # If GTK available, should succeed
            assert pdf_output is not None
            assert isinstance(pdf_output, bytes)
            assert len(pdf_output) > 0
        except RuntimeError as e:
            # If GTK not available, should fail gracefully
            assert "WeasyPrint" in str(e) or "GTK" in str(e)
    
    @pytest.mark.asyncio
    async def test_report_generation_all_formats(self, report_generator, sample_report_data):
        """Test report generation in all formats."""
        # JSON
        json_bytes = await report_generator.generate_report(sample_report_data, ReportFormat.JSON)
        assert len(json_bytes) > 0
        
        # HTML
        html_bytes = await report_generator.generate_report(sample_report_data, ReportFormat.HTML)
        assert len(html_bytes) > 0
    
    @pytest.mark.asyncio
    async def test_generator_cleanup(self, report_generator):
        """Test proper resource cleanup."""
        await report_generator.cleanup()
        assert report_generator._is_closed or report_generator._pdf_executor is None


class TestReportValidation:
    """Test report data validation."""
    
    def test_valid_report_metadata(self):
        """Test valid report metadata."""
        metadata = ReportMetadata(
            report_id="rep_valid_001",
            test_run_id="test_valid",
            game_title="Valid Game",
            test_environment="Valid Env",
            timestamp_generated_utc=datetime.utcnow(),
            status="PASS"
        )
        
        assert metadata.report_id == "rep_valid_001"
        assert metadata.status == "PASS"
    
    def test_invalid_report_id_format(self):
        """Test invalid report ID format is rejected."""
        with pytest.raises(ValueError):
            ReportMetadata(
                report_id="invalid",  # Doesn't match pattern
                test_run_id="test",
                game_title="Game",
                test_environment="Env",
                timestamp_generated_utc=datetime.utcnow(),
                status="PASS"
            )
    
    def test_invalid_status(self):
        """Test invalid status is rejected."""
        with pytest.raises(ValueError):
            ReportMetadata(
                report_id="rep_test_001",
                test_run_id="test",
                game_title="Game",
                test_environment="Env",
                timestamp_generated_utc=datetime.utcnow(),
                status="INVALID"  # Not PASS/FAIL/WARNING
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

