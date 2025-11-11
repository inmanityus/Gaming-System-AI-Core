"""
Narrative Design AI - Stage 1 of Archetype Automation
Coder: Claude Sonnet 4.5
Reviewer: GPT-Codex-2 (Pending)

Generates complete archetype profiles from simple concepts using Story Teller AI (Gemini 2.5 Pro).

Input: Archetype concept (2-3 sentences)
Output: Complete character profile with behavioral traits, Dark World integration, narrative hooks

Integrates with existing Story Teller collaboration:
- 4 previous sessions
- Comprehensive narrative design
- Deep understanding of The Body Broker universe
"""

import os
import json
import logging
import re
import time
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def sanitize_filename(name: str) -> str:
    """
    Sanitize filename to prevent path traversal and invalid characters.
    
    Handles:
    - Path separators (/, \, mixed)
    - Special characters
    - Windows reserved device names
    - Unicode normalization
    - Length limits
    """
    # Remove any path separators (/, \, mixed)
    name = name.replace('\\', '').replace('/', '')
    
    # Remove special characters (keep alphanumeric, spaces, hyphens, underscores)
    name = re.sub(r'[^\w\s-]', '', name)
    
    # Replace spaces and consecutive dashes/underscores
    name = re.sub(r'[-\s]+', '-', name)
    name = re.sub(r'_+', '_', name)
    
    # Convert to lowercase
    name = name.lower().strip('-_')
    
    # Handle Windows reserved device names
    windows_reserved = [
        'con', 'prn', 'aux', 'nul',
        'com1', 'com2', 'com3', 'com4', 'com5', 'com6', 'com7', 'com8', 'com9',
        'lpt1', 'lpt2', 'lpt3', 'lpt4', 'lpt5', 'lpt6', 'lpt7', 'lpt8', 'lpt9'
    ]
    
    if name in windows_reserved:
        name = f"archetype_{name}"  # Prefix to make safe
    
    # Limit length
    name = name[:100]
    
    if not name:
        raise ValueError("Sanitized name is empty")
    
    return name


@dataclass
class ArchetypeConcept:
    """Input specification for new archetype."""
    name: str
    concept: str  # 2-3 sentence description
    primary_trait: str  # e.g., "predatory", "mindless", "cursed"
    optional_context: Dict = None  # Additional context if needed


@dataclass
class ArchetypeProfile:
    """Complete archetype profile output."""
    archetype_name: str
    core_identity: Dict  # base_nature, transformation, conflicts, traits
    behavioral_traits: Dict  # personality, dialogue, actions, emotions, worldview, social, goals
    dark_world_integration: Dict  # clients, drugs, body_parts, specialties
    narrative_hooks: Dict  # origin, relationships, story_arcs
    generation_metadata: Dict  # timestamp, model, version


class NarrativeDesignAI:
    """
    Stage 1: Narrative Design AI
    
    Generates complete archetype profiles using Story Teller (Gemini 2.5 Pro).
    
    Collaborates with existing Story Teller system that has:
    - Designed 8 Dark World families
    - Designed dual empire mechanics
    - Designed death system (Debt of Flesh)
    - Designed morality system
    """
    
    def __init__(self, model: str = "google/gemini-2.5-pro"):
        self.model = model
        self.story_teller_context = self._load_story_teller_context()
        logger.info(f"Narrative Design AI initialized with {model}")
    
    def _load_story_teller_context(self) -> Dict:
        """Load existing Story Teller context for consistency."""
        return {
            "game_world": "The Body Broker",
            "genre": "Dark fantasy body-harvesting operation",
            "player_role": "Body broker who kills humans, harvests parts, sells to Dark World",
            "dark_families": [
                "Carrion Kin", "Chatter-Swarm", "Stitch-Guild", "Moon-Clans",
                "Vampiric Houses", "Obsidian Synod", "Silent Court/Fae", "Leviathan Conclave"
            ],
            "dark_drugs": [
                "Grave-Dust", "Hive-Nectar", "Still-Blood", "Moon-Wine",
                "Vitae", "Logic-Spore", "Enchantments", "Aether"
            ],
            "core_loop": "Kill → Harvest → Negotiate → Get Drugs → Build Empire → Repeat",
            "morality_system": "Surgeon path (only bad guys) vs Butcher path (anyone)",
            "death_system": "Debt of Flesh (Soul-Echo, Corpse-Tender, naked runs)",
            "story_teller_quote": "Forget being a hero. We are building a monster. A king."
        }
    
    def design_archetype(self, concept: ArchetypeConcept) -> ArchetypeProfile:
        """
        Generate complete archetype profile from concept.
        
        Uses Story Teller (Gemini 2.5 Pro) to create comprehensive character design
        consistent with The Body Broker universe.
        """
        logger.info(f"\n{'='*60}\nDesigning Archetype: {concept.name}\n{'='*60}")
        
        # Validate input concept (edge cases)
        self._validate_concept(concept)
        
        logger.info(f"Concept: {concept.concept}")
        
        # Build comprehensive design prompt
        prompt = self._build_design_prompt(concept)
        
        # Call Story Teller via OpenRouter MCP (with retry logic)
        profile_json = self._call_story_teller_with_retry(prompt, max_retries=3)
        
        # Parse and validate profile
        profile = self._parse_profile(profile_json, concept.name)
        
        # Validate completeness and quality
        self._validate_profile(profile)
        
        # Save profile (atomic write)
        self._save_profile(profile)
        
        logger.info(f"✅ Archetype profile complete: {concept.name}")
        return profile
    
    def _validate_concept(self, concept: ArchetypeConcept) -> None:
        """Validate input concept for edge cases."""
        # Check name
        if not concept.name or not concept.name.strip():
            raise ValueError("Archetype name cannot be empty")
        
        if len(concept.name) > 100:
            raise ValueError(f"Archetype name too long: {len(concept.name)} chars (max 100)")
        
        # Check concept description
        if not concept.concept or not concept.concept.strip():
            raise ValueError("Concept description cannot be empty")
        
        if len(concept.concept) < 20:
            raise ValueError(f"Concept too short: {len(concept.concept)} chars (min 20)")
        
        if len(concept.concept) > 5000:
            raise ValueError(f"Concept too long: {len(concept.concept)} chars (max 5000)")
        
        # Check primary trait
        if not concept.primary_trait or not concept.primary_trait.strip():
            raise ValueError("Primary trait cannot be empty")
        
        logger.debug("✅ Concept validation passed")
    
    def _build_design_prompt(self, concept: ArchetypeConcept) -> str:
        """Build comprehensive design prompt for Story Teller."""
        
        context = self.story_teller_context
        
        prompt = f"""
# ARCHETYPE DESIGN REQUEST - The Body Broker

## Context
You are Story Teller, narrative designer for The Body Broker - a dark fantasy game about body-harvesting.

**Your Previous Work**:
- 8 Dark World client families
- Dual empire mechanics (Drug Empire + Dark Politics)
- Morality system (Surgeon vs Butcher)
- Death system (Debt of Flesh)
- Your quote: "{context['story_teller_quote']}"

## New Archetype to Design

**Name**: {concept.name}
**Concept**: {concept.concept}
**Primary Trait**: {concept.primary_trait}

## Required Output

Design a COMPLETE archetype profile in JSON format with these sections:

### 1. core_identity
```json
{{
  "base_nature": "What this creature fundamentally is",
  "transformation_or_curse": "How they became what they are (if applicable)",
  "internal_conflicts": ["List of 3-5 internal struggles"],
  "unique_traits": ["List of 5-8 defining characteristics"],
  "relationship_to_humanity": "How they view/interact with humans",
  "relationship_to_death": "How they relate to death/killing"
}}
```

### 2. behavioral_traits
```json
{{
  "personality": ["5-8 personality traits"],
  "dialogue_patterns": ["5-8 speech characteristics"],
  "action_tendencies": ["5-8 behavioral patterns"],
  "emotional_range": ["5-8 emotions they experience"],
  "world_view": ["5-8 beliefs about the world"],
  "social_dynamics": ["5-8 social behavior patterns"],
  "goals_and_motivations": ["5-8 driving goals"]
}}
```

### 3. dark_world_integration
```json
{{
  "primary_clients": ["Which Dark World families they serve/relate to"],
  "secondary_clients": ["Other families they might interact with"],
  "preferred_drugs": ["Which Dark drugs they want/use"],
  "body_part_specialties": ["What body parts they're known for"],
  "reputation_among_families": "How Dark World sees them",
  "role_in_dark_economy": "Their place in the body broker ecosystem"
}}
```

### 4. narrative_hooks
```json
{{
  "origin_stories": ["3-5 possible backstories"],
  "key_relationships": ["Relationships with other archetypes"],
  "story_arcs": ["3-5 potential character arc paths"],
  "tragic_elements": ["What makes them tragic/sympathetic"],
  "horror_elements": ["What makes them terrifying"],
  "player_interaction_opportunities": ["How players engage with them"]
}}
```

## Design Guidelines

1. **Stay True to The Body Broker Vision**:
   - Dark, ruthless, no heroes
   - Body harvesting is the core mechanic
   - Moral complexity (not just evil)
   - Tragic and terrifying simultaneously

2. **Make Them Distinct**:
   - Must be clearly different from Vampire and Zombie
   - Unique voice/personality
   - Unique relationship to death
   - Unique Dark World connections

3. **Make Them Playable**:
   - Interesting to interact with
   - Depth and complexity
   - Not one-dimensional
   - Room for character development

4. **Dark World Integration**:
   - Must fit within existing 8 families
   - Must have drug preferences
   - Must have body part specialties
   - Must make sense in the economy

## Output Format

Provide ONLY valid JSON with the 4 sections above. No additional text.

Begin:
"""
        
        return prompt
    
    def _call_story_teller_with_retry(self, prompt: str, max_retries: int = 3) -> str:
        """
        Call Story Teller with retry logic for failures.
        
        Implements exponential backoff for transient failures.
        """
        last_error = None
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Calling Story Teller (attempt {attempt + 1}/{max_retries})...")
                return self._call_story_teller(prompt)
            
            except Exception as e:
                last_error = e
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
                
                if attempt < max_retries - 1:
                    # Exponential backoff
                    wait_time = 2 ** attempt  # 1s, 2s, 4s
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
        
        # All retries failed
        raise RuntimeError(f"Story Teller call failed after {max_retries} attempts: {last_error}")
    
    def _call_story_teller(self, prompt: str) -> str:
        """
        Call Story Teller (Gemini 2.5 Pro) via OpenRouter MCP.
        
        Note: This is a placeholder - actual implementation will use MCP.
        For now, returns structured template that must be filled manually.
        """
        logger.info("Calling Story Teller (Gemini 2.5 Pro)...")
        
        # TODO: Implement actual MCP call
        # from mcp_integration import mcp_openrouterai_chat_completion
        # response = mcp_openrouterai_chat_completion(
        #     model=self.model,
        #     messages=[{"role": "user", "content": prompt}],
        #     max_tokens=4000
        # )
        # return response['choices'][0]['message']['content']
        
        # For now, return template structure
        logger.warning("⚠️ MCP call not implemented - returning template")
        logger.warning("⚠️ Production will implement actual API call")
        
        template = {
            "core_identity": {
                "base_nature": "TO_BE_FILLED",
                "transformation_or_curse": "TO_BE_FILLED",
                "internal_conflicts": ["TO_BE_FILLED"],
                "unique_traits": ["TO_BE_FILLED"],
                "relationship_to_humanity": "TO_BE_FILLED",
                "relationship_to_death": "TO_BE_FILLED"
            },
            "behavioral_traits": {
                "personality": ["TO_BE_FILLED"],
                "dialogue_patterns": ["TO_BE_FILLED"],
                "action_tendencies": ["TO_BE_FILLED"],
                "emotional_range": ["TO_BE_FILLED"],
                "world_view": ["TO_BE_FILLED"],
                "social_dynamics": ["TO_BE_FILLED"],
                "goals_and_motivations": ["TO_BE_FILLED"]
            },
            "dark_world_integration": {
                "primary_clients": ["TO_BE_FILLED"],
                "secondary_clients": ["TO_BE_FILLED"],
                "preferred_drugs": ["TO_BE_FILLED"],
                "body_part_specialties": ["TO_BE_FILLED"],
                "reputation_among_families": "TO_BE_FILLED",
                "role_in_dark_economy": "TO_BE_FILLED"
            },
            "narrative_hooks": {
                "origin_stories": ["TO_BE_FILLED"],
                "key_relationships": ["TO_BE_FILLED"],
                "story_arcs": ["TO_BE_FILLED"],
                "tragic_elements": ["TO_BE_FILLED"],
                "horror_elements": ["TO_BE_FILLED"],
                "player_interaction_opportunities": ["TO_BE_FILLED"]
            }
        }
        
        return json.dumps(template, indent=2)
    
    def _parse_profile(self, profile_json: str, archetype_name: str) -> ArchetypeProfile:
        """Parse JSON response into ArchetypeProfile."""
        try:
            data = json.loads(profile_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON from Story Teller: {e}")
        
        # Create profile object
        profile = ArchetypeProfile(
            archetype_name=archetype_name,
            core_identity=data.get('core_identity', {}),
            behavioral_traits=data.get('behavioral_traits', {}),
            dark_world_integration=data.get('dark_world_integration', {}),
            narrative_hooks=data.get('narrative_hooks', {}),
            generation_metadata={
                'generated_at': datetime.now().isoformat(),
                'model': self.model,
                'version': '1.0'
            }
        )
        
        return profile
    
    def _validate_profile(self, profile: ArchetypeProfile) -> None:
        """Validate profile completeness and field types."""
        required_sections = {
            'core_identity': {
                'required_fields': ['base_nature', 'internal_conflicts', 'unique_traits'],
                'field_types': {'base_nature': str, 'internal_conflicts': list, 'unique_traits': list}
            },
            'behavioral_traits': {
                'required_fields': ['personality', 'dialogue_patterns', 'action_tendencies'],
                'field_types': {'personality': list, 'dialogue_patterns': list, 'action_tendencies': list}
            },
            'dark_world_integration': {
                'required_fields': ['primary_clients', 'preferred_drugs'],
                'field_types': {'primary_clients': list, 'preferred_drugs': list}
            },
            'narrative_hooks': {
                'required_fields': ['origin_stories', 'story_arcs'],
                'field_types': {'origin_stories': list, 'story_arcs': list}
            }
        }
        
        for section_name, section_spec in required_sections.items():
            data = getattr(profile, section_name)
            
            # Check section exists and not empty
            if not data or not isinstance(data, dict):
                raise ValueError(f"Missing or invalid section: {section_name}")
            
            # Check for placeholder text
            json_str = json.dumps(data)
            if 'TO_BE_FILLED' in json_str:
                raise ValueError(f"Profile contains placeholders in {section_name}")
            
            # Validate required fields exist
            for field in section_spec['required_fields']:
                if field not in data:
                    raise ValueError(f"Missing required field '{field}' in {section_name}")
                
                # Validate field type
                expected_type = section_spec['field_types'].get(field)
                if expected_type and not isinstance(data[field], expected_type):
                    raise TypeError(f"Field '{field}' in {section_name} should be {expected_type.__name__}, got {type(data[field]).__name__}")
                
                # Validate list fields are not empty
                if expected_type == list and len(data[field]) == 0:
                    raise ValueError(f"Field '{field}' in {section_name} cannot be empty list")
        
        logger.info("✅ Profile validation passed (structure + types + content)")
    
    def _save_profile(self, profile: ArchetypeProfile) -> None:
        """Save profile to JSON file with atomic write and collision handling."""
        # Resolve output directory relative to script
        script_dir = Path(__file__).parent.resolve()
        output_dir = script_dir / "profiles"
        
        # Ensure directory exists
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise RuntimeError(f"Failed to create profiles directory: {e}")
        
        # Sanitize filename (prevent path traversal)
        safe_name = sanitize_filename(profile.archetype_name)
        base_output_path = output_dir / f"{safe_name}_profile.json"
        
        # Handle filename collisions (CRITICAL for production)
        output_path = base_output_path
        collision_suffix = 1
        
        while output_path.exists():
            # File exists - add suffix to avoid overwrite
            output_path = output_dir / f"{safe_name}_{collision_suffix}_profile.json"
            collision_suffix += 1
            
            if collision_suffix > 1000:
                raise RuntimeError(f"Too many collisions for {safe_name} (>1000)")
        
        # Security: Ensure output is within profiles directory
        output_path = output_path.resolve()
        if not str(output_path).startswith(str(output_dir)):
            raise ValueError(f"Path traversal detected in profile save: {profile.archetype_name}")
        
        # Convert to dict
        profile_dict = {
            'archetype_name': profile.archetype_name,
            'core_identity': profile.core_identity,
            'behavioral_traits': profile.behavioral_traits,
            'dark_world_integration': profile.dark_world_integration,
            'narrative_hooks': profile.narrative_hooks,
            'generation_metadata': profile.generation_metadata
        }
        
        # Atomic write with fsync (prevent corruption + ensure durability)
        temp_fd, temp_path = tempfile.mkstemp(
            dir=output_dir,
            prefix=f".{safe_name}_profile.tmp_",
            suffix=".json"
        )
        
        try:
            with os.fdopen(temp_fd, 'w') as f:
                json.dump(profile_dict, f, indent=2)
                f.flush()
                os.fsync(f.fileno())  # Ensure data written to disk
            
            # Atomic move (os.replace on same filesystem)
            os.replace(temp_path, output_path)
            
            # Fsync directory to ensure directory entry persists
            dir_fd = os.open(output_dir, os.O_RDONLY)
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
                
        except Exception as e:
            try:
                os.unlink(temp_path)
            except:
                pass
            raise RuntimeError(f"Failed to save profile: {e}")
        
        logger.info(f"Profile saved: {output_path}")


def test_narrative_design():
    """Test narrative design with sample archetype."""
    print("\n=== Testing Narrative Design AI ===")
    
    concept = ArchetypeConcept(
        name="werewolf",
        concept="A cursed human who transforms under the full moon, torn between human morality and primal hunger.",
        primary_trait="cursed"
    )
    
    ai = NarrativeDesignAI()
    
    try:
        profile = ai.design_archetype(concept)
        print(f"✅ Profile generated for {profile.archetype_name}")
        print(f"   Core identity: {len(profile.core_identity)} fields")
        print(f"   Behavioral traits: {len(profile.behavioral_traits)} fields")
        print(f"   Dark World integration: {len(profile.dark_world_integration)} fields")
        print(f"   Narrative hooks: {len(profile.narrative_hooks)} fields")
        return True
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False


if __name__ == "__main__":
    success = test_narrative_design()
    exit(0 if success else 1)

