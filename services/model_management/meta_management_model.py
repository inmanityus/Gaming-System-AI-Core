"""
Meta-Management Model - Orchestrates all model management.
Does NOT directly participate in player worlds.
"""

import asyncio
from typing import Any, Dict, List, Optional
from uuid import UUID

from services.state_manager.connection_pool import PostgreSQLPool
from services.model_management.model_registry import ModelRegistry
from services.model_management.deployment_manager import DeploymentManager
from services.model_management.rollback_manager import RollbackManager
from services.model_management.guardrails_monitor import GuardrailsMonitor


class OptimizationDecision:
    """Container for optimization decision."""
    
    def __init__(self):
        self.decision_type = "none"  # deploy_model, rollback, adjust_parameters, retrain
        self.target_model_id = None
        self.current_model_id = None
        self.reason = ""
        self.priority = "medium"  # low, medium, high, critical
        self.parameter_adjustments = {}


class MetaManagementModel:
    """
    Meta-management model that orchestrates all model operations.
    
    This model:
    - Does NOT directly participate in player worlds
    - Ensures best models at all times
    - Monitors and optimizes system
    - Enforces guardrails
    - Makes optimization decisions
    """
    
    def __init__(
        self,
        db_pool: Optional[PostgreSQLPool] = None,
        model_registry: Optional[ModelRegistry] = None,
        deployment_manager: Optional[DeploymentManager] = None,
        rollback_manager: Optional[RollbackManager] = None,
        guardrails_monitor: Optional[GuardrailsMonitor] = None
    ):
        self.db_pool = db_pool
        self.model_registry = model_registry or ModelRegistry(db_pool)
        self.deployment_manager = deployment_manager or DeploymentManager(db_pool, rollback_manager)
        self.rollback_manager = rollback_manager or RollbackManager(db_pool)
        self.guardrails_monitor = guardrails_monitor or GuardrailsMonitor(db_pool)
        self.running = False
        self.check_interval = 3600  # Check every hour
    
    async def run_optimization_loop(self):
        """
        Continuous optimization loop.
        
        Runs:
        - Model discovery checks
        - Performance monitoring
        - Guardrails enforcement
        - Optimization decisions
        - Automatic improvements
        """
        self.running = True
        print("Meta-Management Model: Starting optimization loop")
        
        while self.running:
            try:
                # 1. Check for better models
                print("Meta-Management: Checking for better models...")
                await self._check_for_better_models()
                
                # 2. Monitor current models
                print("Meta-Management: Monitoring current models...")
                monitoring_results = await self._monitor_all_models()
                
                # 3. Enforce guardrails
                print("Meta-Management: Enforcing guardrails...")
                guardrails_results = await self._check_all_models_guardrails()
                
                # 4. Make optimization decisions
                print("Meta-Management: Making optimization decisions...")
                decisions = await self._analyze_and_decide(monitoring_results, guardrails_results)
                
                # 5. Implement decisions
                if decisions:
                    print(f"Meta-Management: Implementing {len(decisions)} decisions...")
                    await self._implement_decisions(decisions)
                
                # 6. Wait before next cycle
                print(f"Meta-Management: Cycle complete. Next check in {self.check_interval}s")
                await asyncio.sleep(self.check_interval)
            
            except Exception as e:
                print(f"Meta-Management: Error in optimization loop: {e}")
                # Wait shorter time on error before retry
                await asyncio.sleep(60)
    
    async def _check_for_better_models(self) -> None:
        """
        Check all use cases for better models.
        """
        try:
            # Get all use cases
            use_cases = await self._get_all_use_cases()
            
            for use_case in use_cases:
                # Get current model
                current_model = await self.model_registry.get_current_model(use_case)
                if not current_model:
                    continue
                
                # Check for better models
                # NOTE: Actual implementation would call paid/self-hosted scanners
                # For now, this is a placeholder
                print(f"Checking for better models for use case: {use_case}")
                
        except Exception as e:
            print(f"Error checking for better models: {e}")
    
    async def _get_all_use_cases(self) -> List[str]:
        """Get all use cases from registry."""
        if not self.db_pool:
            return []
        
        try:
            async with self.db_pool.get_connection() as conn:
                query = "SELECT DISTINCT use_case FROM models WHERE status = 'current'"
                rows = await conn.fetch(query)
                return [row['use_case'] for row in rows]
        except Exception as e:
            print(f"Error getting use cases: {e}")
            return []
    
    async def _monitor_all_models(self) -> Dict[str, Any]:
        """
        Monitor all current models.
        
        Monitors:
        - Performance metrics
        - Error rates
        - Resource usage
        - User satisfaction
        """
        results = {}
        
        try:
            use_cases = await self._get_all_use_cases()
            
            for use_case in use_cases:
                current_model = await self.model_registry.get_current_model(use_case)
                if current_model:
                    # Get performance metrics
                    metrics = await self._get_model_performance_metrics(current_model['model_id'])
                    results[use_case] = {
                        'model_id': str(current_model['model_id']),
                        'metrics': metrics
                    }
            
        except Exception as e:
            print(f"Error monitoring models: {e}")
        
        return results
    
    async def _get_model_performance_metrics(self, model_id: UUID) -> Dict[str, Any]:
        """Get performance metrics for a model."""
        if not self.db_pool:
            return {}
        
        try:
            async with self.db_pool.get_connection() as conn:
                query = """
                    SELECT performance_metrics
                    FROM models
                    WHERE model_id = $1
                """
                row = await conn.fetchrow(query, model_id)
                if row and row['performance_metrics']:
                    return row['performance_metrics']
        except Exception as e:
            print(f"Error getting performance metrics: {e}")
        
        return {}
    
    async def _check_all_models_guardrails(self) -> Dict[str, Any]:
        """
        Check guardrails for all models.
        """
        results = {}
        
        try:
            use_cases = await self._get_all_use_cases()
            
            for use_case in use_cases:
                current_model = await self.model_registry.get_current_model(use_case)
                if current_model:
                    # Get recent outputs for guardrails check
                    outputs = await self._get_recent_outputs(current_model['model_id'], limit=10)
                    
                    # Check guardrails
                    guardrails_result = await self.guardrails_monitor.monitor_outputs(
                        str(current_model['model_id']),
                        outputs
                    )
                    
                    results[use_case] = guardrails_result
            
        except Exception as e:
            print(f"Error checking guardrails: {e}")
        
        return results
    
    async def _get_recent_outputs(self, model_id: UUID, limit: int = 10) -> List[str]:
        """Get recent model outputs for guardrails checking."""
        if not self.db_pool:
            return []
        
        try:
            async with self.db_pool.get_connection() as conn:
                query = """
                    SELECT generated_output
                    FROM model_historical_logs
                    WHERE model_id = $1
                    ORDER BY timestamp DESC
                    LIMIT $2
                """
                rows = await conn.fetch(query, model_id, limit)
                return [row['generated_output'] for row in rows]
        except Exception as e:
            print(f"Error getting recent outputs: {e}")
            return []
    
    async def _analyze_and_decide(
        self,
        monitoring_results: Dict[str, Any],
        guardrails_results: Dict[str, Any]
    ) -> List[OptimizationDecision]:
        """
        Analyze monitoring and guardrails results and make decisions.
        
        Decision types:
        - deploy_model: Deploy a new/better model
        - rollback: Rollback a problematic model
        - adjust_parameters: Adjust model configuration
        - retrain: Retrain model with new data
        """
        decisions = []
        
        try:
            # Check guardrails results for violations
            for use_case, guardrails_result in guardrails_results.items():
                if not guardrails_result.get('compliant', True):
                    # Guardrails violation detected
                    decision = OptimizationDecision()
                    decision.decision_type = "rollback"
                    decision.target_model_id = guardrails_result.get('model_id')
                    decision.reason = "Guardrails violation detected"
                    decision.priority = "critical" if any(
                        v.get('severity') == 'critical' for v in guardrails_result.get('violations', [])
                    ) else "high"
                    decisions.append(decision)
            
            # Check performance metrics
            for use_case, monitor_result in monitoring_results.items():
                metrics = monitor_result.get('metrics', {})
                
                # Check for performance degradation
                if self._performance_degraded(metrics):
                    decision = OptimizationDecision()
                    decision.decision_type = "adjust_parameters"
                    decision.target_model_id = monitor_result.get('model_id')
                    decision.reason = "Performance degradation detected"
                    decision.priority = "high"
                    decisions.append(decision)
            
        except Exception as e:
            print(f"Error analyzing and deciding: {e}")
        
        return decisions
    
    def _performance_degraded(self, metrics: Dict[str, Any]) -> bool:
        """Check if performance has degraded."""
        # Placeholder implementation
        # Production would check actual metrics
        return False
    
    async def _implement_decisions(self, decisions: List[OptimizationDecision]) -> None:
        """
        Implement optimization decisions.
        
        Decision types:
        - Deploy new model
        - Rollback model
        - Adjust model parameters
        - Retrain model
        """
        for decision in decisions:
            try:
                if decision.decision_type == "deploy_model":
                    if decision.target_model_id and decision.current_model_id:
                        await self.deployment_manager.deploy_model(
                            new_model_id=decision.target_model_id,
                            current_model_id=decision.current_model_id,
                            strategy="blue_green"
                        )
                        print(f"Deployed model {decision.target_model_id}")
                
                elif decision.decision_type == "rollback":
                    if decision.target_model_id:
                        success = await self.rollback_manager.rollback(
                            model_id=UUID(decision.target_model_id)
                        )
                        if success:
                            print(f"Rolled back model {decision.target_model_id}: {decision.reason}")
                
                elif decision.decision_type == "adjust_parameters":
                    if decision.target_model_id and decision.parameter_adjustments:
                        await self._adjust_model_parameters(
                            model_id=UUID(decision.target_model_id),
                            adjustments=decision.parameter_adjustments
                        )
                        print(f"Adjusted parameters for model {decision.target_model_id}")
                
                elif decision.decision_type == "retrain":
                    if decision.target_model_id:
                        print(f"Retraining model {decision.target_model_id}: {decision.reason}")
                        # TODO: Implement actual retraining
                
            except Exception as e:
                print(f"Error implementing decision: {e}")
    
    async def _adjust_model_parameters(
        self,
        model_id: UUID,
        adjustments: Dict[str, Any]
    ) -> None:
        """Adjust model parameters."""
        if not self.db_pool:
            return
        
        try:
            async with self.db_pool.get_connection() as conn:
                # Get current configuration
                query = "SELECT configuration FROM models WHERE model_id = $1"
                row = await conn.fetchrow(query, model_id)
                
                if row:
                    current_config = row['configuration'] or {}
                    current_config.update(adjustments)
                    
                    # Update configuration
                    update_query = "UPDATE models SET configuration = $1 WHERE model_id = $2"
                    await conn.execute(update_query, current_config, model_id)
                    print(f"Updated parameters for model {model_id}")
                    
        except Exception as e:
            print(f"Error adjusting parameters: {e}")
    
    async def stop(self):
        """Stop the optimization loop."""
        print("Meta-Management Model: Stopping optimization loop")
        self.running = False
