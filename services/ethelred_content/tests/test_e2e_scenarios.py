"""
End-to-End Content Governance Scenario Tests
============================================

Tests complete flows from Settings → Guardrails → Ethelred content validation,
verifying that different player profiles experience appropriate content filtering.
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from services.ethelred_content.content_models import ContentObservation
from services.ethelred_content.content_validator import (
    TextContentClassifier,
    ContentContextCrossChecker,
    ContentViolationEngine,
)
from services.ethelred_coordinator.domain_correlator import (
    DomainCorrelator,
    DomainSignal,
    QADomain,
)
from services.guardrails.guardrails_monitor import (
    GuardrailsMonitor,
    ContentModerationRequest,
)
from services.guardrails.policy_cache import PolicyCache
from services.settings.content_schemas import (
    CategoryLevels,
    ContentProfile,
    SessionContentPolicySnapshot,
)


class E2ETestHarness:
    """Test harness for end-to-end content governance scenarios."""
    
    def __init__(self):
        # Mock NATS connections
        self.mock_nats = AsyncMock()
        self.mock_redis = AsyncMock()
        
        # Services
        self.guardrails = GuardrailsMonitor(
            nats_url="nats://mock",
            redis_url="redis://mock"
        )
        self.guardrails.nc = self.mock_nats
        self.guardrails.policy_cache = PolicyCache("redis://mock")
        
        self.text_classifier = TextContentClassifier()
        self.cross_checker = ContentContextCrossChecker()
        self.violation_engine = ContentViolationEngine()
        
        self.correlator = DomainCorrelator()
        
        # Test data
        self.teen_player = uuid4()
        self.mature_player = uuid4()
        self.session_teen = uuid4()
        self.session_mature = uuid4()
        
        # Policies
        self.teen_policy = SessionContentPolicySnapshot(
            session_id=self.session_teen,
            player_id=self.teen_player,
            base_profile="TeenSafe",
            effective_levels={
                "violence_gore": 1,
                "language_profanity": 1,
                "horror_intensity": 1,
                "sexual_content_nudity": 0,
                "drugs_substances": 0,
                "sensitive_themes": 1,
                "moral_complexity": 2,
            },
            policy_version=1,
            created_at=datetime.utcnow(),
        )
        
        self.mature_policy = SessionContentPolicySnapshot(
            session_id=self.session_mature,
            player_id=self.mature_player,
            base_profile="MatureFullExperience",
            effective_levels={
                "violence_gore": 4,
                "language_profanity": 4,
                "horror_intensity": 4,
                "sexual_content_nudity": 3,
                "drugs_substances": 3,
                "sensitive_themes": 4,
                "moral_complexity": 4,
            },
            policy_version=1,
            created_at=datetime.utcnow(),
        )
    
    async def setup(self):
        """Initialize test harness."""
        # Mock Redis connection for policy cache
        with patch('aioredis.from_url', return_value=self.mock_redis):
            await self.guardrails.policy_cache.connect()
        
        # Pre-cache policies
        await self.guardrails.policy_cache.set_policy(
            self.session_teen, self.teen_policy
        )
        await self.guardrails.policy_cache.set_policy(
            self.session_mature, self.mature_policy
        )
    
    async def run_content_through_pipeline(
        self,
        session_id: UUID,
        player_id: UUID,
        content: str,
        content_type: str = "text",
    ) -> Dict[str, Any]:
        """Run content through the full pipeline and collect results."""
        results = {
            "guardrails_response": None,
            "content_observations": [],
            "violations": [],
            "correlated_issues": [],
        }
        
        # Step 1: Guardrails pre-moderation
        mod_request = ContentModerationRequest(
            session_id=session_id,
            player_id=player_id,
            content_type=content_type,
            content=content,
        )
        
        results["guardrails_response"] = await self.guardrails.moderate_content(
            mod_request
        )
        
        # Step 2: Content classification (if allowed through)
        if results["guardrails_response"].allowed:
            if content_type == "text":
                observation = await self.text_classifier.classify_text(
                    session_id=session_id,
                    text=content,
                    player_id=player_id,
                )
                results["content_observations"].append(observation)
            
            # Step 3: Violation detection
            policy = await self.guardrails.get_policy_for_session(session_id)
            if policy and results["content_observations"]:
                violations = await self.violation_engine.evaluate(
                    observation=results["content_observations"][0],
                    policy=policy,
                )
                results["violations"] = violations
                
                # Step 4: Send to correlator
                for violation in violations:
                    signal = DomainSignal(
                        domain=QADomain.CONTENT,
                        signal_type="violation",
                        severity=violation.severity,
                        session_id=session_id,
                        player_id=player_id,
                        details={
                            "category": violation.category,
                            "expected": violation.expected_level,
                            "observed": violation.observed_level,
                        },
                    )
                    
                    issue = await self.correlator.add_signal(signal)
                    if issue:
                        results["correlated_issues"].append(issue)
        
        return results


@pytest.mark.asyncio
class TestContentGovernanceE2E:
    """End-to-end scenario tests for content governance."""
    
    async def test_teen_safe_vs_mature_horror_content(self):
        """Test how teen-safe vs mature profiles handle horror content."""
        harness = E2ETestHarness()
        await harness.setup()
        
        # Horror content that should trigger different responses
        horror_content = (
            "The room was filled with blood and dismembered bodies. "
            "A terrifying scream echoed as the creature tore through flesh."
        )
        
        # Run for teen player
        teen_results = await harness.run_content_through_pipeline(
            session_id=harness.session_teen,
            player_id=harness.teen_player,
            content=horror_content,
        )
        
        # Run for mature player
        mature_results = await harness.run_content_through_pipeline(
            session_id=harness.session_mature,
            player_id=harness.mature_player,
            content=horror_content,
        )
        
        # Verify teen player experience
        assert not teen_results["guardrails_response"].allowed
        assert len(teen_results["guardrails_response"].violations) > 0
        assert any(
            v["category"] == "violence_gore"
            for v in teen_results["guardrails_response"].violations
        )
        
        # Verify mature player experience
        assert mature_results["guardrails_response"].allowed
        assert len(mature_results["violations"]) == 0  # Within their limits
        assert mature_results["guardrails_response"].modified_content is not None
    
    async def test_profanity_filtering_levels(self):
        """Test profanity filtering at different levels."""
        harness = E2ETestHarness()
        await harness.setup()
        
        # Profane content
        profane_content = "What the fuck is this shit? This game is fucking amazing!"
        
        # Run for teen player
        teen_results = await harness.run_content_through_pipeline(
            session_id=harness.session_teen,
            player_id=harness.teen_player,
            content=profane_content,
        )
        
        # Verify filtering occurred
        assert not teen_results["guardrails_response"].allowed
        # In real implementation, would check for masked/filtered content
        
        # Run for mature player
        mature_results = await harness.run_content_through_pipeline(
            session_id=harness.session_mature,
            player_id=harness.mature_player,
            content=profane_content,
        )
        
        # Verify no filtering for mature
        assert mature_results["guardrails_response"].allowed
        assert mature_results["guardrails_response"].modified_content == profane_content
    
    async def test_multi_domain_correlation(self):
        """Test correlation of content violations with other domains."""
        harness = E2ETestHarness()
        await harness.setup()
        
        session_id = harness.session_teen
        player_id = harness.teen_player
        
        # First, trigger a content violation
        horror_content = "Blood and gore everywhere, screaming in terror!"
        content_results = await harness.run_content_through_pipeline(
            session_id=session_id,
            player_id=player_id,
            content=horror_content,
        )
        
        # Simulate an audio domain signal
        audio_signal = DomainSignal(
            domain=QADomain.AUDIO,
            signal_type="quality_issue",
            severity="high",
            session_id=session_id,
            player_id=player_id,
            details={
                "issue": "screaming_audio",
                "intensity": 0.9,
            },
        )
        
        # Add audio signal to correlator
        correlated_issue = await harness.correlator.add_signal(audio_signal)
        
        # Should detect content-audio mismatch pattern
        assert correlated_issue is not None
        assert correlated_issue.pattern == "content_audio_mismatch"
        assert QADomain.CONTENT in correlated_issue.domains_affected
        assert QADomain.AUDIO in correlated_issue.domains_affected
        assert correlated_issue.severity in ["high", "critical"]
    
    async def test_safe_content_no_violations(self):
        """Test that appropriate content generates no violations."""
        harness = E2ETestHarness()
        await harness.setup()
        
        # Safe content for all audiences
        safe_content = "The player explored the sunny meadow, collecting flowers."
        
        # Run for both players
        for session_id, player_id in [
            (harness.session_teen, harness.teen_player),
            (harness.session_mature, harness.mature_player),
        ]:
            results = await harness.run_content_through_pipeline(
                session_id=session_id,
                player_id=player_id,
                content=safe_content,
            )
            
            assert results["guardrails_response"].allowed
            assert len(results["violations"]) == 0
            assert len(results["correlated_issues"]) == 0
    
    async def test_policy_version_mismatch_handling(self):
        """Test handling of policy version mismatches."""
        harness = E2ETestHarness()
        await harness.setup()
        
        # Update teen policy with new version
        updated_policy = SessionContentPolicySnapshot(
            **harness.teen_policy.dict(),
            policy_version=2,
            effective_levels={
                **harness.teen_policy.effective_levels,
                "violence_gore": 0,  # Even more restrictive
            }
        )
        
        await harness.guardrails.policy_cache.set_policy(
            harness.session_teen, updated_policy
        )
        
        # Mild violence content
        mild_violence = "The character punched the enemy."
        
        results = await harness.run_content_through_pipeline(
            session_id=harness.session_teen,
            player_id=harness.teen_player,
            content=mild_violence,
        )
        
        # Should now be blocked with updated policy
        assert not results["guardrails_response"].allowed


@pytest.mark.asyncio
async def test_red_alert_integration():
    """Test that critical violations trigger Red Alert."""
    harness = E2ETestHarness()
    await harness.setup()
    
    # Track published messages
    published_messages = []
    
    async def mock_publish(topic: str, data: bytes):
        published_messages.append((topic, data))
    
    harness.mock_nats.publish = mock_publish
    
    # Extreme content that should trigger critical alert
    extreme_content = "Extreme violence, gore, and dismemberment!"
    
    # Process through pipeline
    results = await harness.run_content_through_pipeline(
        session_id=harness.session_teen,
        player_id=harness.teen_player,
        content=extreme_content,
    )
    
    # Check that violation event was published
    violation_publishes = [
        msg for topic, msg in published_messages
        if topic == "ethelred.content.violation_detected"
    ]
    
    assert len(violation_publishes) > 0
