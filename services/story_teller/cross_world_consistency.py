"""
Cross-World Consistency System - Ensures same assets/buildings look identical across all player worlds.
Provides canonical asset templates and version control for consistent generation.
"""

import json
import hashlib
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

import asyncpg

# Type aliases for database connections
PostgreSQLPool = asyncpg.Pool


class AssetTemplate:
    """Represents a canonical asset template that ensures consistency."""
    
    def __init__(
        self,
        template_id: UUID,
        asset_type: str,  # "building", "landscape", "interior", etc.
        asset_name: str,
        canonical_description: str,
        ldt_specs: Dict[str, Any],
        generation_parameters: Dict[str, Any],
        template_hash: str,
    ):
        self.template_id = template_id
        self.asset_type = asset_type
        self.asset_name = asset_name
        self.canonical_description = canonical_description
        self.ldt_specs = ldt_specs
        self.generation_parameters = generation_parameters
        self.template_hash = template_hash
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "template_id": str(self.template_id),
            "asset_type": self.asset_type,
            "asset_name": self.asset_name,
            "canonical_description": self.canonical_description,
            "ldt_specs": self.ldt_specs,
            "generation_parameters": self.generation_parameters,
            "template_hash": self.template_hash,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AssetTemplate":
        """Create from dictionary."""
        return cls(
            template_id=UUID(data["template_id"]),
            asset_type=data["asset_type"],
            asset_name=data["asset_name"],
            canonical_description=data["canonical_description"],
            ldt_specs=data["ldt_specs"],
            generation_parameters=data["generation_parameters"],
            template_hash=data["template_hash"],
        )


class CrossWorldConsistency:
    """
    Manages cross-world consistency for environment assets.
    Ensures same building/asset looks identical across all player worlds initially.
    Allows story teller to modify while maintaining version control.
    """
    
    def __init__(self):
        self.postgres: Optional[PostgreSQLPool] = None
        self._template_cache: Dict[str, AssetTemplate] = {}
    
    async def _get_postgres(self) -> PostgreSQLPool:
        """Get PostgreSQL pool instance."""
        if self.postgres is None:
            self.postgres = get_state_manager_client()
        return self.postgres
    
    async def create_canonical_template(
        self,
        asset_type: str,
        asset_name: str,
        canonical_description: str,
        ldt_specs: Dict[str, Any],
        generation_parameters: Dict[str, Any],
        model_id: Optional[UUID] = None,
    ) -> AssetTemplate:
        """
        Create a canonical asset template that ensures consistency.
        
        Args:
            asset_type: Type of asset (building, landscape, interior, etc.)
            asset_name: Name of the asset
            canonical_description: Minimal description that generates consistent output
            ldt_specs: Light-Dark-Texture specifications
            generation_parameters: Parameters for model generation (seed, etc.)
            model_id: Optional model ID to use for generation
            
        Returns:
            AssetTemplate with template_id and hash
        """
        # Generate template hash for consistency verification
        template_data = {
            "asset_type": asset_type,
            "asset_name": asset_name,
            "canonical_description": canonical_description,
            "ldt_specs": json.dumps(ldt_specs, sort_keys=True),
            "generation_parameters": json.dumps(generation_parameters, sort_keys=True),
        }
        template_hash = hashlib.sha256(
            json.dumps(template_data, sort_keys=True).encode()
        ).hexdigest()
        
        template_id = uuid4()
        
        # Create template
        template = AssetTemplate(
            template_id=template_id,
            asset_type=asset_type,
            asset_name=asset_name,
            canonical_description=canonical_description,
            ldt_specs=ldt_specs,
            generation_parameters=generation_parameters,
            template_hash=template_hash,
        )
        
        # Store in database
        postgres = await self._get_postgres()
        await postgres.execute(
            """
            INSERT INTO asset_templates (
                template_id, asset_type, asset_name, canonical_description,
                ldt_specs, generation_parameters, template_hash, model_id, created_at
            ) VALUES ($1, $2, $3, $4, $5::jsonb, $6::jsonb, $7, $8, NOW())
            """,
            template_id,
            asset_type,
            asset_name,
            canonical_description,
            json.dumps(ldt_specs),
            json.dumps(generation_parameters),
            template_hash,
            model_id,
        )
        
        # Cache template
        self._template_cache[template_hash] = template
        
        return template
    
    async def get_canonical_template(
        self,
        asset_name: str,
        asset_type: Optional[str] = None,
    ) -> Optional[AssetTemplate]:
        """
        Get canonical template by name.
        
        Args:
            asset_name: Name of the asset
            asset_type: Optional type filter
            
        Returns:
            AssetTemplate or None if not found
        """
        postgres = await self._get_postgres()
        
        conditions = ["asset_name = $1"]
        params = [asset_name]
        
        if asset_type:
            conditions.append("asset_type = $2")
            params.append(asset_type)
        
        query = f"""
            SELECT * FROM asset_templates
            WHERE {' AND '.join(conditions)}
            ORDER BY created_at DESC
            LIMIT 1
        """
        
        row = await postgres.fetch(query, *params)
        if not row:
            return None
        
        return AssetTemplate(
            template_id=row["template_id"],
            asset_type=row["asset_type"],
            asset_name=row["asset_name"],
            canonical_description=row["canonical_description"],
            ldt_specs=json.loads(row["ldt_specs"]) if isinstance(row["ldt_specs"], str) else row["ldt_specs"],
            generation_parameters=json.loads(row["generation_parameters"]) if isinstance(row["generation_parameters"], str) else row["generation_parameters"],
            template_hash=row["template_hash"],
        )
    
    async def generate_asset_from_template(
        self,
        template: AssetTemplate,
        world_id: UUID,
        world_type: str,  # "day" or "dark"
        modifications: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Generate an asset from a canonical template for a specific world.
        Ensures consistency while allowing world-specific modifications.
        
        Args:
            template: AssetTemplate to use
            world_id: World ID where asset will be generated
            world_type: "day" or "dark" world type
            modifications: Optional modifications (destruction, creation, etc.)
            
        Returns:
            Generated asset specification
        """
        # Start with canonical generation parameters
        generation_params = template.generation_parameters.copy()
        
        # Apply world type modifications
        ldt_specs = template.ldt_specs.copy()
        if "lighting" in ldt_specs:
            lighting = ldt_specs["lighting"]
            if world_type == "day":
                lighting["brightness"] = lighting.get("day_brightness", "high")
                lighting["atmosphere"] = lighting.get("day_atmosphere", "bright_sunshine")
            elif world_type == "dark":
                lighting["brightness"] = lighting.get("dark_brightness", "low")
                lighting["atmosphere"] = lighting.get("dark_atmosphere", "deep_darkness")
        
        # Apply story teller modifications
        if modifications:
            if "destruction" in modifications:
                # Apply destruction effects
                if "destruction" not in ldt_specs:
                    ldt_specs["destruction"] = {}
                ldt_specs["destruction"].update(modifications["destruction"])
            
            if "creation" in modifications:
                # Apply creation effects
                if "creation" not in ldt_specs:
                    ldt_specs["creation"] = {}
                ldt_specs["creation"].update(modifications["creation"])
            
            if "texture_changes" in modifications:
                # Apply texture modifications
                if "textures" not in ldt_specs:
                    ldt_specs["textures"] = {}
                ldt_specs["textures"].update(modifications["texture_changes"])
        
        # Build generation prompt (minimal instructions for expert models)
        prompt = self._build_minimal_prompt(
            template=template,
            world_type=world_type,
            ldt_specs=ldt_specs,
        )
        
        # Store generation request for tracking
        generation_id = uuid4()
        postgres = await self._get_postgres()
        await postgres.execute(
            """
            INSERT INTO asset_generations (
                generation_id, template_id, world_id, world_type,
                generation_prompt, ldt_specs, modifications, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7::jsonb, NOW())
            """,
            generation_id,
            template.template_id,
            world_id,
            world_type,
            prompt,
            json.dumps(ldt_specs),
            json.dumps(modifications or {}),
        )
        
        return {
            "generation_id": str(generation_id),
            "template_id": str(template.template_id),
            "template_hash": template.template_hash,
            "asset_name": template.asset_name,
            "asset_type": template.asset_type,
            "generation_prompt": prompt,
            "ldt_specs": ldt_specs,
            "world_type": world_type,
            "modifications": modifications or {},
            "consistency_guaranteed": True,  # Generated from canonical template
        }
    
    def _build_minimal_prompt(
        self,
        template: AssetTemplate,
        world_type: str,
        ldt_specs: Dict[str, Any],
    ) -> str:
        """
        Build minimal prompt for expert models to generate consistent output.
        Uses canonical description + world type + LDT specs.
        """
        prompt_parts = [
            f"Generate {template.asset_type}: {template.asset_name}",
            f"Description: {template.canonical_description}",
            f"World Type: {world_type}",
        ]
        
        # Add lighting specifications
        if "lighting" in ldt_specs:
            lighting = ldt_specs["lighting"]
            prompt_parts.append(f"Lighting: {lighting.get('brightness', 'standard')} brightness, {lighting.get('atmosphere', 'neutral')} atmosphere")
        
        # Add texture specifications
        if "textures" in ldt_specs:
            textures = ldt_specs["textures"]
            material_type = textures.get("material_type", "standard")
            prompt_parts.append(f"Textures: {material_type} material")
        
        # Add destruction/creation if specified
        if "destruction" in ldt_specs:
            destruction = ldt_specs["destruction"]
            damage_state = destruction.get("damage_states", "intact")
            prompt_parts.append(f"Destruction State: {damage_state}")
        
        if "creation" in ldt_specs:
            creation = ldt_specs["creation"]
            growth_state = creation.get("growth_states", "mature")
            prompt_parts.append(f"Creation State: {growth_state}")
        
        prompt_parts.append("\nGenerate consistent output matching these specifications.")
        
        return "\n".join(prompt_parts)
    
    async def verify_consistency(
        self,
        asset_name: str,
        world_ids: List[UUID],
    ) -> Dict[str, Any]:
        """
        Verify that an asset is consistent across multiple worlds.
        
        Args:
            asset_name: Name of the asset to verify
            world_ids: List of world IDs to check
            
        Returns:
            Verification results
        """
        template = await self.get_canonical_template(asset_name)
        if not template:
            return {
                "consistent": False,
                "error": f"Template not found for asset: {asset_name}",
            }
        
        postgres = await self._get_postgres()
        
        # Check all generations for this template
        generations = await postgres.fetch_all(
            """
            SELECT generation_id, world_id, world_type, template_hash, modifications
            FROM asset_generations
            WHERE template_id = $1 AND world_id = ANY($2::uuid[])
            """,
            template.template_id,
            world_ids,
        )
        
        # Verify all use same template hash
        template_hashes = set()
        for gen in generations:
            template_hashes.add(gen["template_hash"])
        
        consistent = len(template_hashes) == 1 and template_hashes.pop() == template.template_hash
        
        return {
            "consistent": consistent,
            "template_hash": template.template_hash,
            "generation_count": len(generations),
            "worlds_checked": len(world_ids),
            "modifications": [
                {
                    "world_id": str(gen["world_id"]),
                    "has_modifications": bool(gen["modifications"]),
                }
                for gen in generations
            ],
        }
    
    async def list_assets_by_type(
        self,
        asset_type: str,
    ) -> List[AssetTemplate]:
        """List all canonical assets of a specific type."""
        postgres = await self._get_postgres()
        
        rows = await postgres.fetch_all(
            """
            SELECT * FROM asset_templates
            WHERE asset_type = $1
            ORDER BY asset_name
            """,
            asset_type,
        )
        
        templates = []
        for row in rows:
            templates.append(AssetTemplate(
                template_id=row["template_id"],
                asset_type=row["asset_type"],
                asset_name=row["asset_name"],
                canonical_description=row["canonical_description"],
                ldt_specs=json.loads(row["ldt_specs"]) if isinstance(row["ldt_specs"], str) else row["ldt_specs"],
                generation_parameters=json.loads(row["generation_parameters"]) if isinstance(row["generation_parameters"], str) else row["generation_parameters"],
                template_hash=row["template_hash"],
            ))
        
        return templates

