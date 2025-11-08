"""
Feature Awareness System - Makes story teller aware of all available models and features.
Provides comprehensive feature discovery and integration for narrative generation.
"""

import json
from typing import Any, Dict, List, Optional
from uuid import UUID

# HTTP client for model management
import aiohttp
import os
import logging

logger = logging.getLogger(__name__)


class FeatureAwareness:
    """
    Provides feature discovery and awareness for the story teller system.
    Makes all available models, capabilities, and features known to narrative generation.
    """
    
    def __init__(self):
        self.model_registry = ModelRegistry()
        self.env_model_registry = EnvironmentModelRegistry()
        self._feature_cache: Dict[str, Any] = {}
        self._cache_ttl = 300  # 5 minutes
    
    async def get_all_features(self) -> Dict[str, Any]:
        """
        Get comprehensive list of all available features and models.
        
        Returns:
            Dictionary with all features organized by category
        """
        features = {
            "environment_models": await self._get_environment_features(),
            "narrative_models": await self._get_narrative_features(),
            "npc_models": await self._get_npc_features(),
            "world_generation": await self._get_world_generation_features(),
            "capabilities": await self._get_system_capabilities(),
        }
        
        return features
    
    async def _get_environment_features(self) -> Dict[str, Any]:
        """Get all environment, landscape, and building model features."""
        env_models = await self.env_model_registry.get_environment_models()
        
        features = {
            "landscape": {
                "models": [],
                "capabilities": ["terrain_generation", "vegetation", "water_bodies", "natural_features"],
            },
            "building_exterior": {
                "models": [],
                "capabilities": ["facades", "structural_elements", "exterior_details"],
            },
            "building_interior": {
                "models": [],
                "capabilities": ["rooms", "furniture", "decorations", "interior_spaces"],
            },
            "lighting": {
                "models": [],
                "capabilities": ["bright_world", "dark_world", "shadows", "atmosphere"],
            },
            "textures": {
                "models": [],
                "capabilities": ["materials", "surface_properties", "weathering"],
            },
            "destruction": {
                "models": [],
                "capabilities": ["damage_states", "destruction_effects", "decay"],
            },
            "creation": {
                "models": [],
                "capabilities": ["growth", "construction", "restoration", "bloom"],
            },
        }
        
        for model in env_models:
            category = model.get("resource_requirements", {}).get("environment_category", "")
            if category:
                category_key = category.replace("environment_", "")
                if category_key in features:
                    features[category_key]["models"].append({
                        "model_id": model["model_id"],
                        "model_name": model["model_name"],
                        "version": model["version"],
                        "status": model["status"],
                        "ldt_specs": model.get("resource_requirements", {}).get("ldt_requirements", {}),
                    })
        
        return features
    
    async def _get_narrative_features(self) -> Dict[str, Any]:
        """Get narrative generation model features."""
        narrative_models = await self.model_registry.get_current_model("story_generation")
        
        return {
            "models": [narrative_models] if narrative_models else [],
            "capabilities": [
                "story_generation",
                "narrative_branching",
                "choice_generation",
                "world_state_integration",
            ],
        }
    
    async def _get_npc_features(self) -> Dict[str, Any]:
        """Get NPC-related model features."""
        # Get all NPC-related models
        postgres = await self.model_registry.get_postgres_pool()
        npc_rows = await postgres.fetch_all(
            "SELECT * FROM models WHERE use_case LIKE 'npc_%' AND status IN ('current', 'candidate')"
        )
        
        npc_models = [self.model_registry._row_to_dict(row) for row in npc_rows]
        
        return {
            "models": npc_models,
            "capabilities": [
                "dialogue_generation",
                "behavior_simulation",
                "personality_modeling",
                "relationship_tracking",
            ],
        }
    
    async def _get_world_generation_features(self) -> Dict[str, Any]:
        """Get world generation and simulation features."""
        return {
            "capabilities": [
                "world_simulation",
                "temporal_orchestration",
                "faction_dynamics",
                "economic_simulation",
                "spatial_management",
                "causal_chains",
                "event_generation",
            ],
            "light_dark_texture": {
                "lighting": {
                    "day_world": "Bright sunshine, deep shadows, tunnels, underpasses, sparkling snow, vibrant meadows",
                    "dark_world": "Deep darkness, pools of light, bright bars, dimly lit alleys, moonlight, lightning",
                },
                "textures": {
                    "examples": [
                        "Metal gleam",
                        "Ancient stone/castle walls",
                        "Polished new car",
                        "Weathered old wagon",
                        "Wooden floors",
                        "Shiny mosaic tiles",
                        "Blood glistening on blades",
                    ],
                },
                "destruction": {
                    "examples": [
                        "Half destroyed buildings",
                        "Demolished structures",
                        "Broken chairs and doors",
                        "Old moldy interiors",
                        "Holes in windows and walls",
                    ],
                },
                "creation": {
                    "examples": [
                        "Young flowers growing",
                        "Death vines expanding",
                        "Spring blossoms",
                        "Sparkling fresh water",
                        "Beauty explosions",
                    ],
                },
            },
        }
    
    async def _get_system_capabilities(self) -> Dict[str, Any]:
        """Get overall system capabilities."""
        return {
            "model_management": {
                "registry": "Centralized model registration and tracking",
                "deployment": "Automated model deployment and versioning",
                "monitoring": "Performance monitoring and guardrails",
                "rollback": "Model version rollback capability",
            },
            "environment_generation": {
                "landscape": "Terrain, vegetation, water, natural features",
                "buildings": "Exterior and interior building generation",
                "lighting": "Day and dark world lighting systems",
                "textures": "Material textures and surface properties",
                "destruction": "Damage and destruction effects",
                "creation": "Growth and construction effects",
            },
            "narrative_generation": {
                "story_creation": "AI-powered story node generation",
                "branching": "Dynamic story branching based on choices",
                "world_integration": "Integration with world state and events",
                "consistency": "Cross-world consistency enforcement",
            },
        }
    
    async def get_feature_instructions(
        self,
        feature_type: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Get instructions for how to use a specific feature.
        
        Args:
            feature_type: Type of feature (e.g., "environment_landscape", "building_exterior")
            context: Optional context for generating specific instructions
            
        Returns:
            Instructions string for the story teller
        """
        all_features = await self.get_all_features()
        
        # Build feature-specific instructions
        instructions = []
        
        if feature_type == "environment_landscape":
            env_features = all_features.get("environment_models", {}).get("landscape", {})
            instructions.append("LANDSCAPE GENERATION:")
            instructions.append("- Generate terrain, vegetation, water bodies, natural features")
            instructions.append("- Support both day and dark world variants")
            instructions.append("- Include texture specifications (metal, stone, wood, etc.)")
            instructions.append("- Support creation effects (flowers growing, water sparkling)")
            instructions.append("- Support destruction effects (erosion, decay)")
            
            if env_features.get("models"):
                instructions.append(f"\nAvailable models: {len(env_features['models'])}")
        
        elif feature_type == "building_exterior":
            env_features = all_features.get("environment_models", {}).get("building_exterior", {})
            instructions.append("BUILDING EXTERIOR GENERATION:")
            instructions.append("- Generate building facades, structural elements, exteriors")
            instructions.append("- Apply appropriate lighting (bright day world or dark world)")
            instructions.append("- Include texture details (polished, weathered, ancient)")
            instructions.append("- Support destruction states (half-destroyed, demolished)")
            
            if env_features.get("models"):
                instructions.append(f"\nAvailable models: {len(env_features['models'])}")
        
        elif feature_type == "building_interior":
            env_features = all_features.get("environment_models", {}).get("building_interior", {})
            instructions.append("BUILDING INTERIOR GENERATION:")
            instructions.append("- Generate interior spaces, rooms, furniture, decorations")
            instructions.append("- Apply interior lighting appropriate to world type")
            instructions.append("- Include texture details (wooden floors, mosaic tiles, etc.)")
            instructions.append("- Support destruction (broken furniture, moldy interiors, holes)")
            
            if env_features.get("models"):
                instructions.append(f"\nAvailable models: {len(env_features['models'])}")
        
        elif feature_type == "world_generation":
            world_features = all_features.get("world_generation", {})
            instructions.append("WORLD GENERATION CAPABILITIES:")
            instructions.append("- World simulation engine with temporal orchestration")
            instructions.append("- Faction dynamics and economic simulation")
            instructions.append("- Spatial management and territory control")
            instructions.append("- Causal chain system for event consequences")
            instructions.append("- Light-Dark-Texture system for environmental details")
            
            ldt = world_features.get("light_dark_texture", {})
            if ldt:
                instructions.append("\nLight-Dark-Texture System:")
                instructions.append(f"- Lighting: {json.dumps(ldt.get('lighting', {}), indent=2)}")
                instructions.append(f"- Textures: {json.dumps(ldt.get('textures', {}), indent=2)}")
                instructions.append(f"- Destruction: {json.dumps(ldt.get('destruction', {}), indent=2)}")
                instructions.append(f"- Creation: {json.dumps(ldt.get('creation', {}), indent=2)}")
        
        else:
            instructions.append(f"Feature type '{feature_type}' - consult system capabilities")
            instructions.append("Available features:")
            for category, features in all_features.items():
                instructions.append(f"- {category}: {len(features.get('models', []))} models")
        
        return "\n".join(instructions)
    
    async def build_story_teller_prompt_context(
        self,
        world_type: Optional[str] = None,
        location_type: Optional[str] = None,
    ) -> str:
        """
        Build comprehensive context for story teller narrative generation.
        Includes all available features and capabilities.
        
        Args:
            world_type: "day" or "dark" world
            location_type: Type of location (landscape, building_exterior, building_interior)
            
        Returns:
            Context string for narrative generation prompts
        """
        all_features = await self.get_all_features()
        
        context_parts = [
            "=== AVAILABLE SYSTEM FEATURES ===",
            "",
            "ENVIRONMENT MODELS:",
        ]
        
        # Add environment features
        env_models = all_features.get("environment_models", {})
        for category, features in env_models.items():
            models = features.get("models", [])
            if models:
                context_parts.append(f"  - {category}: {len(models)} model(s) available")
                context_parts.append(f"    Capabilities: {', '.join(features.get('capabilities', []))}")
        
        # Add world generation features
        world_gen = all_features.get("world_generation", {})
        context_parts.append("")
        context_parts.append("WORLD GENERATION:")
        context_parts.append(f"  Capabilities: {', '.join(world_gen.get('capabilities', []))}")
        
        # Add Light-Dark-Texture context
        ldt = world_gen.get("light_dark_texture", {})
        if ldt:
            context_parts.append("")
            context_parts.append("LIGHT-DARK-TEXTURE SYSTEM:")
            context_parts.append(f"  Lighting: {json.dumps(ldt.get('lighting', {}), indent=4)}")
            context_parts.append(f"  Textures: {json.dumps(ldt.get('textures', {}), indent=4)}")
            context_parts.append(f"  Destruction: {json.dumps(ldt.get('destruction', {}), indent=4)}")
            context_parts.append(f"  Creation: {json.dumps(ldt.get('creation', {}), indent=4)}")
        
        # Add world-specific context
        if world_type:
            context_parts.append("")
            context_parts.append(f"CURRENT WORLD TYPE: {world_type}")
            if world_type == "day":
                context_parts.append("  - Use bright sunshine, deep shadows, vibrant colors")
                context_parts.append("  - Sparkling elements (snow, water, meadows)")
                context_parts.append("  - Clear visibility with defined shadows")
            elif world_type == "dark":
                context_parts.append("  - Use deep darkness with pools of light")
                context_parts.append("  - Dimly lit areas, bright light sources")
                context_parts.append("  - Dramatic lighting (moonlight, lightning, flashlights)")
        
        if location_type:
            context_parts.append("")
            context_parts.append(f"CURRENT LOCATION TYPE: {location_type}")
            feature_instructions = await self.get_feature_instructions(location_type)
            context_parts.append(feature_instructions)
        
        return "\n".join(context_parts)

