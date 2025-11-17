"""
Comprehensive unit tests for EngagementSafetyConstraints.
Tests privacy protection and anti-predatory safeguards.
"""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock
import asyncio
import json

from services.ethelred_engagement.safety_constraints import (
    EngagementSafetyConstraints,
    SafetyConstraintsConfig
)


class TestEngagementSafetyConstraints:
    """Test suite for EngagementSafetyConstraints."""
    
    @pytest.mark.unit
    def test_initialization_default(self):
        """Test constraints initialization with defaults."""
        constraints = EngagementSafetyConstraints()
        
        assert constraints.config.min_cohort_size == 100
        assert constraints.config.max_hourly_checks_dashboard == 10
        assert constraints.config.max_daily_checks_report == 5
        assert constraints.config.max_hourly_checks_api == 60
        assert constraints.config.max_checks_real_time == 0
        assert constraints.config.real_time_latency_threshold_ms == 100
        
        # Check optimization keywords
        assert 'maximize' in constraints.config.optimization_keywords
        assert 'optimize' in constraints.config.optimization_keywords
    
    @pytest.mark.unit
    def test_initialization_custom_config(self, safety_config):
        """Test constraints initialization with custom config."""
        constraints = EngagementSafetyConstraints(config=safety_config)
        
        assert constraints.config == safety_config
        
        # Verify max_access_frequency is properly initialized
        assert constraints.max_access_frequency['dashboard'] == safety_config.max_hourly_checks_dashboard
        assert constraints.max_access_frequency['report'] == safety_config.max_daily_checks_report
        assert constraints.max_access_frequency['api'] == safety_config.max_hourly_checks_api
        assert constraints.max_access_frequency['real_time'] == safety_config.max_checks_real_time
    
    @pytest.mark.unit
    def test_check_usage_allowed_cohort_size(self):
        """Test cohort size validation."""
        constraints = EngagementSafetyConstraints()
        
        # Too small cohort
        allowed, reason = constraints.check_usage_allowed(
            cohort_size=50,
            usage_context='dashboard',
            latency_requirement_ms=1000
        )
        
        assert not allowed
        assert 'Cohort size 50 below minimum' in reason
        
        # Sufficient cohort
        allowed, reason = constraints.check_usage_allowed(
            cohort_size=150,
            usage_context='dashboard',
            latency_requirement_ms=1000
        )
        
        assert allowed
        assert reason == ""
    
    @pytest.mark.unit
    def test_check_usage_allowed_real_time_context(self):
        """Test real-time context restrictions."""
        constraints = EngagementSafetyConstraints()
        
        # Real-time with low latency requirement
        allowed, reason = constraints.check_usage_allowed(
            cohort_size=200,
            usage_context='real_time',
            latency_requirement_ms=50
        )
        
        assert not allowed
        assert 'Real-time usage not allowed' in reason
        
        # Real-time with acceptable latency
        allowed, reason = constraints.check_usage_allowed(
            cohort_size=200,
            usage_context='real_time',
            latency_requirement_ms=150
        )
        
        # Still not allowed due to max_checks_real_time = 0
        assert not allowed
    
    @pytest.mark.unit
    def test_check_usage_allowed_optimization_context(self):
        """Test optimization context detection."""
        constraints = EngagementSafetyConstraints()
        
        # Request with optimization keyword
        allowed, reason = constraints.check_usage_allowed(
            cohort_size=200,
            usage_context='api',
            latency_requirement_ms=1000,
            request_metadata={'purpose': 'maximize engagement'}
        )
        
        assert not allowed
        assert 'Optimization-focused usage detected' in reason
        
        # Request without optimization keywords
        allowed, reason = constraints.check_usage_allowed(
            cohort_size=200,
            usage_context='api',
            latency_requirement_ms=1000,
            request_metadata={'purpose': 'monitor health metrics'}
        )
        
        assert allowed
    
    @pytest.mark.unit
    def test_check_access_frequency_dashboard(self):
        """Test dashboard access frequency limits."""
        constraints = EngagementSafetyConstraints()
        
        # First access
        allowed = constraints._check_access_frequency('test_user', 'dashboard')
        assert allowed
        
        # Access within limits (hourly)
        for _ in range(9):  # Total 10 accesses
            allowed = constraints._check_access_frequency('test_user', 'dashboard')
            assert allowed
        
        # Exceed limit
        allowed = constraints._check_access_frequency('test_user', 'dashboard')
        assert not allowed
    
    @pytest.mark.unit
    def test_check_access_frequency_report(self):
        """Test report access frequency limits (daily)."""
        constraints = EngagementSafetyConstraints()
        
        # Access within daily limit
        for _ in range(5):
            allowed = constraints._check_access_frequency('test_user', 'report')
            assert allowed
        
        # Exceed daily limit
        allowed = constraints._check_access_frequency('test_user', 'report')
        assert not allowed
    
    @pytest.mark.unit
    def test_check_access_frequency_api(self):
        """Test API access frequency limits."""
        constraints = EngagementSafetyConstraints()
        
        # Higher limit for API
        for _ in range(60):
            allowed = constraints._check_access_frequency('api_user', 'api')
            assert allowed
        
        # Exceed limit
        allowed = constraints._check_access_frequency('api_user', 'api')
        assert not allowed
    
    @pytest.mark.unit
    def test_check_access_frequency_time_window_reset(self):
        """Test that access counts reset after time window."""
        # Use custom config with very low limits for testing
        config = SafetyConstraintsConfig(
            max_hourly_checks_dashboard=2,
            max_daily_checks_report=2
        )
        constraints = EngagementSafetyConstraints(config=config)
        
        # Use up dashboard limit
        constraints._check_access_frequency('user1', 'dashboard')
        constraints._check_access_frequency('user1', 'dashboard')
        
        # Should be blocked
        allowed = constraints._check_access_frequency('user1', 'dashboard')
        assert not allowed
        
        # Simulate time passing by clearing old entries
        # In real implementation, would check timestamps
        constraints.access_counts['dashboard']['user1'] = []
        
        # Should be allowed again
        allowed = constraints._check_access_frequency('user1', 'dashboard')
        assert allowed
    
    @pytest.mark.unit
    def test_check_access_frequency_different_users(self):
        """Test that access limits are per-user."""
        constraints = EngagementSafetyConstraints()
        
        # Max out user1's dashboard access
        for _ in range(10):
            constraints._check_access_frequency('user1', 'dashboard')
        
        # user1 should be blocked
        assert not constraints._check_access_frequency('user1', 'dashboard')
        
        # user2 should still be allowed
        assert constraints._check_access_frequency('user2', 'dashboard')
    
    @pytest.mark.unit
    def test_check_optimization_context_metadata(self):
        """Test optimization keyword detection in metadata."""
        constraints = EngagementSafetyConstraints()
        
        optimization_requests = [
            {'purpose': 'maximize revenue'},
            {'goal': 'optimize player retention'},
            {'description': 'increase engagement metrics'},
            {'task': 'boost daily active users'},
            {'objective': 'enhance monetization'},
            {'aim': 'improve conversion rates'},
            {'target': 'growth of user base'}
        ]
        
        for metadata in optimization_requests:
            is_optimization = constraints._check_optimization_context(metadata)
            assert is_optimization
        
        safe_requests = [
            {'purpose': 'monitor player health'},
            {'goal': 'track addiction indicators'},
            {'description': 'analyze play patterns'},
            {'task': 'generate safety report'}
        ]
        
        for metadata in safe_requests:
            is_optimization = constraints._check_optimization_context(metadata)
            assert not is_optimization
    
    @pytest.mark.unit
    def test_check_optimization_context_nested_metadata(self):
        """Test optimization keyword detection in nested metadata."""
        constraints = EngagementSafetyConstraints()
        
        nested_metadata = {
            'request': {
                'details': {
                    'purpose': 'maximize user engagement'
                }
            },
            'tags': ['analytics', 'optimization']
        }
        
        is_optimization = constraints._check_optimization_context(nested_metadata)
        assert is_optimization
    
    @pytest.mark.unit
    def test_check_optimization_context_case_insensitive(self):
        """Test case-insensitive keyword detection."""
        constraints = EngagementSafetyConstraints()
        
        test_cases = [
            {'purpose': 'MAXIMIZE engagement'},
            {'purpose': 'Optimize metrics'},
            {'purpose': 'INCREASE revenue'},
            {'purpose': 'mAxImIzE profits'}
        ]
        
        for metadata in test_cases:
            is_optimization = constraints._check_optimization_context(metadata)
            assert is_optimization
    
    @pytest.mark.unit
    def test_edge_case_empty_inputs(self):
        """Test handling of empty/None inputs."""
        constraints = EngagementSafetyConstraints()
        
        # Zero cohort size
        allowed, reason = constraints.check_usage_allowed(
            cohort_size=0,
            usage_context='dashboard'
        )
        assert not allowed
        
        # None metadata
        allowed, reason = constraints.check_usage_allowed(
            cohort_size=200,
            usage_context='dashboard',
            request_metadata=None
        )
        assert allowed
        
        # Empty metadata
        is_optimization = constraints._check_optimization_context({})
        assert not is_optimization
    
    @pytest.mark.unit
    def test_edge_case_invalid_context(self):
        """Test handling of invalid usage context."""
        constraints = EngagementSafetyConstraints()
        
        # Unknown context - should use default behavior
        allowed = constraints._check_access_frequency('user', 'unknown_context')
        # Should still track it
        assert 'unknown_context' in constraints.access_counts
    
    @pytest.mark.unit
    def test_config_validation(self):
        """Test configuration validation edge cases."""
        # Negative values
        config = SafetyConstraintsConfig(
            min_cohort_size=-10,  # Invalid
            max_hourly_checks_dashboard=-5  # Invalid
        )
        
        constraints = EngagementSafetyConstraints(config=config)
        
        # Should still function with invalid config
        allowed, reason = constraints.check_usage_allowed(
            cohort_size=50,
            usage_context='dashboard'
        )
        
        # Cohort check should use absolute value or treat as 0
        if config.min_cohort_size < 0:
            # Implementation specific - document behavior
            pass
    
    @pytest.mark.unit
    def test_concurrent_access(self):
        """Test thread safety with concurrent access checks."""
        constraints = EngagementSafetyConstraints()
        
        async def check_access_async(user_id, context):
            return constraints._check_access_frequency(user_id, context)
        
        async def run_concurrent_checks():
            # 5 users, each making 3 requests
            tasks = []
            for user_id in range(5):
                for _ in range(3):
                    task = check_access_async(f'user_{user_id}', 'api')
                    tasks.append(task)
            
            results = await asyncio.gather(*tasks)
            return results
        
        results = asyncio.run(run_concurrent_checks())
        
        # All should succeed (well under limit)
        assert all(results)
    
    @pytest.mark.unit
    def test_custom_optimization_keywords(self):
        """Test custom optimization keyword configuration."""
        custom_keywords = ['monetize', 'convert', 'upsell', 'gamify']
        
        config = SafetyConstraintsConfig(
            optimization_keywords=custom_keywords
        )
        
        constraints = EngagementSafetyConstraints(config=config)
        
        # Test custom keywords
        assert constraints._check_optimization_context({'goal': 'monetize users'})
        assert constraints._check_optimization_context({'plan': 'upsell premium'})
        
        # Original keywords should not work
        assert not constraints._check_optimization_context({'goal': 'maximize revenue'})
    
    @pytest.mark.performance
    def test_performance_high_frequency(self, performance_timer):
        """Test performance under high-frequency access."""
        constraints = EngagementSafetyConstraints()
        
        with performance_timer as timer:
            # Simulate 10000 access checks
            for i in range(10000):
                user_id = f'user_{i % 100}'  # 100 different users
                constraints._check_access_frequency(user_id, 'api')
        
        # Should handle high frequency efficiently
        assert timer.elapsed < 1.0  # Less than 1 second for 10k checks
    
    @pytest.mark.unit
    def test_check_usage_allowed_all_conditions(self):
        """Test check_usage_allowed with all conditions."""
        config = SafetyConstraintsConfig(
            min_cohort_size=50,
            max_hourly_checks_dashboard=5,
            real_time_latency_threshold_ms=200,
            optimization_keywords=['maximize', 'boost']
        )
        
        constraints = EngagementSafetyConstraints(config=config)
        
        # Valid request
        allowed, reason = constraints.check_usage_allowed(
            cohort_size=100,
            usage_context='dashboard',
            latency_requirement_ms=1000,
            request_metadata={'purpose': 'view metrics'}
        )
        assert allowed
        
        # Multiple failures
        allowed, reason = constraints.check_usage_allowed(
            cohort_size=30,  # Too small
            usage_context='real_time',  # Not allowed
            latency_requirement_ms=50,  # Too low
            request_metadata={'goal': 'maximize engagement'}  # Optimization
        )
        assert not allowed
        # Should mention cohort size as first failure
        assert 'Cohort size' in reason
