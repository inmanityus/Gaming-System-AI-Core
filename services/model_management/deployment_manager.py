"""
Deployment Manager - Manages model deployment with rollback.
Blue-green deployment, canary releases, automatic rollback.
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID, uuid4

from services.state_manager.connection_pool import PostgreSQLPool
from services.model_management.rollback_manager import RollbackManager


class DeploymentManager:
    """
    Manages model deployment with rollback capability.
    
    Supports multiple deployment strategies:
    - Blue-green: Run both models in parallel, shift traffic gradually
    - Canary: Small percentage of traffic to new model
    - All-at-once: Immediate switch (risky, not recommended)
    """
    
    def __init__(
        self, 
        db_pool: Optional[PostgreSQLPool] = None,
        rollback_manager: Optional[RollbackManager] = None
    ):
        self.db_pool = db_pool
        self.rollback_manager = rollback_manager or RollbackManager(db_pool)
        self.traffic_shifts = [10, 25, 50, 75, 100]  # Percentage increments
        self.monitoring_duration = 300  # 5 minutes per shift
    
    async def deploy_model(
        self, 
        new_model_id: str, 
        current_model_id: str, 
        strategy: str = "blue_green"
    ) -> bool:
        """
        Deploy new model using specified strategy.
        
        Args:
            new_model_id: ID of new model to deploy
            current_model_id: ID of current model to replace
            strategy: Deployment strategy (blue_green, canary, all_at_once)
        
        Returns:
            True if deployment successful, False if rolled back
        """
        try:
            # Convert to UUID if strings
            if isinstance(new_model_id, str):
                new_model_id = UUID(new_model_id)
            if isinstance(current_model_id, str):
                current_model_id = UUID(current_model_id)
            
            # Route to appropriate deployment strategy
            if strategy == "blue_green":
                return await self._blue_green_deploy(new_model_id, current_model_id)
            elif strategy == "canary":
                return await self._canary_deploy(new_model_id, current_model_id)
            elif strategy == "all_at_once":
                return await self._all_at_once_deploy(new_model_id, current_model_id)
            else:
                raise ValueError(f"Unknown deployment strategy: {strategy}")
        
        except Exception as e:
            print(f"Error deploying model {new_model_id}: {e}")
            return False
    
    async def _blue_green_deploy(
        self,
        new_model_id: UUID,
        current_model_id: UUID
    ) -> bool:
        """
        Blue-green deployment: run both models in parallel.
        
        Process:
        1. Create snapshot for rollback
        2. Deploy new model (green) alongside current (blue)
        3. Gradually shift traffic 10% → 25% → 50% → 75% → 100%
        4. Monitor for issues at each shift
        5. Rollback if issues detected
        6. Decommission old model if successful
        """
        deployment_id = None
        try:
            # Create deployment record
            deployment_id = await self._create_deployment_record(
                new_model_id=new_model_id,
                strategy="blue_green",
                status="in_progress"
            )
            
            # Create snapshot for rollback
            snapshot_id = await self.rollback_manager.create_snapshot(current_model_id)
            print(f"Created snapshot {snapshot_id} for potential rollback")
            
            # Deploy new model (green) alongside current (blue)
            await self._deploy_green_instance(new_model_id)
            print(f"Deployed green instance for model {new_model_id}")
            
            # Gradually shift traffic
            for shift_percent in self.traffic_shifts:
                print(f"Shifting traffic to {shift_percent}% for new model")
                
                # Shift traffic
                await self._shift_traffic(new_model_id, shift_percent)
                await self._update_deployment_traffic(deployment_id, shift_percent)
                
                # Monitor for issues
                print(f"Monitoring deployment for {self.monitoring_duration}s at {shift_percent}% traffic")
                await asyncio.sleep(self.monitoring_duration)
                
                issues = await self._detect_deployment_issues(new_model_id)
                
                if issues:
                    print(f"Issues detected at {shift_percent}% traffic - initiating rollback")
                    # Rollback immediately
                    rollback_success = await self.rollback_manager.rollback(current_model_id, snapshot_id)
                    await self._update_deployment_status(deployment_id, "rolled_back", issues)
                    return False
                
                print(f"✓ Traffic shift to {shift_percent}% completed successfully")
            
            # Complete deployment
            print("✓ All traffic shifts completed successfully")
            await self._decommission_blue_instance(current_model_id)
            await self._update_deployment_status(deployment_id, "completed")
            
            return True
        
        except Exception as e:
            print(f"Error during blue-green deployment: {e}")
            if deployment_id:
                await self._update_deployment_status(deployment_id, "failed", str(e))
            return False
    
    async def _canary_deploy(
        self,
        new_model_id: UUID,
        current_model_id: UUID
    ) -> bool:
        """
        Canary deployment: small percentage of traffic to new model.
        
        Process:
        1. Create snapshot for rollback
        2. Deploy new model with 5% traffic
        3. Monitor for extended period
        4. If successful, increase to 25%, then 50%, then 100%
        5. Rollback if issues detected
        """
        deployment_id = None
        try:
            # Create deployment record
            deployment_id = await self._create_deployment_record(
                new_model_id=new_model_id,
                strategy="canary",
                status="in_progress"
            )
            
            # Create snapshot for rollback
            snapshot_id = await self.rollback_manager.create_snapshot(current_model_id)
            print(f"Created snapshot {snapshot_id} for potential rollback")
            
            # Deploy new model with initial 5% traffic
            await self._deploy_green_instance(new_model_id)
            await self._shift_traffic(new_model_id, 5)
            await self._update_deployment_traffic(deployment_id, 5)
            
            # Extended monitoring at 5%
            print("Monitoring canary deployment at 5% traffic for 15 minutes")
            await asyncio.sleep(900)  # 15 minutes
            
            issues = await self._detect_deployment_issues(new_model_id)
            if issues:
                print("Issues detected in canary - initiating rollback")
                await self.rollback_manager.rollback(current_model_id, snapshot_id)
                await self._update_deployment_status(deployment_id, "rolled_back", issues)
                return False
            
            # Progressive increases: 25%, 50%, 100%
            for shift_percent in [25, 50, 100]:
                print(f"Shifting canary traffic to {shift_percent}%")
                await self._shift_traffic(new_model_id, shift_percent)
                await self._update_deployment_traffic(deployment_id, shift_percent)
                await asyncio.sleep(self.monitoring_duration)
                
                issues = await self._detect_deployment_issues(new_model_id)
                if issues:
                    print(f"Issues detected at {shift_percent}% - initiating rollback")
                    await self.rollback_manager.rollback(current_model_id, snapshot_id)
                    await self._update_deployment_status(deployment_id, "rolled_back", issues)
                    return False
            
            # Complete deployment
            await self._decommission_blue_instance(current_model_id)
            await self._update_deployment_status(deployment_id, "completed")
            return True
        
        except Exception as e:
            print(f"Error during canary deployment: {e}")
            if deployment_id:
                await self._update_deployment_status(deployment_id, "failed", str(e))
            return False
    
    async def _all_at_once_deploy(
        self,
        new_model_id: UUID,
        current_model_id: UUID
    ) -> bool:
        """
        All-at-once deployment: immediate switch.
        
        WARNING: This is risky and not recommended for production.
        Use only for low-risk deployments or testing.
        """
        deployment_id = None
        try:
            # Create deployment record
            deployment_id = await self._create_deployment_record(
                new_model_id=new_model_id,
                strategy="all_at_once",
                status="in_progress"
            )
            
            # Create snapshot for rollback
            snapshot_id = await self.rollback_manager.create_snapshot(current_model_id)
            
            # Immediate switch
            await self._deploy_green_instance(new_model_id)
            await self._shift_traffic(new_model_id, 100)
            await self._update_deployment_traffic(deployment_id, 100)
            
            # Brief monitoring
            await asyncio.sleep(60)  # 1 minute
            
            issues = await self._detect_deployment_issues(new_model_id)
            if issues:
                await self.rollback_manager.rollback(current_model_id, snapshot_id)
                await self._update_deployment_status(deployment_id, "rolled_back", issues)
                return False
            
            await self._decommission_blue_instance(current_model_id)
            await self._update_deployment_status(deployment_id, "completed")
            return True
        
        except Exception as e:
            print(f"Error during all-at-once deployment: {e}")
            if deployment_id:
                await self._update_deployment_status(deployment_id, "failed", str(e))
            return False
    
    async def _create_deployment_record(
        self,
        new_model_id: UUID,
        strategy: str,
        status: str
    ) -> Optional[str]:
        """Create deployment record in database."""
        if not self.db_pool:
            return None
        
        try:
            async with self.db_pool.get_connection() as conn:
                deployment_id = uuid4()
                query = """
                    INSERT INTO model_deployments (
                        deployment_id, model_id, deployment_type, status, start_time
                    ) VALUES ($1, $2, $3, $4, $5)
                    RETURNING deployment_id
                """
                
                db_deployment_id = await conn.fetchval(
                    query,
                    deployment_id,
                    new_model_id,
                    strategy,
                    status,
                    datetime.now()
                )
                
                return str(db_deployment_id)
        except Exception as e:
            print(f"Error creating deployment record: {e}")
            return None
    
    async def _update_deployment_status(
        self,
        deployment_id: str,
        status: str,
        rollback_reason: Optional[str] = None
    ) -> None:
        """Update deployment status in database."""
        if not self.db_pool:
            return
        
        try:
            async with self.db_pool.get_connection() as conn:
                query = """
                    UPDATE model_deployments
                    SET status = $1, 
                        completion_time = CASE WHEN $1 IN ('completed', 'failed', 'rolled_back') THEN $2 ELSE completion_time END,
                        rollback_reason = $3
                    WHERE deployment_id = $4
                """
                
                await conn.execute(
                    query,
                    status,
                    datetime.now() if status in ['completed', 'failed', 'rolled_back'] else None,
                    rollback_reason,
                    UUID(deployment_id)
                )
        except Exception as e:
            print(f"Error updating deployment status: {e}")
    
    async def _update_deployment_traffic(
        self,
        deployment_id: str,
        traffic_percentage: int
    ) -> None:
        """Update traffic percentage in deployment record."""
        if not self.db_pool:
            return
        
        try:
            async with self.db_pool.get_connection() as conn:
                query = """
                    UPDATE model_deployments
                    SET traffic_percentage = $1
                    WHERE deployment_id = $2
                """
                
                await conn.execute(query, traffic_percentage, UUID(deployment_id))
        except Exception as e:
            print(f"Error updating deployment traffic: {e}")
    
    async def _deploy_green_instance(self, model_id: UUID) -> None:
        """
        Deploy green (new) model instance.
        
        NOTE: This is a placeholder implementation.
        Production implementation would:
        1. Load model from registry
        2. Initialize model with configuration
        3. Register with load balancer/routing
        4. Update model status to 'current'
        """
        # Update model status in registry
        if self.db_pool:
            try:
                async with self.db_pool.get_connection() as conn:
                    query = """
                        UPDATE models
                        SET status = 'current'
                        WHERE model_id = $1
                    """
                    await conn.execute(query, model_id)
                print(f"Deployed green instance for model {model_id}")
            except Exception as e:
                print(f"Error deploying green instance: {e}")
    
    async def _shift_traffic(self, new_model_id: UUID, percentage: int) -> None:
        """
        Shift traffic percentage to new model.
        
        NOTE: This is a placeholder implementation.
        Production implementation would:
        1. Update load balancer weights
        2. Update routing rules
        3. Adjust API gateway traffic split
        4. Log traffic shift
        """
        print(f"Shifting {percentage}% traffic to model {new_model_id}")
        # TODO: Implement actual traffic shifting via load balancer/routing
    
    async def _detect_deployment_issues(self, model_id: UUID) -> Optional[str]:
        """
        Detect issues with deployed model.
        
        Monitors:
        - Error rates
        - Latency increases
        - Quality degradation
        - Resource usage spikes
        
        Returns issue description if detected, None otherwise.
        """
        # Placeholder implementation
        # Production implementation would:
        # 1. Check error rates from monitoring
        # 2. Check latency percentiles
        # 3. Check quality metrics
        # 4. Check resource usage
        # 5. Return issue description if thresholds exceeded
        
        # For now, return None (no issues detected)
        return None
    
    async def _decommission_blue_instance(self, current_model_id: UUID) -> None:
        """
        Decommission blue (old) model instance.
        
        NOTE: This is a placeholder implementation.
        Production implementation would:
        1. Mark model as deprecated
        2. Gracefully shutdown model instances
        3. Remove from load balancer
        4. Clean up resources
        """
        if self.db_pool:
            try:
                async with self.db_pool.get_connection() as conn:
                    query = """
                        UPDATE models
                        SET status = 'deprecated'
                        WHERE model_id = $1
                    """
                    await conn.execute(query, current_model_id)
                print(f"Decommissioned blue instance for model {current_model_id}")
            except Exception as e:
                print(f"Error decommissioning blue instance: {e}")

