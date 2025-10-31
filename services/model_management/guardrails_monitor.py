"""
Guardrails Monitor - Monitors all model outputs for safety.
Ensures immersive/addictive but NOT harmful.
"""

import json
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from services.state_manager.connection_pool import PostgreSQLPool


class MonitoringResults:
    """Container for monitoring results."""
    
    def __init__(self):
        self.compliant = True
        self.safety = {}
        self.addiction_metrics = {}
        self.harmful_content = {}
        self.violations = []
        self.intervention_triggered = False
        self.details = {}


class GuardrailsMonitor:
    """
    Monitors all models to ensure guardrails compliance.
    
    Key Principle: Immersive/addictive but NOT harmful to humans in real life.
    
    Monitors:
    - Safety: No harmful content
    - Addiction metrics: Engagement vs harmful addiction
    - Ethical compliance: Fair, non-discriminatory
    - Content appropriateness: Age-appropriate, rating-compliant
    """
    
    def __init__(self, db_pool: Optional[PostgreSQLPool] = None):
        self.db_pool = db_pool
    
    async def monitor_outputs(self, model_id: str, outputs: List[str]) -> Dict[str, Any]:
        """
        Monitor model outputs for guardrails compliance.
        
        Checks:
        1. Safety: No harmful content
        2. Addiction metrics: Engagement vs harmful addiction
        3. Harmful content detection
        4. Content appropriateness
        
        Args:
            model_id: ID of model being monitored
            outputs: List of model outputs to check
        
        Returns:
            MonitoringResults with compliance status
        """
        results = MonitoringResults()
        
        try:
            # 1. Safety checks
            safety_results = await self._check_safety(outputs)
            results.safety = safety_results
            
            # 2. Addiction metrics
            addiction_results = await self._analyze_engagement(outputs)
            results.addiction_metrics = addiction_results
            
            # 3. Harmful content detection
            harmful_results = await self._detect_harmful_content(outputs)
            results.harmful_content = harmful_results
            
            # Overall compliance assessment
            results.compliant = (
                safety_results.get('passed', False) and
                addiction_results.get('healthy_engagement', False) and
                not harmful_results.get('detected', False)
            )
            
            # Collect violations
            if not safety_results.get('passed', False):
                results.violations.append({
                    'type': 'safety',
                    'severity': safety_results.get('severity', 'medium'),
                    'details': safety_results.get('details', {})
                })
            
            if not addiction_results.get('healthy_engagement', False):
                results.violations.append({
                    'type': 'addiction',
                    'severity': 'medium' if addiction_results.get('unhealthy_score', 0) > 0.5 else 'low',
                    'details': addiction_results.get('details', {})
                })
            
            if harmful_results.get('detected', False):
                results.violations.append({
                    'type': 'harmful_content',
                    'severity': harmful_results.get('severity', 'high'),
                    'details': harmful_results.get('details', {})
                })
            
            # Store violations if any
            if results.violations:
                await self._store_violations(model_id, results.violations)
            
            # Auto-intervention if non-compliant
            if not results.compliant:
                results.intervention_triggered = True
                await self._trigger_intervention(model_id, results)
            
            results.details = {
                'outputs_checked': len(outputs),
                'compliance_score': self._calculate_compliance_score(results)
            }
            
        except Exception as e:
            results.compliant = False
            results.details['error'] = str(e)
        
        return results.__dict__
    
    async def _check_safety(self, outputs: List[str]) -> Dict[str, Any]:
        """
        Check safety of outputs.
        
        Checks for:
        - Harmful content
        - Dangerous instructions
        - Self-harm references
        - Violence
        - Illegal activities
        """
        # Placeholder implementation
        # Production implementation would:
        # 1. Use moderation APIs (OpenAI, Perspective, etc.)
        # 2. Custom safety rule engine
        # 3. Content classification models
        # 4. Keyword-based filtering
        
        passed = True
        issues = []
        
        # Basic keyword checks (placeholder)
        harmful_keywords = ['kill yourself', 'commit suicide', 'harm others']
        for output in outputs:
            lower_output = output.lower()
            for keyword in harmful_keywords:
                if keyword in lower_output:
                    passed = False
                    issues.append({
                        'keyword': keyword,
                        'severity': 'critical'
                    })
        
        return {
            'passed': passed,
            'severity': 'critical' if issues else 'none',
            'issues': issues,
            'details': {
                'checked_count': len(outputs)
            }
        }
    
    async def _analyze_engagement(self, outputs: List[str]) -> Dict[str, Any]:
        """
        Analyze if outputs encourage healthy or harmful engagement.
        
        Healthy Engagement:
        - Players return regularly but not obsessively
        - Players take breaks
        - Players have healthy balance
        
        Harmful Addiction:
        - Players unable to stop
        - Players neglect real-life responsibilities
        - Players show signs of distress when unable to play
        """
        healthy_indicators = 0
        unhealthy_indicators = 0
        
        for output in outputs:
            lower_output = output.lower()
            
            # Check for healthy engagement patterns
            if self._encourages_breaks(lower_output):
                healthy_indicators += 1
            if self._acknowledges_real_life(lower_output):
                healthy_indicators += 1
            if self._has_respectful_boundaries(lower_output):
                healthy_indicators += 1
            
            # Check for unhealthy patterns
            if self._uses_manipulation(lower_output):
                unhealthy_indicators += 1
            if self._creates_fomo(lower_output):
                unhealthy_indicators += 1
            if self._encourages_obsession(lower_output):
                unhealthy_indicators += 1
        
        # Calculate scores
        total_checks = len(outputs) * 3
        healthy_score = healthy_indicators / total_checks if total_checks > 0 else 0.0
        unhealthy_score = unhealthy_indicators / total_checks if total_checks > 0 else 0.0
        
        return {
            'healthy_engagement': healthy_score >= 0.7,
            'unhealthy_patterns_detected': unhealthy_score > 0.3,
            'healthy_score': healthy_score,
            'unhealthy_score': unhealthy_score,
            'recommendation': 'continue' if healthy_score >= 0.7 else 'intervene',
            'details': {
                'healthy_indicators': healthy_indicators,
                'unhealthy_indicators': unhealthy_indicators,
                'total_checks': total_checks
            }
        }
    
    def _encourages_breaks(self, output: str) -> bool:
        """Check if output encourages taking breaks."""
        break_keywords = ['take a break', 'rest', 'pause', 'step away', 'balance']
        return any(keyword in output for keyword in break_keywords)
    
    def _acknowledges_real_life(self, output: str) -> bool:
        """Check if output acknowledges real-life responsibilities."""
        real_life_keywords = ['real world', 'real life', 'responsibilities', 'priority', 'important']
        return any(keyword in output for keyword in real_life_keywords)
    
    def _has_respectful_boundaries(self, output: str) -> bool:
        """Check if output has respectful boundaries."""
        boundary_keywords = ['when you ready', 'at your own pace', 'your choice', 'your decision']
        return any(keyword in output for keyword in boundary_keywords)
    
    def _uses_manipulation(self, output: str) -> bool:
        """Check if output uses manipulation techniques."""
        manipulation_keywords = ['you must', 'need to', 'have to', 'everyone else is', 'don\'t miss']
        return any(keyword in output for keyword in manipulation_keywords)
    
    def _creates_fomo(self, output: str) -> bool:
        """Check if output creates fear of missing out."""
        fomo_keywords = ['limited time', 'expires soon', 'last chance', 'can\'t wait', 'must act now']
        return any(keyword in output for keyword in fomo_keywords)
    
    def _encourages_obsession(self, output: str) -> bool:
        """Check if output encourages obsession."""
        obsession_keywords = ['never stop', 'always play', 'can\'t stop', 'addicted', 'obsessed']
        return any(keyword in output for keyword in obsession_keywords)
    
    async def _detect_harmful_content(self, outputs: List[str]) -> Dict[str, Any]:
        """
        Detect harmful content in outputs.
        
        Checks for:
        - Extremist content
        - Hate speech
        - Discriminatory language
        - Dangerous misinformation
        """
        detected = False
        severity = 'none'
        issues = []
        
        # Placeholder implementation
        # Production implementation would use:
        # - Content moderation APIs
        # - Toxicity detection models
        # - Hate speech classifiers
        
        # Basic keyword checks
        harmful_keywords = {
            'critical': ['violence', 'terror', 'hate'],
            'high': ['discrimination', 'harassment'],
            'medium': ['misinformation']
        }
        
        for output in outputs:
            lower_output = output.lower()
            for sev, keywords in harmful_keywords.items():
                if any(keyword in lower_output for keyword in keywords):
                    detected = True
                    severity = sev
                    issues.append({
                        'severity': sev,
                        'output_sample': output[:100]
                    })
        
        return {
            'detected': detected,
            'severity': severity,
            'issues': issues,
            'details': {}
        }
    
    async def _store_violations(self, model_id: str, violations: List[Dict[str, Any]]) -> None:
        """Store violations in database."""
        if not self.db_pool:
            return
        
        try:
            async with self.db_pool.get_connection() as conn:
                for violation in violations:
                    query = """
                        INSERT INTO guardrails_violations (
                            violation_id, model_id, violation_type, severity,
                            violation_details, output_sample, intervention_taken
                        ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """
                    
                    await conn.execute(
                        query,
                        uuid4(),
                        UUID(model_id) if isinstance(model_id, str) else model_id,
                        violation['type'],
                        violation['severity'],
                        json.dumps(violation['details']),
                        violation.get('output_sample', ''),
                        'triggered'
                    )
        except Exception as e:
            print(f"Error storing violations: {e}")
    
    async def _trigger_intervention(self, model_id: str, results: MonitoringResults) -> None:
        """
        Trigger intervention when guardrails violated.
        
        Interventions:
        - Block harmful outputs
        - Adjust model parameters
        - Retrain model if persistent issues
        - Rollback model if severe violations
        """
        # Determine severity
        max_severity = 'low'
        for violation in results.violations:
            severity = violation.get('severity', 'low')
            if severity == 'critical':
                max_severity = 'critical'
            elif severity == 'high' and max_severity != 'critical':
                max_severity = 'high'
            elif severity == 'medium' and max_severity not in ['critical', 'high']:
                max_severity = 'medium'
        
        print(f"Guardrails violation detected for model {model_id}, severity: {max_severity}")
        
        # Placeholder intervention logic
        # Production implementation would:
        # 1. For critical: Immediate rollback via RollbackManager
        # 2. For high: Block outputs, adjust parameters
        # 3. For medium: Log and monitor closely
        # 4. Trigger retraining if persistent
        
        if max_severity in ['critical', 'high']:
            print(f"Severe violation - intervention required for model {model_id}")
            # TODO: Implement actual intervention (rollback, blocking, etc.)
    
    def _calculate_compliance_score(self, results: MonitoringResults) -> float:
        """Calculate overall compliance score."""
        if results.compliant:
            return 1.0
        
        # Weighted score based on severity
        weights = {'critical': 0.0, 'high': 0.3, 'medium': 0.6, 'low': 0.8}
        base_score = 1.0
        
        for violation in results.violations:
            severity = violation.get('severity', 'low')
            base_score = min(base_score, weights.get(severity, 0.5))
        
        return base_score

