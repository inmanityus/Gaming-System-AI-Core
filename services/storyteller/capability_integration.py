# services/storyteller/capability_integration.py
"""
Storyteller Capability Integration
Enables Storyteller to dynamically adapt to UE5 version capabilities
"""

from typing import Dict, List, Optional
import httpx
import json
import os

class StorytellerCapabilityManager:
    def __init__(self, registry_api_url: Optional[str] = None):
        self.registry_api = registry_api_url or os.getenv(
            "CAPABILITY_REGISTRY_URL",
            "http://localhost:8080"
        )
        self.cached_capabilities = {}
        self.current_version = os.getenv("UE5_VERSION", "5.6.1")
        
    async def get_capabilities_for_version(
        self, 
        version: Optional[str] = None
    ) -> Dict:
        """Get all capabilities for a UE5 version"""
        version = version or self.current_version
        
        if version not in self.cached_capabilities:
            async with httpx.AsyncClient(timeout=10.0) as client:
                try:
                    response = await client.get(
                        f"{self.registry_api}/api/v1/capabilities",
                        params={"version": version}
                    )
                    response.raise_for_status()
                    self.cached_capabilities[version] = response.json()
                except Exception as e:
                    print(f"Error fetching capabilities: {e}")
                    # Return empty capabilities on error
                    self.cached_capabilities[version] = {
                        'version': version,
                        'capabilities': {}
                    }
        
        return self.cached_capabilities[version]
    
    def build_capability_prompt(
        self, 
        base_prompt: str, 
        version: Optional[str] = None
    ) -> str:
        """Build enhanced prompt with UE5 capabilities"""
        import asyncio
        
        # Run async function in sync context
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        capabilities = loop.run_until_complete(
            self.get_capabilities_for_version(version)
        )
        
        capability_text = self.format_capabilities(capabilities)
        
        enhanced_prompt = f"""
{base_prompt}

AVAILABLE UNREAL ENGINE 5 CAPABILITIES (Version {version or self.current_version}):

{capability_text}

INSTRUCTIONS:
- Use these capabilities to enhance the player's world
- Create more immersive and dynamic experiences
- Leverage advanced features for unique story elements
- Adapt narrative to take advantage of available features
- Do not reference features that are not available in this version
"""
        return enhanced_prompt
    
    def format_capabilities(self, capabilities: Dict) -> str:
        """Format capabilities for prompt inclusion"""
        formatted = []
        caps = capabilities.get('capabilities', {})
        
        for category, features in caps.items():
            formatted.append(f"\n{category.upper().replace('_', ' ')}:")
            for feature in features:
                name = feature.get('name', 'Unknown')
                desc = feature.get('description', '')
                formatted.append(f"  - {name}: {desc}")
                if feature.get('example_usage'):
                    formatted.append(f"    Example: {feature['example_usage']}")
        
        if not formatted:
            return "No capabilities available for this version."
        
        return "\n".join(formatted)
    
    async def suggest_story_elements(
        self, 
        current_story_context: str,
        version: Optional[str] = None
    ) -> List[str]:
        """Suggest story elements based on available capabilities"""
        capabilities = await self.get_capabilities_for_version(version)
        suggestions = []
        
        # Analyze story context and suggest relevant features
        context_lower = current_story_context.lower()
        
        if "underground" in context_lower or "cavern" in context_lower:
            rendering = capabilities.get('capabilities', {}).get('rendering', [])
            if any('lumen' in str(f).lower() for f in rendering):
                suggestions.append(
                    "Use Lumen global illumination to create realistic "
                    "underground lighting with dynamic light bounces"
                )
        
        if "crowd" in context_lower or "city" in context_lower:
            ai_features = capabilities.get('capabilities', {}).get('ai', [])
            if any('mass' in str(f).lower() for f in ai_features):
                suggestions.append(
                    "Use Mass AI to create realistic crowd behaviors "
                    "with thousands of NPCs"
                )
        
        if "weather" in context_lower:
            rendering = capabilities.get('capabilities', {}).get('rendering', [])
            if any('niagara' in str(f).lower() for f in rendering):
                suggestions.append(
                    "Use Niagara particle systems for dynamic weather effects"
                )
        
        return suggestions

class CapabilityAwareStoryteller:
    def __init__(self, capability_manager: StorytellerCapabilityManager):
        self.capability_manager = capability_manager
        
    async def generate_story_segment(
        self, 
        context: str,
        player_state: Dict
    ) -> str:
        """Generate story segment with capability awareness"""
        
        # Get available capabilities
        capabilities = await self.capability_manager.get_capabilities_for_version()
        
        # Build enhanced prompt
        base_prompt = self.build_base_prompt(context, player_state)
        enhanced_prompt = self.capability_manager.build_capability_prompt(
            base_prompt
        )
        
        # Get suggestions
        suggestions = await self.capability_manager.suggest_story_elements(
            context
        )
        
        # Include suggestions in prompt
        if suggestions:
            enhanced_prompt += "\n\nSUGGESTED FEATURES TO USE:\n"
            for suggestion in suggestions:
                enhanced_prompt += f"- {suggestion}\n"
        
        # Generate story with LLM (placeholder - integrate with actual LLM)
        story = await self.llm_generate(enhanced_prompt)
        
        return story
    
    def build_base_prompt(self, context: str, player_state: Dict) -> str:
        """Build base story prompt"""
        return f"""
Generate a story segment based on the following context:

Context: {context}
Player State: {json.dumps(player_state, indent=2)}
"""
    
    async def llm_generate(self, prompt: str) -> str:
        """Generate story using LLM (placeholder)"""
        # This would integrate with the actual LLM service
        return f"[Generated story based on: {prompt[:100]}...]"





