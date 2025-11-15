"""
Ethelred Coordinator Service
============================

Main service that orchestrates multi-domain QA correlation and feeds
Red Alert dashboards with critical quality issues.
"""

from __future__ import annotations

import asyncio
import json
from typing import Optional, Dict, Any
from uuid import UUID

import nats
from loguru import logger

from .domain_correlator import DomainCorrelator, DomainSignal, QADomain, CorrelatedIssue


class EthelredCoordinator:
    """
    Central hub for ETHELRED system coordination.
    
    Subscribes to signals from all QA domains and performs
    real-time correlation to identify multi-domain issues.
    """
    
    def __init__(
        self,
        nats_url: str,
        redis_url: str,
        service_name: str = "ethelred-coordinator"
    ):
        self.nats_url = nats_url
        self.redis_url = redis_url
        self.service_name = service_name
        
        self.nc: Optional[nats.NATS] = None
        self.correlator = DomainCorrelator()
        
        # Track Red Alert publishing
        self._red_alert_batch: list[CorrelatedIssue] = []
        self._batch_lock = asyncio.Lock()
    
    async def start(self) -> None:
        """Start the coordinator service."""
        self.nc = await nats.connect(self.nats_url)
        
        # Subscribe to domain-specific signals
        await self._subscribe_to_domains()
        
        # Start Red Alert batch publisher
        asyncio.create_task(self._red_alert_publisher())
        
        logger.info(f"{self.service_name} started")
    
    async def stop(self) -> None:
        """Stop the service gracefully."""
        if self.nc:
            await self.nc.close()
        logger.info(f"{self.service_name} stopped")
    
    async def _subscribe_to_domains(self) -> None:
        """Subscribe to all QA domain signal streams."""
        # Content Governance
        await self.nc.subscribe(
            "ethelred.content.violation_detected",
            cb=lambda msg: self._handle_domain_signal(msg, QADomain.CONTENT)
        )
        
        # Story Memory
        await self.nc.subscribe(
            "ethelred.story.drift_detected",
            cb=lambda msg: self._handle_domain_signal(msg, QADomain.STORY)
        )
        
        # 4D Vision (placeholder)
        await self.nc.subscribe(
            "ethelred.vision.quality_issue",
            cb=lambda msg: self._handle_domain_signal(msg, QADomain.VISION_4D)
        )
        
        # Audio (placeholder)
        await self.nc.subscribe(
            "ethelred.audio.quality_issue",
            cb=lambda msg: self._handle_domain_signal(msg, QADomain.AUDIO)
        )
        
        # Engagement Analytics
        await self.nc.subscribe(
            "events.ethelred.emo.v1.engagement_metrics",
            cb=lambda msg: self._handle_domain_signal(msg, QADomain.ENGAGEMENT)
        )
        await self.nc.subscribe(
            "events.ethelred.emo.v1.addiction_risk",
            cb=lambda msg: self._handle_domain_signal(msg, QADomain.ENGAGEMENT)
        )
        await self.nc.subscribe(
            "events.ethelred.emo.v1.severe_risk_alert",
            cb=lambda msg: self._handle_domain_signal(msg, QADomain.ENGAGEMENT)
        )
        
        # Multi-Language (placeholder)
        await self.nc.subscribe(
            "ethelred.language.translation_issue",
            cb=lambda msg: self._handle_domain_signal(msg, QADomain.LANGUAGE)
        )
        
        logger.info("Subscribed to all QA domain signals")
    
    async def _handle_domain_signal(self, msg: nats.Msg, domain: QADomain) -> None:
        """Process a signal from a QA domain."""
        try:
            data = json.loads(msg.data.decode())
            
            # Map domain-specific data to generic signal
            signal = self._map_to_domain_signal(data, domain)
            
            # Add to correlator
            correlated_issue = await self.correlator.add_signal(signal)
            
            if correlated_issue:
                logger.warning(
                    f"Correlated issue detected: {correlated_issue.pattern} "
                    f"(severity: {correlated_issue.severity})"
                )
                
                # Queue for Red Alert
                async with self._batch_lock:
                    self._red_alert_batch.append(correlated_issue)
                
                # Publish immediate alert for critical issues
                if correlated_issue.severity == "critical":
                    await self._publish_critical_alert(correlated_issue)
            
        except Exception as e:
            logger.error(f"Failed to process {domain} signal: {e}")
    
    def _map_to_domain_signal(self, data: Dict[str, Any], domain: QADomain) -> DomainSignal:
        """Map domain-specific event data to generic signal format."""
        # Common fields
        session_id = data.get("session_id")
        if session_id:
            session_id = UUID(session_id)
        
        player_id = data.get("player_id")
        if player_id:
            player_id = UUID(player_id)
        
        # Domain-specific mapping
        if domain == QADomain.CONTENT:
            # Content violation event
            violations = data.get("violations", [])
            if violations:
                # Use highest severity violation
                severities = [v.get("severity", "medium") for v in violations]
                severity_map = {"medium": 1, "high": 2, "critical": 3}
                max_severity_val = max(severity_map.get(s, 1) for s in severities)
                severity = ["medium", "high", "critical"][max_severity_val - 1]
            else:
                severity = "medium"
            
            return DomainSignal(
                domain=domain,
                signal_type="violation",
                severity=severity,
                session_id=session_id,
                player_id=player_id,
                details={
                    "violations": violations,
                    "content_type": data.get("content_type"),
                    "category": violations[0].get("category") if violations else None
                },
                evidence_refs=data.get("evidence_refs", [])
            )
        
        elif domain == QADomain.STORY:
            # Story drift event
            drift_score = data.get("drift_score", 0.5)
            if drift_score > 0.8:
                severity = "critical"
            elif drift_score > 0.6:
                severity = "high"
            elif drift_score > 0.4:
                severity = "medium"
            else:
                severity = "low"
            
            return DomainSignal(
                domain=domain,
                signal_type="drift",
                severity=severity,
                session_id=session_id,
                player_id=player_id,
                details={
                    "drift_type": data.get("drift_type"),
                    "drift_score": drift_score,
                    "description": data.get("description")
                }
            )
        
        elif domain == QADomain.ENGAGEMENT:
            # Engagement analytics events
            issue_type = data.get("issue_type", "")
            severity = data.get("severity", "INFO").lower()
            
            # Map INFO/WARNING/ERROR/CRITICAL to our scale
            severity_map = {
                "info": "low",
                "warning": "medium", 
                "error": "high",
                "critical": "critical"
            }
            severity = severity_map.get(severity, "medium")
            
            # Handle different engagement event types
            if "ADDICTION_RISK" in issue_type:
                payload = data.get("payload", {})
                risk_level = payload.get("risk_level", "healthy")
                
                # Map addiction risk levels to severity
                if risk_level == "severe":
                    severity = "critical"
                elif risk_level == "concerning":
                    severity = "high"
                elif risk_level == "moderate":
                    severity = "medium"
                else:
                    severity = "low"
                
                return DomainSignal(
                    domain=domain,
                    signal_type="addiction_risk",
                    severity=severity,
                    session_id=session_id,
                    player_id=player_id,
                    details={
                        "risk_level": risk_level,
                        "risk_factors": payload.get("risk_factors", []),
                        "cohort": payload.get("cohort_identifier", {}),
                        "sample_size": payload.get("sample_size", 0)
                    }
                )
            
            elif "ENGAGEMENT_METRICS" in issue_type:
                payload = data.get("payload", {})
                aggregate_type = payload.get("aggregate_type", "")
                
                # Check for concerning patterns
                signal_type = "engagement_metric"
                if aggregate_type == "npc_attachment" and payload.get("attachment_score", 1.0) < 0.2:
                    signal_type = "low_engagement"
                    severity = "medium"
                elif aggregate_type == "moral_tension" and payload.get("tension_score", 0) > 0.8:
                    signal_type = "high_tension"
                    severity = "medium"
                
                return DomainSignal(
                    domain=domain,
                    signal_type=signal_type,
                    severity=severity,
                    session_id=session_id,
                    player_id=player_id,
                    details=payload
                )
            
            else:
                # Generic engagement signal
                return DomainSignal(
                    domain=domain,
                    signal_type=issue_type.lower().replace(".", "_"),
                    severity=severity,
                    session_id=session_id,
                    player_id=player_id,
                    details=data.get("payload", {})
                )
        
        else:
            # Generic mapping for other domains (placeholders)
            return DomainSignal(
                domain=domain,
                signal_type=data.get("signal_type", "quality_issue"),
                severity=data.get("severity", "medium"),
                session_id=session_id,
                player_id=player_id,
                details=data.get("details", {})
            )
    
    async def _publish_critical_alert(self, issue: CorrelatedIssue) -> None:
        """Immediately publish critical alerts to Red Alert."""
        alert_data = {
            "alert_type": "multi_domain_critical",
            "issue_id": str(issue.issue_id),
            "pattern": issue.pattern,
            "severity": issue.severity,
            "domains_affected": issue.domains_affected,
            "session_id": str(issue.session_id) if issue.session_id else None,
            "player_id": str(issue.player_id) if issue.player_id else None,
            "description": issue.description,
            "recommended_action": issue.recommended_action,
            "signal_count": len(issue.signals),
            "timestamp": issue.created_at.isoformat()
        }
        
        await self.nc.publish(
            "red_alert.critical.multi_domain",
            json.dumps(alert_data).encode()
        )
        
        logger.critical(f"Published critical Red Alert: {issue.pattern}")
    
    async def _red_alert_publisher(self) -> None:
        """Periodically publish batch alerts to Red Alert dashboard."""
        while True:
            await asyncio.sleep(30)  # Batch every 30 seconds
            
            async with self._batch_lock:
                if not self._red_alert_batch:
                    continue
                
                # Group by severity
                by_severity: Dict[str, list] = {
                    "low": [],
                    "medium": [],
                    "high": [],
                    "critical": []
                }
                
                for issue in self._red_alert_batch:
                    by_severity[issue.severity].append({
                        "issue_id": str(issue.issue_id),
                        "pattern": issue.pattern,
                        "domains": issue.domains_affected,
                        "session_id": str(issue.session_id) if issue.session_id else None,
                        "description": issue.description
                    })
                
                # Publish batch
                batch_data = {
                    "batch_id": str(UUID()),
                    "timestamp": datetime.utcnow().isoformat(),
                    "total_issues": len(self._red_alert_batch),
                    "by_severity": by_severity,
                    "stats": await self.correlator.get_domain_stats()
                }
                
                await self.nc.publish(
                    "red_alert.batch.multi_domain",
                    json.dumps(batch_data).encode()
                )
                
                logger.info(
                    f"Published Red Alert batch: {len(self._red_alert_batch)} issues"
                )
                
                # Clear batch
                self._red_alert_batch.clear()
    
    async def handle_query(self, msg: nats.Msg) -> None:
        """Handle queries for active issues and stats."""
        try:
            data = json.loads(msg.data.decode())
            query_type = data.get("type", "active_issues")
            
            if query_type == "active_issues":
                session_id = data.get("session_id")
                if session_id:
                    session_id = UUID(session_id)
                
                issues = await self.correlator.get_active_issues(session_id=session_id)
                
                response = {
                    "issues": [
                        {
                            "issue_id": str(issue.issue_id),
                            "pattern": issue.pattern,
                            "severity": issue.severity,
                            "domains": issue.domains_affected,
                            "description": issue.description,
                            "signal_count": len(issue.signals)
                        }
                        for issue in issues
                    ]
                }
            
            elif query_type == "stats":
                response = await self.correlator.get_domain_stats()
            
            else:
                response = {"error": f"Unknown query type: {query_type}"}
            
            if msg.reply:
                await self.nc.publish(
                    msg.reply,
                    json.dumps(response).encode()
                )
        
        except Exception as e:
            logger.error(f"Failed to handle query: {e}")
            if msg.reply:
                await self.nc.publish(
                    msg.reply,
                    json.dumps({"error": str(e)}).encode()
                )


# Import at end to avoid circular dependency
from datetime import datetime
