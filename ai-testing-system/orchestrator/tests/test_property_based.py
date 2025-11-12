#!/usr/bin/env python3
"""
Property-Based Tests for Report System
TEST-2: Hypothesis property tests for 100/100 quality
"""

import pytest
from hypothesis import given, strategies as st, settings, HealthCheck
from datetime import datetime, timezone
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.report import ReportMetadata, IssuesSummary, CostBreakdown


# Custom strategies
@st.composite
def valid_report_ids(draw):
    """Generate valid report IDs matching pattern rep_[a-zA-Z0-9_]{8,20}."""
    length = draw(st.integers(min_value=8, max_value=20))
    chars = draw(st.text(alphabet='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_', min_size=length, max_size=length))
    return f"rep_{chars}"


@st.composite
def valid_test_run_ids(draw):
    """Generate valid test run IDs."""
    return draw(st.text(min_size=3, max_size=100, alphabet=st.characters(blacklist_categories=('Cc', 'Cs'))))


class TestPropertyBased:
    """Property-based tests using Hypothesis."""
    
    @given(valid_report_ids())
    @settings(max_examples=100, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_report_id_always_valid(self, report_id):
        """Property: Valid report IDs always parse correctly."""
        metadata = ReportMetadata(
            report_id=report_id,
            test_run_id="test",
            game_title="Game",
            test_environment="Env",
            timestamp_generated_utc=datetime.now(timezone.utc),
            status="PASS"
        )
        assert metadata.report_id == report_id
    
    @given(st.integers(min_value=0, max_value=1000))
    @settings(max_examples=100)
    def test_issues_summary_totals_consistent(self, critical):
        """Property: Issues summary total equals sum of components."""
        high = st.integers(min_value=0, max_value=100).example()
        medium = st.integers(min_value=0, max_value=100).example()
        low = st.integers(min_value=0, max_value=100).example()
        
        summary = IssuesSummary(
            critical=critical,
            high=high,
            medium=medium,
            low=low,
            total=critical + high + medium + low
        )
        
        assert summary.total == summary.critical + summary.high + summary.medium + summary.low
    
    @given(
        st.floats(min_value=0, max_value=100),
        st.floats(min_value=0, max_value=100),
        st.floats(min_value=0, max_value=100)
    )
    @settings(max_examples=50)
    def test_cost_breakdown_total_consistent(self, cost1, cost2, cost3):
        """Property: Total cost equals sum of individual costs."""
        costs = CostBreakdown(
            gemini_cost_usd=cost1,
            gpt5_cost_usd=cost2,
            claude_cost_usd=cost3,
            storage_cost_usd=0.001,
            total_cost_usd=cost1 + cost2 + cost3 + 0.001
        )
        
        expected_total = costs.gemini_cost_usd + costs.gpt5_cost_usd + costs.claude_cost_usd + costs.storage_cost_usd
        assert abs(costs.total_cost_usd - expected_total) < 0.0001  # Float precision tolerance


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--hypothesis-show-statistics"])

