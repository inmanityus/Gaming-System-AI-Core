"""
Rollback Manager - Manages model rollback when issues detected.
"""

import json
import os
import shutil
import time
from typing import Any, Dict, Optional
from uuid import UUID, uuid4
from datetime import datetime
from pathlib import Path

from state_manager.connection_pool import PostgreSQLPool


class RollbackManager:
    """
    Manages model rollback when issues are detected during deployment.
    
    Provides:
    - Snapshot creation for rollback points
    - Model state restoration
    - Traffic allocation restoration
    - Rollback verification
    """
    
    def __init__(self, db_pool: Optional[PostgreSQLPool] = None):
        self.db_pool = db_pool
        self.snapshots_dir = Path("models/snapshots")
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
    
    async def create_snapshot(self, model_id: UUID) -> str:
        """
        Create snapshot of model state for rollback.
        
        Snapshot includes:
        - Model weights/files
        - Configuration
        - Performance metrics
        - Current traffic allocation
        
        Args:
            model_id: UUID of model to snapshot
        
        Returns:
            Snapshot ID for later rollback
        """
        try:
            # Generate snapshot ID
            snapshot_id = str(uuid4())
            snapshot_name = f"snapshot-{model_id}-{int(time.time())}"
            
            # Get model information
            model_info = await self._get_model_info(model_id)
            if not model_info:
                raise ValueError(f"Model {model_id} not found")
            
            # Capture model state
            model_state_path = await self._capture_model_state(model_id, snapshot_id)
            
            # Get current metrics and traffic allocation
            current_metrics = await self._get_current_metrics(model_id)
            traffic_allocation = await self._get_traffic_allocation(model_id)
            
            # Store snapshot in database
            snapshot_db_id = await self._persist_snapshot(
                snapshot_id=snapshot_id,
                snapshot_name=snapshot_name,
                model_id=model_id,
                model_state_path=str(model_state_path),
                configuration=model_info.get('configuration', {}),
                performance_metrics=current_metrics,
                traffic_allocation=traffic_allocation
            )
            
            return snapshot_id
            
        except Exception as e:
            print(f"Error creating snapshot for model {model_id}: {e}")
            raise
    
    async def rollback(self, model_id: UUID, snapshot_id: str = None) -> bool:
        """
        Rollback to previous model state.
        
        Can rollback to:
        - Specific snapshot (snapshot_id provided)
        - Most recent stable snapshot (if snapshot_id is None)
        
        Args:
            model_id: UUID of model to rollback
            snapshot_id: Optional specific snapshot ID to rollback to
        
        Returns:
            True if rollback successful, False otherwise
        """
        try:
            # Determine which snapshot to use
            if snapshot_id:
                snapshot = await self._get_snapshot(snapshot_id)
            else:
                snapshot = await self._get_most_recent_stable_snapshot(model_id)
            
            if not snapshot:
                print(f"No suitable snapshot found for rollback of model {model_id}")
                return False
            
            # Restore model state
            await self._restore_model_state(model_id, snapshot)
            
            # Restore traffic allocation
            await self._restore_traffic_allocation(model_id, snapshot)
            
            # Restore configuration
            await self._restore_model_configuration(model_id, snapshot)
            
            # Verify rollback success
            verification = await self._verify_rollback(model_id, snapshot)
            
            if verification:
                print(f"Rollback successful for model {model_id} to snapshot {snapshot['snapshot_id']}")
                return True
            else:
                print(f"Rollback verification failed for model {model_id}")
                return False
                
        except Exception as e:
            print(f"Error during rollback for model {model_id}: {e}")
            return False
    
    async def _get_model_info(self, model_id: UUID) -> Optional[Dict[str, Any]]:
        """Get model information from database."""
        if not self.db_pool:
            return None
        
        try:
            async with self.db_pool.get_connection() as conn:
                query = """
                    SELECT model_id, model_name, model_type, use_case, 
                           configuration, performance_metrics
                    FROM models
                    WHERE model_id = $1
                """
                row = await conn.fetchrow(query, model_id)
                if row:
                    return dict(row)
            return None
        except Exception as e:
            print(f"Error getting model info: {e}")
            return None
    
    async def _capture_model_state(self, model_id: UUID, snapshot_id: str) -> Path:
        """
        Capture model state (weights, files, etc.) to disk.
        
        Args:
            model_id: UUID of model
            snapshot_id: UUID of snapshot
        
        Returns:
            Path to saved model state
        """
        # Create snapshot directory
        snapshot_path = self.snapshots_dir / snapshot_id
        snapshot_path.mkdir(parents=True, exist_ok=True)
        
        # Get model path from database
        model_info = await self._get_model_info(model_id)
        if not model_info or not model_info.get('model_path'):
            # No model path, save metadata only
            with open(snapshot_path / "metadata.json", "w") as f:
                json.dump({"model_id": str(model_id), "snapshot_id": snapshot_id}, f)
            return snapshot_path / "metadata.json"
        
        # REAL IMPLEMENTATION - Create snapshot of model state
        # If model has files, copy them; otherwise save reference
        if model_info.get('model_path') and os.path.exists(model_info['model_path']):
            # Copy model files to snapshot directory
            model_source = Path(model_info['model_path'])
            
            if model_source.is_dir():
                # Copy entire directory
                dest_dir = snapshot_path / "model_files"
                dest_dir.mkdir(parents=True, exist_ok=True)
                shutil.copytree(model_source, dest_dir, dirs_exist_ok=True)
                model_files_path = dest_dir
            else:
                # Copy single file
                dest_file = snapshot_path / model_source.name
                shutil.copy2(model_source, dest_file)
                model_files_path = dest_file
            
            # Save metadata with actual file path
            metadata = {
                "model_id": str(model_id),
                "snapshot_id": snapshot_id,
                "model_files_path": str(model_files_path),
                "original_model_path": model_info['model_path'],
                "snapshot_type": "full" if model_source.is_dir() else "file",
            }
        else:
            # For paid models or models without local files, save configuration reference
            metadata = {
                "model_id": str(model_id),
                "snapshot_id": snapshot_id,
                "original_model_path": model_info.get('model_path'),
                "snapshot_type": "reference",
                "configuration": model_info.get('configuration', {}),
            }
        
        with open(snapshot_path / "model_reference.json", "w") as f:
            json.dump(metadata, f, indent=2)
        
        return snapshot_path / "model_reference.json"
    
    async def _get_current_metrics(self, model_id: UUID) -> Dict[str, Any]:
        """Get current performance metrics for model."""
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
            return {}
        except Exception as e:
            print(f"Error getting current metrics: {e}")
            return {}
    
    async def _get_traffic_allocation(self, model_id: UUID) -> Dict[str, Any]:
        """Get current traffic allocation for model."""
        if not self.db_pool:
            return {}
        
        try:
            async with self.db_pool.get_connection() as conn:
                query = """
                    SELECT traffic_percentage
                    FROM model_deployments
                    WHERE model_id = $1
                      AND status IN ('in_progress', 'completed')
                    ORDER BY start_time DESC
                    LIMIT 1
                """
                row = await conn.fetchrow(query, model_id)
                if row:
                    return {"traffic_percentage": row['traffic_percentage']}
            return {}
        except Exception as e:
            print(f"Error getting traffic allocation: {e}")
            return {}
    
    async def _persist_snapshot(
        self,
        snapshot_id: str,
        snapshot_name: str,
        model_id: UUID,
        model_state_path: str,
        configuration: Dict[str, Any],
        performance_metrics: Dict[str, Any],
        traffic_allocation: Dict[str, Any]
    ) -> Optional[str]:
        """Store snapshot metadata in database."""
        if not self.db_pool:
            return None
        
        try:
            async with self.db_pool.get_connection() as conn:
                query = """
                    INSERT INTO model_snapshots (
                        snapshot_id,
                        snapshot_name,
                        model_id,
                        model_state_path,
                        configuration,
                        performance_metrics,
                        traffic_allocation
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7)
                    RETURNING snapshot_id
                """
                
                db_snapshot_id = await conn.fetchval(
                    query,
                    UUID(snapshot_id),
                    snapshot_name,
                    model_id,
                    model_state_path,
                    json.dumps(configuration),
                    json.dumps(performance_metrics),
                    json.dumps(traffic_allocation)
                )
                
                return str(db_snapshot_id)
        except Exception as e:
            print(f"Error persisting snapshot: {e}")
            return None
    
    async def _get_snapshot(self, snapshot_id: str) -> Optional[Dict[str, Any]]:
        """Get snapshot by ID."""
        if not self.db_pool:
            return None
        
        try:
            async with self.db_pool.get_connection() as conn:
                query = """
                    SELECT snapshot_id, model_id, model_state_path,
                           configuration, performance_metrics, traffic_allocation
                    FROM model_snapshots
                    WHERE snapshot_id = $1
                """
                row = await conn.fetchrow(query, UUID(snapshot_id))
                if row:
                    return dict(row)
            return None
        except Exception as e:
            print(f"Error getting snapshot: {e}")
            return None
    
    async def _get_most_recent_stable_snapshot(self, model_id: UUID) -> Optional[Dict[str, Any]]:
        """Get most recent stable snapshot for model."""
        if not self.db_pool:
            return None
        
        try:
            async with self.db_pool.get_connection() as conn:
                query = """
                    SELECT snapshot_id, model_id, model_state_path,
                           configuration, performance_metrics, traffic_allocation
                    FROM model_snapshots
                    WHERE model_id = $1
                    ORDER BY created_at DESC
                    LIMIT 1
                """
                row = await conn.fetchrow(query, model_id)
                if row:
                    return dict(row)
            return None
        except Exception as e:
            print(f"Error getting most recent snapshot: {e}")
            return None
    
    async def _restore_model_state(self, model_id: UUID, snapshot: Dict[str, Any]) -> bool:
        """
        Restore model state from snapshot.
        
        In production, this would:
        1. Load model files from snapshot
        2. Restore model weights
        3. Update model registry
        """
        # REAL IMPLEMENTATION - Restore model state from snapshot
        try:
            snapshot_path = Path(f"models/rollbacks/{snapshot['snapshot_id']}")
            reference_file = snapshot_path / "model_reference.json"
            
            if not reference_file.exists():
                print(f"[ERROR] Snapshot reference not found: {reference_file}")
                return False
            
            with open(reference_file, "r") as f:
                metadata = json.load(f)
            
            snapshot_type = metadata.get("snapshot_type", "reference")
            
            if snapshot_type == "full" or snapshot_type == "file":
                # Restore model files
                model_files_path = Path(metadata.get("model_files_path"))
                original_path = Path(metadata.get("original_model_path", ""))
                
                if model_files_path.exists() and original_path:
                    # Ensure destination directory exists
                    original_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    if model_files_path.is_dir():
                        # Restore directory
                        if original_path.exists():
                            shutil.rmtree(original_path)  # Remove old if exists
                        shutil.copytree(model_files_path, original_path, dirs_exist_ok=True)
                    else:
                        # Restore file
                        original_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(model_files_path, original_path)
                    
                    print(f"[RESTORE] Model files restored to {original_path}")
                else:
                    print(f"[ERROR] Model files not found in snapshot: {model_files_path}")
                    return False
            
            # Restore model configuration in registry
            from model_registry import ModelRegistry
            registry = ModelRegistry()
            
            if metadata.get("configuration"):
                await registry.update_model_config(
                    model_id,
                    metadata["configuration"]
                )
            
            print(f"[RESTORE] Model state restored for {model_id} from snapshot {snapshot['snapshot_id']}")
            return True
            
        except Exception as e:
            print(f"[ERROR] Failed to restore model state: {e}")
            return False
    
    async def _restore_traffic_allocation(self, model_id: UUID, snapshot: Dict[str, Any]) -> bool:
        """Restore traffic allocation from snapshot."""
        if not self.db_pool or not snapshot.get('traffic_allocation'):
            return True
        
        try:
            # Update model status in registry
            async with self.db_pool.get_connection() as conn:
                query = """
                    UPDATE models
                    SET status = 'current'
                    WHERE model_id = $1
                """
                await conn.execute(query, model_id)
            
            # Update deployment status
            async with self.db_pool.get_connection() as conn:
                query = """
                    INSERT INTO model_deployments (
                        model_id, deployment_type, status, 
                        traffic_percentage, start_time
                    ) VALUES ($1, $2, $3, $4, $5)
                """
                await conn.execute(
                    query,
                    model_id,
                    'rollback',
                    'completed',
                    snapshot['traffic_allocation'].get('traffic_percentage', 100),
                    datetime.now()
                )
            
            return True
        except Exception as e:
            print(f"Error restoring traffic allocation: {e}")
            return False
    
    async def _restore_model_configuration(self, model_id: UUID, snapshot: Dict[str, Any]) -> bool:
        """Restore model configuration from snapshot."""
        if not self.db_pool or not snapshot.get('configuration'):
            return True
        
        try:
            async with self.db_pool.get_connection() as conn:
                query = """
                    UPDATE models
                    SET configuration = $1
                    WHERE model_id = $2
                """
                await conn.execute(query, json.dumps(snapshot['configuration']), model_id)
            return True
        except Exception as e:
            print(f"Error restoring configuration: {e}")
            return False
    
    async def _verify_rollback(self, model_id: UUID, snapshot: Dict[str, Any]) -> bool:
        """Verify rollback was successful."""
        try:
            # Verify model is marked as current
            model_info = await self._get_model_info(model_id)
            if model_info and model_info.get('status') == 'current':
                return True
            return False
        except Exception as e:
            print(f"Error verifying rollback: {e}")
            return False

