"""
Model Registry - Central registry for all models.
Tracks models (paid and self-hosted), their status, versions, and metadata.
"""

import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

from services.state_manager.connection_pool import get_postgres_pool, PostgreSQLPool


class ModelRegistry:
    """
    Central registry for all models (paid and self-hosted).
    Tracks model metadata, status, versions, and configurations.
    """
    
    def __init__(self, db_pool: Optional[PostgreSQLPool] = None):
        self.postgres: Optional[PostgreSQLPool] = db_pool
        self._model_cache: Dict[str, Dict[str, Any]] = {}
        self._cache_ttl = 300  # 5 minutes
    
    async def _get_postgres(self) -> PostgreSQLPool:
        """Get PostgreSQL pool instance."""
        if self.postgres is None:
            self.postgres = await get_postgres_pool()
        return self.postgres
    
    async def get_postgres_pool(self) -> PostgreSQLPool:
        """Get PostgreSQL pool (public interface)."""
        return await self._get_postgres()
    
    async def register_model(
        self,
        model_name: str,
        model_type: str,  # "paid" or "self_hosted"
        provider: str,
        use_case: str,
        version: str,
        model_path: Optional[str] = None,
        configuration: Dict[str, Any] = None,
        performance_metrics: Dict[str, Any] = None,
        resource_requirements: Dict[str, Any] = None
    ) -> UUID:
        """
        Register a new model in the registry.
        
        Args:
            model_name: Name of the model
            model_type: "paid" or "self_hosted"
            provider: Provider name (openai, anthropic, huggingface, etc.)
            use_case: Use case identifier
            version: Model version
            model_path: Path to model files (self-hosted only)
            configuration: Model configuration (JSONB)
            performance_metrics: Performance metrics (JSONB)
            resource_requirements: Resource requirements (JSONB)
        
        Returns:
            Model ID (UUID)
        """
        postgres = await self._get_postgres()
        model_id = uuid4()
        
        await postgres.execute(
            """
            INSERT INTO models (
                model_id, model_name, model_type, provider, use_case, version,
                model_path, configuration, performance_metrics, resource_requirements,
                status, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
            """,
            model_id,
            model_name,
            model_type,
            provider,
            use_case,
            version,
            model_path,
            json.dumps(configuration or {}),
            json.dumps(performance_metrics or {}),
            json.dumps(resource_requirements or {}),
            "candidate",  # Default status
            datetime.now(timezone.utc).replace(tzinfo=None),
            datetime.now(timezone.utc).replace(tzinfo=None)
        )
        
        return model_id
    
    async def get_model(
        self,
        model_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """Get model by ID."""
        postgres = await self._get_postgres()
        
        row = await postgres.fetch(
            "SELECT * FROM models WHERE model_id = $1",
            model_id
        )
        
        if not row:
            return None
        
        return self._row_to_dict(row)
    
    async def get_current_model(
        self,
        use_case: str
    ) -> Optional[Dict[str, Any]]:
        """Get current active model for a use case."""
        postgres = await self._get_postgres()
        
        row = await postgres.fetch(
            """
            SELECT * FROM models 
            WHERE use_case = $1 AND status = 'current'
            ORDER BY updated_at DESC
            LIMIT 1
            """,
            use_case
        )
        
        if not row:
            return None
        
        return self._row_to_dict(row)
    
    async def get_candidate_models(
        self,
        use_case: str
    ) -> List[Dict[str, Any]]:
        """Get candidate models for a use case."""
        postgres = await self._get_postgres()
        
        rows = await postgres.fetch_all(
            """
            SELECT * FROM models 
            WHERE use_case = $1 AND status = 'candidate'
            ORDER BY updated_at DESC
            """,
            use_case
        )
        
        return [self._row_to_dict(row) for row in rows]
    
    async def update_model_status(
        self,
        model_id: UUID,
        status: str  # "current", "candidate", "deprecated", "testing"
    ):
        """Update model status."""
        postgres = await self._get_postgres()
        
        await postgres.execute(
            """
            UPDATE models 
            SET status = $1, updated_at = $2
            WHERE model_id = $3
            """,
            status,
            datetime.now(timezone.utc).replace(tzinfo=None),
            model_id
        )
        
        # If setting to "current", set all other models for this use case to "deprecated"
        if status == "current":
            model = await self.get_model(model_id)
            if model:
                await postgres.execute(
                    """
                    UPDATE models 
                    SET status = 'deprecated', updated_at = $1
                    WHERE use_case = $2 AND status = 'current' AND model_id != $3
                    """,
                    datetime.now(timezone.utc).replace(tzinfo=None),
                    model["use_case"],
                    model_id
                )
    
    async def update_model_performance(
        self,
        model_id: UUID,
        performance_metrics: Dict[str, Any]
    ):
        """Update model performance metrics."""
        postgres = await self._get_postgres()
        
        await postgres.execute(
            """
            UPDATE models 
            SET performance_metrics = $1, updated_at = $2
            WHERE model_id = $3
            """,
            json.dumps(performance_metrics),
            datetime.now(timezone.utc).replace(tzinfo=None),
            model_id
        )
    
    async def update_model_config(
        self,
        model_id: Any,  # Accept UUID or string
        config_updates: Dict[str, Any]
    ):
        """
        Update model configuration with new values.
        Merges new config values into existing configuration.
        """
        postgres = await self._get_postgres()
        
        # Convert model_id to UUID if string
        if isinstance(model_id, str):
            try:
                model_id = UUID(model_id)
            except ValueError:
                raise ValueError(f"Invalid model_id format: {model_id}")
        
        # Get existing configuration
        model = await self.get_model(model_id)
        if not model:
            raise ValueError(f"Model {model_id} not found")
        
        # Merge with existing configuration
        existing_config = model.get("configuration", {})
        updated_config = {**existing_config, **config_updates}
        
        # Update in database
        await postgres.execute(
            """
            UPDATE models 
            SET configuration = $1, updated_at = $2
            WHERE model_id = $3
            """,
            json.dumps(updated_config),
            datetime.now(timezone.utc).replace(tzinfo=None),
            model_id
        )
    
    def _row_to_dict(self, row) -> Dict[str, Any]:
        """Convert database row to dictionary."""
        return {
            "model_id": str(row["model_id"]),
            "model_name": row["model_name"],
            "model_type": row["model_type"],
            "provider": row["provider"],
            "use_case": row["use_case"],
            "version": row["version"],
            "status": row["status"],
            "model_path": row["model_path"],
            "configuration": json.loads(row["configuration"]) if isinstance(row["configuration"], str) else row["configuration"],
            "performance_metrics": json.loads(row["performance_metrics"]) if isinstance(row["performance_metrics"], str) else row["performance_metrics"],
            "resource_requirements": json.loads(row["resource_requirements"]) if isinstance(row["resource_requirements"], str) else row["resource_requirements"],
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
            "updated_at": row["updated_at"].isoformat() if row["updated_at"] else None
        }

