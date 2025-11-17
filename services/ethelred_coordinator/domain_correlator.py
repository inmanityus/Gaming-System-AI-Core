"""
Domain Correlator
=================

Correlates signals from multiple QA domains to identify cross-cutting issues
and generate comprehensive quality assessments.
"""

from __future__ import annotations

import asyncio
from collections import defaultdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set, Any
from uuid import UUID

from loguru import logger
from pydantic import BaseModel, Field


class QADomain(str, Enum):
    """QA domains monitored by Ethelred."""
    CONTENT = "content_governance"
    VISION_4D = "4d_vision"
    AUDIO = "audio_auth"
    STORY = "story_memory"
    ENGAGEMENT = "engagement_analytics"
    LANGUAGE = "multi_language"


class DomainSignal(BaseModel):
    """Generic signal from any QA domain."""
    domain: QADomain
    signal_type: str  # e.g., "violation", "drift", "quality_issue"
    severity: str  # "low", "medium", "high", "critical"
    session_id: Optional[UUID] = None
    player_id: Optional[UUID] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: Dict[str, Any] = Field(default_factory=dict)
    evidence_refs: List[str] = Field(default_factory=list)


class CorrelatedIssue(BaseModel):
    """Multi-domain issue identified by correlation."""
    issue_id: UUID = Field(default_factory=UUID)
    domains_affected: List[QADomain]
    primary_domain: QADomain
    severity: str
    session_id: Optional[UUID] = None
    player_id: Optional[UUID] = None
    signals: List[DomainSignal]
    pattern: str  # e.g., "content_audio_sync", "narrative_visual_mismatch"
    description: str
    recommended_action: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DomainCorrelator:
    """
    Correlates signals across QA domains to identify multi-domain issues.
    
    This is the brain of Ethelred - it understands how different quality
    issues relate to each other and can identify systemic problems.
    """
    
    def __init__(self, correlation_window_minutes: int = 5):
        self.correlation_window = timedelta(minutes=correlation_window_minutes)
        
        # Recent signals by session for correlation
        self._session_signals: Dict[UUID, List[DomainSignal]] = defaultdict(list)
        
        # Recent signals by player for pattern detection
        self._player_signals: Dict[UUID, List[DomainSignal]] = defaultdict(list)
        
        # Active correlated issues
        self._active_issues: Dict[UUID, CorrelatedIssue] = {}
        
        # Pattern detection rules
        self._correlation_patterns = self._init_correlation_patterns()
        
        self._lock = asyncio.Lock()
    
    def _init_correlation_patterns(self) -> List[Dict[str, Any]]:
        """Initialize cross-domain correlation patterns."""
        return [
            {
                "name": "content_audio_mismatch",
                "required_domains": [QADomain.CONTENT, QADomain.AUDIO],
                "description": "Audio content doesn't match visual content ratings",
                "severity_boost": 1,  # Increase severity by 1 level
            },
            {
                "name": "narrative_content_violation",
                "required_domains": [QADomain.CONTENT, QADomain.STORY],
                "description": "Content violations disrupting narrative flow",
                "severity_boost": 2,  # Major issue
            },
            {
                "name": "multimodal_horror_overload",
                "required_domains": [QADomain.CONTENT, QADomain.VISION_4D, QADomain.AUDIO],
                "signal_filters": {
                    QADomain.CONTENT: lambda s: s.details.get("category") == "horror_intensity"
                },
                "description": "Horror content overwhelming across multiple senses",
                "severity_boost": 2,
            },
            {
                "name": "player_distress_pattern",
                "required_domains": [QADomain.ENGAGEMENT, QADomain.CONTENT],
                "signal_filters": {
                    QADomain.ENGAGEMENT: lambda s: s.details.get("metric", "").startswith("exit_")
                },
                "description": "Player showing distress signals correlated with content",
                "severity_boost": 3,  # Critical - player wellbeing
            },
            {
                "name": "localization_content_mismatch",
                "required_domains": [QADomain.LANGUAGE, QADomain.CONTENT],
                "description": "Translated content has different rating than original",
                "severity_boost": 1,
            }
        ]
    
    async def add_signal(self, signal: DomainSignal) -> Optional[CorrelatedIssue]:
        """
        Add a new signal and check for correlations.
        
        Returns a CorrelatedIssue if a new multi-domain issue is identified.
        """
        async with self._lock:
            # Store by session if available
            if signal.session_id:
                self._session_signals[signal.session_id].append(signal)
                # Cleanup old signals
                cutoff = datetime.utcnow() - self.correlation_window
                self._session_signals[signal.session_id] = [
                    s for s in self._session_signals[signal.session_id]
                    if s.timestamp > cutoff
                ]
            
            # Store by player if available
            if signal.player_id:
                self._player_signals[signal.player_id].append(signal)
                # Cleanup old signals
                cutoff = datetime.utcnow() - self.correlation_window
                self._player_signals[signal.player_id] = [
                    s for s in self._player_signals[signal.player_id]
                    if s.timestamp > cutoff
                ]
            
            # Check for correlations
            return await self._check_correlations(signal)
    
    async def _check_correlations(self, new_signal: DomainSignal) -> Optional[CorrelatedIssue]:
        """Check if new signal correlates with existing signals."""
        # Get relevant signals for correlation
        relevant_signals: List[DomainSignal] = []
        
        if new_signal.session_id:
            relevant_signals.extend(self._session_signals[new_signal.session_id])
        elif new_signal.player_id:
            relevant_signals.extend(self._player_signals[new_signal.player_id])
        else:
            # No correlation possible without session or player
            return None
        
        # Check each correlation pattern
        for pattern in self._correlation_patterns:
            issue = self._check_pattern(new_signal, relevant_signals, pattern)
            if issue:
                # Store active issue
                self._active_issues[issue.issue_id] = issue
                logger.info(
                    f"Identified correlated issue: {issue.pattern} "
                    f"affecting {len(issue.domains_affected)} domains"
                )
                return issue
        
        return None
    
    def _check_pattern(
        self,
        new_signal: DomainSignal,
        relevant_signals: List[DomainSignal],
        pattern: Dict[str, Any]
    ) -> Optional[CorrelatedIssue]:
        """Check if signals match a specific correlation pattern."""
        required_domains = set(pattern["required_domains"])
        
        # Must include the new signal's domain
        if new_signal.domain not in required_domains:
            return None
        
        # Collect signals by domain
        signals_by_domain: Dict[QADomain, List[DomainSignal]] = defaultdict(list)
        for signal in relevant_signals:
            if signal.domain in required_domains:
                # Apply signal filter if specified
                signal_filter = pattern.get("signal_filters", {}).get(signal.domain)
                if signal_filter and not signal_filter(signal):
                    continue
                signals_by_domain[signal.domain].append(signal)
        
        # Check if we have signals from all required domains
        if set(signals_by_domain.keys()) != required_domains:
            return None
        
        # Calculate combined severity
        all_signals = [s for signals in signals_by_domain.values() for s in signals]
        max_severity = self._get_max_severity(all_signals)
        boosted_severity = self._boost_severity(max_severity, pattern.get("severity_boost", 0))
        
        # Create correlated issue
        return CorrelatedIssue(
            domains_affected=list(signals_by_domain.keys()),
            primary_domain=new_signal.domain,
            severity=boosted_severity,
            session_id=new_signal.session_id,
            player_id=new_signal.player_id,
            signals=all_signals,
            pattern=pattern["name"],
            description=pattern["description"],
            recommended_action=self._get_recommended_action(pattern["name"], boosted_severity)
        )
    
    def _get_max_severity(self, signals: List[DomainSignal]) -> str:
        """Get the highest severity from a list of signals."""
        severity_order = ["low", "medium", "high", "critical"]
        max_index = 0
        
        for signal in signals:
            try:
                index = severity_order.index(signal.severity)
                max_index = max(max_index, index)
            except ValueError:
                pass
        
        return severity_order[max_index]
    
    def _boost_severity(self, severity: str, boost: int) -> str:
        """Increase severity by boost levels."""
        severity_order = ["low", "medium", "high", "critical"]
        try:
            index = severity_order.index(severity)
            new_index = min(index + boost, len(severity_order) - 1)
            return severity_order[new_index]
        except ValueError:
            return severity
    
    def _get_recommended_action(self, pattern_name: str, severity: str) -> str:
        """Get recommended action based on pattern and severity."""
        actions = {
            "content_audio_mismatch": {
                "low": "flag_for_review",
                "medium": "adjust_audio_filtering", 
                "high": "mute_problematic_audio",
                "critical": "emergency_content_swap"
            },
            "narrative_content_violation": {
                "low": "log_for_analysis",
                "medium": "adjust_narrative_path",
                "high": "emergency_narrative_branch",
                "critical": "immediate_scene_skip"
            },
            "multimodal_horror_overload": {
                "low": "reduce_intensity",
                "medium": "apply_comfort_filters",
                "high": "emergency_tone_shift",
                "critical": "immediate_safe_mode"
            },
            "player_distress_pattern": {
                "low": "monitor_closely",
                "medium": "offer_comfort_options",
                "high": "auto_apply_comfort_mode",
                "critical": "emergency_pause_and_check"
            },
            "localization_content_mismatch": {
                "low": "log_for_loc_team",
                "medium": "use_safer_translation",
                "high": "revert_to_original",
                "critical": "disable_locale"
            }
        }
        
        pattern_actions = actions.get(pattern_name, {})
        return pattern_actions.get(severity, "review_required")
    
    async def get_active_issues(
        self,
        session_id: Optional[UUID] = None,
        player_id: Optional[UUID] = None,
    ) -> List[CorrelatedIssue]:
        """Get active correlated issues, optionally filtered."""
        async with self._lock:
            issues = list(self._active_issues.values())
            
            if session_id:
                issues = [i for i in issues if i.session_id == session_id]
            elif player_id:
                issues = [i for i in issues if i.player_id == player_id]
            
            # Clean up old issues
            cutoff = datetime.utcnow() - timedelta(hours=1)
            self._active_issues = {
                k: v for k, v in self._active_issues.items()
                if v.created_at > cutoff
            }
            
            return issues
    
    async def get_domain_stats(self) -> Dict[str, Any]:
        """Get statistics about domain signals and correlations."""
        async with self._lock:
            total_signals = sum(
                len(signals) 
                for signals in self._session_signals.values()
            )
            
            domain_counts = defaultdict(int)
            severity_counts = defaultdict(int)
            
            for signals in self._session_signals.values():
                for signal in signals:
                    domain_counts[signal.domain] += 1
                    severity_counts[signal.severity] += 1
            
            pattern_counts = defaultdict(int)
            for issue in self._active_issues.values():
                pattern_counts[issue.pattern] += 1
            
            return {
                "total_signals": total_signals,
                "active_sessions": len(self._session_signals),
                "active_issues": len(self._active_issues),
                "signals_by_domain": dict(domain_counts),
                "signals_by_severity": dict(severity_counts),
                "issues_by_pattern": dict(pattern_counts),
            }

