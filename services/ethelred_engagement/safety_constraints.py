"""
Safety constraints and enforcement for engagement & addiction analytics.
Ensures metrics are only used for cohort-level analysis and design feedback.
"""
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class ConstraintViolation(Exception):
    """Raised when a safety constraint is violated."""
    pass


class UsageContext(str, Enum):
    """Allowed contexts for engagement/addiction data usage."""
    COHORT_ANALYSIS = "cohort_analysis"
    DESIGN_REPORT = "design_report"
    ETHICS_REVIEW = "ethics_review"
    AGGREGATE_DASHBOARD = "aggregate_dashboard"
    BUILD_COMPARISON = "build_comparison"


class DisallowedUsage(str, Enum):
    """Explicitly disallowed usage patterns."""
    PLAYER_TARGETING = "player_targeting"
    REAL_TIME_PERSONALIZATION = "real_time_personalization"
    REWARD_OPTIMIZATION = "reward_optimization"
    INDIVIDUAL_PROFILING = "individual_profiling"
    AUTOMATED_DIFFICULTY = "automated_difficulty"
    MONETIZATION_TARGETING = "monetization_targeting"


class EngagementSafetyConstraints:
    """
    Enforces architectural constraints ensuring engagement/addiction metrics
    are used only for ethical purposes.
    
    CRITICAL: This class is the primary safeguard against predatory usage.
    """
    
    # Minimum cohort size for any analysis
    MIN_COHORT_SIZE = 50
    
    # Maximum frequency for accessing metrics (per context)
    MAX_ACCESS_FREQUENCY = {
        UsageContext.COHORT_ANALYSIS: 3600,  # Once per hour
        UsageContext.DESIGN_REPORT: 86400,    # Once per day
        UsageContext.ETHICS_REVIEW: 3600,     # Once per hour
        UsageContext.AGGREGATE_DASHBOARD: 300, # Every 5 minutes
        UsageContext.BUILD_COMPARISON: 3600    # Once per hour
    }
    
    def __init__(self):
        self.access_log = {}
        self.violation_log = []
    
    def check_usage_allowed(
        self,
        context: UsageContext,
        request_metadata: Dict[str, Any]
    ) -> bool:
        """
        Check if a usage request is allowed under safety constraints.
        
        Args:
            context: The intended usage context
            request_metadata: Metadata about the request
            
        Returns:
            True if allowed, raises ConstraintViolation if not
        """
        # Check for disallowed patterns
        self._check_disallowed_patterns(request_metadata)
        
        # Check cohort size constraints
        self._check_cohort_size(request_metadata)
        
        # Check access frequency
        self._check_access_frequency(context, request_metadata)
        
        # Check data granularity
        self._check_data_granularity(request_metadata)
        
        # Log successful access
        self._log_access(context, request_metadata)
        
        return True
    
    def _check_disallowed_patterns(self, metadata: Dict[str, Any]):
        """Check for explicitly disallowed usage patterns."""
        # Check for player-specific identifiers
        if any(key in metadata for key in ['player_id', 'user_id', 'account_id']):
            self._log_violation(
                DisallowedUsage.PLAYER_TARGETING,
                "Request contains player-specific identifiers"
            )
            raise ConstraintViolation(
                "Player-specific metrics access is forbidden. "
                "Only cohort-level analysis is allowed."
            )
        
        # Check for real-time indicators
        if metadata.get('real_time', False) or metadata.get('latency_ms', float('inf')) < 1000:
            self._log_violation(
                DisallowedUsage.REAL_TIME_PERSONALIZATION,
                "Request indicates real-time usage"
            )
            raise ConstraintViolation(
                "Real-time usage of engagement metrics is forbidden. "
                "Metrics are for offline analysis only."
            )
        
        # Check for optimization context
        optimization_keywords = [
            'optimize', 'maximize', 'increase', 'boost', 
            'retention', 'monetization', 'conversion'
        ]
        request_purpose = str(metadata.get('purpose', '')).lower()
        if any(keyword in request_purpose for keyword in optimization_keywords):
            self._log_violation(
                DisallowedUsage.REWARD_OPTIMIZATION,
                f"Request purpose suggests optimization: {request_purpose}"
            )
            raise ConstraintViolation(
                "Using engagement metrics for optimization is forbidden. "
                "Metrics are for health monitoring and ethical design only."
            )
    
    def _check_cohort_size(self, metadata: Dict[str, Any]):
        """Ensure minimum cohort size for privacy."""
        cohort_size = metadata.get('cohort_size', 0)
        if cohort_size > 0 and cohort_size < self.MIN_COHORT_SIZE:
            raise ConstraintViolation(
                f"Cohort size {cohort_size} is below minimum {self.MIN_COHORT_SIZE}. "
                "Smaller cohorts risk re-identification."
            )
    
    def _check_access_frequency(self, context: UsageContext, metadata: Dict[str, Any]):
        """Prevent too-frequent access that might indicate misuse."""
        requester = metadata.get('requester', 'unknown')
        key = f"{context}:{requester}"
        
        now = datetime.utcnow().timestamp()
        last_access = self.access_log.get(key, 0)
        
        min_interval = self.MAX_ACCESS_FREQUENCY.get(context, 3600)
        if now - last_access < min_interval:
            remaining = int(min_interval - (now - last_access))
            raise ConstraintViolation(
                f"Access too frequent for {context}. "
                f"Please wait {remaining} seconds before next request."
            )
    
    def _check_data_granularity(self, metadata: Dict[str, Any]):
        """Ensure data is appropriately aggregated."""
        granularity = metadata.get('granularity', 'cohort')
        
        if granularity in ['player', 'individual', 'user', 'session']:
            self._log_violation(
                DisallowedUsage.INDIVIDUAL_PROFILING,
                f"Request for {granularity}-level data"
            )
            raise ConstraintViolation(
                f"{granularity}-level data access is forbidden. "
                "Only cohort-level aggregates are allowed."
            )
        
        # Check time granularity
        time_granularity = metadata.get('time_granularity', 'daily')
        if time_granularity in ['realtime', 'minute', 'hourly']:
            raise ConstraintViolation(
                f"{time_granularity} granularity is too fine. "
                "Minimum time granularity is daily for engagement metrics."
            )
    
    def _log_access(self, context: UsageContext, metadata: Dict[str, Any]):
        """Log successful access for audit trail."""
        requester = metadata.get('requester', 'unknown')
        key = f"{context}:{requester}"
        self.access_log[key] = datetime.utcnow().timestamp()
        
        logger.info(
            f"Engagement metrics access allowed: "
            f"context={context}, requester={requester}, "
            f"cohort_size={metadata.get('cohort_size', 'N/A')}"
        )
    
    def _log_violation(self, violation_type: DisallowedUsage, details: str):
        """Log constraint violations for security review."""
        violation = {
            'timestamp': datetime.utcnow().isoformat(),
            'type': violation_type,
            'details': details
        }
        self.violation_log.append(violation)
        
        logger.warning(f"Safety constraint violation: {violation}")
    
    def get_violation_report(self) -> List[Dict[str, Any]]:
        """Get report of all logged violations."""
        return self.violation_log.copy()
    
    def validate_api_endpoint(self, endpoint_config: Dict[str, Any]) -> bool:
        """
        Validate that an API endpoint configuration meets safety requirements.
        Used during service initialization to prevent unsafe endpoints.
        """
        endpoint_path = endpoint_config.get('path', '')
        allowed_methods = endpoint_config.get('methods', [])
        
        # Disallow any endpoint with player-specific paths
        player_patterns = [
            '/player/', '/user/', '/session/', 
            '/individual/', '/personalize/', '/optimize/'
        ]
        if any(pattern in endpoint_path for pattern in player_patterns):
            raise ConstraintViolation(
                f"Endpoint {endpoint_path} suggests player-specific access. "
                "Only cohort-level endpoints are allowed."
            )
        
        # Disallow modification endpoints
        if any(method in allowed_methods for method in ['POST', 'PUT', 'PATCH', 'DELETE']):
            if 'report' not in endpoint_path and 'export' not in endpoint_path:
                raise ConstraintViolation(
                    f"Endpoint {endpoint_path} allows modifications. "
                    "Engagement metrics should be read-only except for reports."
                )
        
        return True
    
    def validate_integration(self, integration_config: Dict[str, Any]) -> bool:
        """
        Validate that an integration with other services meets safety requirements.
        """
        service_name = integration_config.get('service', '')
        data_flow = integration_config.get('data_flow', 'unknown')
        
        # Disallow integrations with real-time systems
        realtime_services = [
            'matchmaking', 'progression', 'rewards', 
            'difficulty', 'monetization', 'personalization'
        ]
        if any(service in service_name.lower() for service in realtime_services):
            raise ConstraintViolation(
                f"Integration with {service_name} is forbidden. "
                "Engagement metrics cannot flow to real-time game systems."
            )
        
        # Ensure data only flows to allowed services
        allowed_services = [
            'ethelred_coordinator', 'red_alert', 'reporting',
            'analytics_dashboard', 'ethics_review'
        ]
        if not any(service in service_name.lower() for service in allowed_services):
            logger.warning(
                f"Integration with {service_name} requires review. "
                "Ensure it doesn't enable predatory patterns."
            )
        
        return True


# Global constraints instance
safety_constraints = EngagementSafetyConstraints()


def require_safe_usage(context: UsageContext):
    """
    Decorator to enforce safety constraints on functions accessing engagement data.
    
    Usage:
        @require_safe_usage(UsageContext.COHORT_ANALYSIS)
        def analyze_cohort_engagement(cohort_id: str, **kwargs):
            ...
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Extract metadata from function arguments
            metadata = {
                'requester': kwargs.get('requester', func.__name__),
                'cohort_size': kwargs.get('cohort_size', 0),
                'granularity': kwargs.get('granularity', 'cohort'),
                'purpose': kwargs.get('purpose', ''),
                **kwargs
            }
            
            # Check constraints
            safety_constraints.check_usage_allowed(context, metadata)
            
            # Execute function
            return func(*args, **kwargs)
        
        wrapper.__name__ = func.__name__
        wrapper.__doc__ = func.__doc__
        return wrapper
    
    return decorator
