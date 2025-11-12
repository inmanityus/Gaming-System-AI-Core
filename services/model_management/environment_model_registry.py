"""
Environment Model Registry - Specialized registry for environment/landscape/building models.
Handles registration, validation, and resource management for environmental AI models.
"""

import json
from typing import Any, Dict, List, Optional
from uuid import UUID



class EnvironmentModelRegistry(ModelRegistry):
    """
    Extended Model Registry for environment, landscape, and building models.
    Validates Light-Dark-Texture requirements and manages environment-specific resources.
    """
    
    # Environment model use case categories
    ENVIRONMENT_USE_CASES = {
        "environment_landscape": "Terrain, vegetation, water bodies, natural features",
        "environment_building_exterior": "Building exteriors, facades, structural elements",
        "environment_building_interior": "Interior spaces, rooms, furniture, decorations",
        "environment_lighting": "Lighting systems, shadows, atmosphere",
        "environment_texture": "Material textures, surface properties, weathering",
        "environment_destruction": "Damage states, destruction effects, decay",
        "environment_creation": "Growth, construction, restoration effects",
    }
    
    # Light-Dark-Texture requirement keys
    LDT_REQUIREMENTS = {
        "lighting": {
            "required": ["brightness_range", "shadow_casting", "atmosphere_type"],
            "optional": ["dynamic_lighting", "color_temperature", "light_sources"],
            "world_types": ["day", "dark"],  # Day world vs Dark world
        },
        "textures": {
            "required": ["material_type", "texture_maps", "surface_properties"],
            "optional": ["weathering_states", "age_variants", "detail_maps"],
            "examples": ["metal_gleam", "ancient_stone", "polished_car", "weathered_wagon", 
                       "wooden_floors", "mosaic_tiles", "blood_glistening"],
        },
        "destruction": {
            "required": ["damage_states", "physics_properties", "destruction_effects"],
            "optional": ["progressive_damage", "debris_generation", "structural_failure"],
            "examples": ["half_destroyed_building", "demolished_structure", "broken_chairs",
                        "old_moldy_interiors", "holes_in_walls"],
        },
        "creation": {
            "required": ["growth_states", "construction_phases", "creation_effects"],
            "optional": ["progressive_growth", "bloom_effects", "restoration_phases"],
            "examples": ["young_flower", "death_vine", "spring_blossoms", "sparkling_water"],
        },
    }
    
    async def register_environment_model(
        self,
        model_name: str,
        model_type: str,  # "paid" or "self_hosted"
        provider: str,
        environment_category: str,  # One of ENVIRONMENT_USE_CASES keys
        version: str,
        model_path: Optional[str] = None,
        lighting_specs: Optional[Dict[str, Any]] = None,
        texture_specs: Optional[Dict[str, Any]] = None,
        destruction_specs: Optional[Dict[str, Any]] = None,
        creation_specs: Optional[Dict[str, Any]] = None,
        configuration: Dict[str, Any] = None,
        performance_metrics: Dict[str, Any] = None,
        resource_requirements: Dict[str, Any] = None,
    ) -> UUID:
        """
        Register an environment model with Light-Dark-Texture requirement validation.
        
        Args:
            model_name: Name of the model
            model_type: "paid" or "self_hosted"
            provider: Provider name
            environment_category: Category from ENVIRONMENT_USE_CASES
            version: Model version
            model_path: Path to model files
            lighting_specs: Lighting requirements (brightness_range, shadow_casting, etc.)
            texture_specs: Texture requirements (material_type, texture_maps, etc.)
            destruction_specs: Destruction requirements (damage_states, physics_properties, etc.)
            creation_specs: Creation requirements (growth_states, construction_phases, etc.)
            configuration: Additional model configuration
            performance_metrics: Performance metrics
            resource_requirements: Resource requirements
            
        Returns:
            Model ID (UUID)
        """
        # Validate environment category
        if environment_category not in self.ENVIRONMENT_USE_CASES:
            raise ValueError(
                f"Invalid environment category: {environment_category}. "
                f"Must be one of: {list(self.ENVIRONMENT_USE_CASES.keys())}"
            )
        
        # Build resource requirements with LDT specs
        ldt_requirements = self._build_ldt_requirements(
            lighting_specs=lighting_specs,
            texture_specs=texture_specs,
            destruction_specs=destruction_specs,
            creation_specs=creation_specs,
        )
        
        # Merge with existing resource requirements
        merged_resource_requirements = {
            **(resource_requirements or {}),
            "ldt_requirements": ldt_requirements,
            "environment_category": environment_category,
            "environment_description": self.ENVIRONMENT_USE_CASES[environment_category],
        }
        
        # Validate LDT requirements
        validation_result = self._validate_ldt_requirements(ldt_requirements, environment_category)
        if not validation_result["valid"]:
            raise ValueError(
                f"LDT validation failed: {validation_result['errors']}"
            )
        
        # Register model with environment use case
        use_case = f"environment_{environment_category}"
        model_id = await self.register_model(
            model_name=model_name,
            model_type=model_type,
            provider=provider,
            use_case=use_case,
            version=version,
            model_path=model_path,
            configuration=configuration or {},
            performance_metrics=performance_metrics or {},
            resource_requirements=merged_resource_requirements,
        )
        
        return model_id
    
    def _build_ldt_requirements(
        self,
        lighting_specs: Optional[Dict[str, Any]] = None,
        texture_specs: Optional[Dict[str, Any]] = None,
        destruction_specs: Optional[Dict[str, Any]] = None,
        creation_specs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Build Light-Dark-Texture requirements dictionary."""
        ldt_requirements = {}
        
        if lighting_specs:
            ldt_requirements["lighting"] = {
                **lighting_specs,
                "world_types": lighting_specs.get("world_types", ["day", "dark"]),
            }
        
        if texture_specs:
            ldt_requirements["textures"] = texture_specs
        
        if destruction_specs:
            ldt_requirements["destruction"] = destruction_specs
        
        if creation_specs:
            ldt_requirements["creation"] = creation_specs
        
        return ldt_requirements
    
    def _validate_ldt_requirements(
        self,
        ldt_requirements: Dict[str, Any],
        environment_category: str,
    ) -> Dict[str, Any]:
        """
        Validate Light-Dark-Texture requirements against specifications.
        
        Returns:
            {"valid": bool, "errors": List[str]}
        """
        errors = []
        
        # Check each LDT category
        for category, specs in self.LDT_REQUIREMENTS.items():
            if category in ldt_requirements:
                category_requirements = ldt_requirements[category]
                required_fields = specs["required"]
                
                # Check required fields
                for field in required_fields:
                    if field not in category_requirements:
                        errors.append(
                            f"Missing required {category} field: {field}"
                        )
        
        # Environment-specific validation
        if "building" in environment_category:
            # Building models must have both interior/exterior specs if applicable
            if "lighting" not in ldt_requirements:
                errors.append("Building models require lighting specifications")
            if "textures" not in ldt_requirements:
                errors.append("Building models require texture specifications")
        
        if "landscape" in environment_category:
            # Landscape models should support creation/destruction
            if "creation" not in ldt_requirements and "destruction" not in ldt_requirements:
                errors.append(
                    "Landscape models should support creation or destruction effects"
                )
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
        }
    
    async def get_environment_models(
        self,
        environment_category: Optional[str] = None,
        world_type: Optional[str] = None,  # "day" or "dark"
    ) -> List[Dict[str, Any]]:
        """
        Get all environment models, optionally filtered by category or world type.
        
        Args:
            environment_category: Filter by environment category
            world_type: Filter by world type (day/dark) if model supports lighting
            
        Returns:
            List of model dictionaries
        """
        postgres = await self._get_postgres()
        
        # Build query
        conditions = ["use_case LIKE 'environment_%'"]
        params = []
        
        if environment_category:
            conditions.append("use_case = $1")
            params.append(f"environment_{environment_category}")
        
        query = f"""
            SELECT * FROM models 
            WHERE {' AND '.join(conditions)}
            AND status IN ('current', 'candidate')
            ORDER BY updated_at DESC
        """
        
        rows = await postgres.fetch_all(query, *params)
        models = [self._row_to_dict(row) for row in rows]
        
        # Filter by world_type if specified
        if world_type:
            filtered_models = []
            for model in models:
                resource_reqs = model.get("resource_requirements", {})
                ldt_reqs = resource_reqs.get("ldt_requirements", {})
                lighting = ldt_reqs.get("lighting", {})
                world_types = lighting.get("world_types", [])
                
                if world_type in world_types or len(world_types) == 0:
                    filtered_models.append(model)
            
            models = filtered_models
        
        return models
    
    async def get_model_ldt_specs(self, model_id: UUID) -> Dict[str, Any]:
        """
        Get Light-Dark-Texture specifications for a model.
        
        Returns:
            Dictionary with lighting, textures, destruction, creation specs
        """
        model = await self.get_model(model_id)
        if not model:
            return {}
        
        resource_requirements = model.get("resource_requirements", {})
        return resource_requirements.get("ldt_requirements", {})

