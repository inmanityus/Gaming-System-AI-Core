"""
Training Data Generator AI - Stage 2 of Archetype Automation
Coder: Claude Sonnet 4.5
Reviewer: GPT-Codex-2 (Pending)

Generates 1,500-2,000 training examples per adapter (7 adapters = 10,500-14,000 total examples)
from archetype profiles created by Narrative Design AI.

Uses batch generation with GPT-4 Turbo or Claude 3.5 for efficiency.

Input: Archetype profile (from Stage 1)
Output: Training data files for all 7 adapters (personality, dialogue, action, emotion, worldview, social, goals)

Timeline: 30-60 minutes per archetype (batched generation)
Cost: $5-10 per archetype
"""

import os
import json
import logging
import time
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class GenerationConfig:
    """Configuration for training data generation."""
    examples_per_adapter: int = 1500
    batch_size: int = 50  # Generate 50 examples per API call
    model: str = "gpt-4-turbo"  # Or claude-3.5-sonnet
    max_retries: int = 3
    temperature: float = 0.8  # Higher for creative variety
    quality_threshold: float = 0.85


@dataclass
class TrainingExample:
    """Single training example."""
    input: str
    output: str
    tags: List[str]
    quality_score: float = 0.0


class TrainingDataGeneratorAI:
    """
    Stage 2: Training Data Generator AI
    
    Generates comprehensive training data for all 7 LoRA adapters
    from archetype profile created by Narrative Design AI.
    
    Uses batch generation for efficiency (50 examples per API call).
    """
    
    def __init__(self, config: GenerationConfig = None):
        self.config = config or GenerationConfig()
        logger.info(f"Training Data Generator initialized: {self.config.examples_per_adapter} examples/adapter")
    
    def generate_all_adapters(self, profile: Dict, archetype_name: str) -> Dict[str, List[Dict]]:
        """
        Generate training data for all 7 adapters.
        
        Returns dict mapping adapter_task -> training examples
        """
        logger.info(f"\n{'='*60}\nGenerating Training Data: {archetype_name}\n{'='*60}")
        
        adapters = [
            "personality", "dialogue_style", "action_policy",
            "emotional_response", "world_knowledge",
            "social_dynamics", "goal_prioritization"
        ]
        
        all_data = {}
        
        for adapter in adapters:
            logger.info(f"\nGenerating {adapter} training data...")
            
            examples = self.generate_adapter_data(
                profile, archetype_name, adapter
            )
            
            # Validate quality
            quality_score = self.calculate_quality_score(examples)
            logger.info(f"  Quality score: {quality_score:.2f}")
            
            if quality_score < self.config.quality_threshold:
                logger.warning(f"  ⚠️ Quality below threshold ({quality_score:.2f} < {self.config.quality_threshold})")
                logger.warning(f"  Consider regenerating or adjusting prompts")
            
            all_data[adapter] = {
                'adapter_task': adapter,
                'archetype': archetype_name,
                'examples': examples,
                'total_examples': len(examples),
                'quality_score': quality_score,
                'generated_at': datetime.now().isoformat()
            }
            
            # Save immediately (incremental saves)
            self.save_adapter_data(all_data[adapter], archetype_name, adapter)
        
        logger.info(f"\n✅ All training data generated: {archetype_name}")
        logger.info(f"   Total examples: {sum(len(d['examples']) for d in all_data.values())}")
        
        return all_data
    
    def generate_adapter_data(self, profile: Dict, archetype_name: str, 
                             adapter_task: str) -> List[Dict]:
        """Generate training data for single adapter using batch generation."""
        
        num_batches = (self.config.examples_per_adapter + self.config.batch_size - 1) // self.config.batch_size
        
        all_examples = []
        
        for batch_num in range(num_batches):
            batch_start = batch_num * self.config.batch_size
            batch_end = min(batch_start + self.config.batch_size, self.config.examples_per_adapter)
            batch_size = batch_end - batch_start
            
            logger.info(f"  Batch {batch_num+1}/{num_batches} ({batch_size} examples)...")
            
            try:
                batch_examples = self.generate_batch_with_retry(
                    profile, archetype_name, adapter_task, batch_size
                )
                all_examples.extend(batch_examples)
            except Exception as e:
                logger.error(f"  ❌ Batch {batch_num+1} failed: {e}")
                # Continue with other batches
                continue
        
        logger.info(f"  ✅ Generated {len(all_examples)}/{self.config.examples_per_adapter} examples")
        
        return all_examples
    
    def generate_batch_with_retry(self, profile: Dict, archetype_name: str,
                                   adapter_task: str, batch_size: int) -> List[Dict]:
        """Generate one batch with retry logic."""
        
        for attempt in range(self.config.max_retries):
            try:
                return self.generate_batch(profile, archetype_name, adapter_task, batch_size)
            except Exception as e:
                logger.warning(f"    Attempt {attempt+1} failed: {e}")
                if attempt < self.config.max_retries - 1:
                    wait_time = 2 ** attempt
                    logger.info(f"    Retrying in {wait_time}s...")
                    time.sleep(wait_time)
        
        raise RuntimeError(f"Batch generation failed after {self.config.max_retries} attempts")
    
    def generate_batch(self, profile: Dict, archetype_name: str,
                      adapter_task: str, batch_size: int) -> List[Dict]:
        """Generate one batch of examples via AI API."""
        
        prompt = self.build_generation_prompt(profile, adapter_task, batch_size)
        
        # Call AI API (placeholder - will implement MCP call)
        response_json = self.call_ai_api(prompt)
        
        # Parse examples from response
        examples = self.parse_examples(response_json, adapter_task)
        
        # Validate examples
        validated = self.validate_examples(examples, profile, adapter_task)
        
        return validated
    
    def build_generation_prompt(self, profile: Dict, adapter_task: str, 
                                batch_size: int) -> str:
        """Build prompt for generating training examples."""
        
        archetype_name = profile.get('archetype_name', 'unknown')
        
        # Extract relevant traits for this adapter
        behavioral_traits = profile.get('behavioral_traits', {})
        core_identity = profile.get('core_identity', {})
        
        prompt = f"""
# TRAINING DATA GENERATION - The Body Broker

## Context
Generate {batch_size} high-quality training examples for the **{adapter_task}** adapter 
of the **{archetype_name}** archetype.

## Archetype Profile Summary

**Core Identity**:
{json.dumps(core_identity, indent=2)}

**Behavioral Traits**:
{json.dumps(behavioral_traits, indent=2)}

## Adapter Task: {adapter_task}

"""
        
        # Add task-specific instructions
        if adapter_task == "personality":
            prompt += """
**Generate examples that demonstrate personality traits.**

Format (JSON array of {batch_size} examples):
[
  {{
    "input": "Situation or question that reveals personality",
    "output": "Response showing personality traits consistently",
    "tags": ["personality_trait1", "personality_trait2"]
  }}
]

Example:
{{
  "input": "Someone insults you. How do you react?",
  "output": "The vampire's eyes flash cold fury, but their voice remains aristocratic and measured. 'How... pedestrian. I've ended bloodlines for less, but you're hardly worth the effort. Run along before I change my mind.'",
  "tags": ["aristocratic", "predatory", "controlled_menace"]
}}
"""
        
        elif adapter_task == "dialogue_style":
            prompt += f"""
**Generate examples demonstrating {archetype_name} dialogue patterns.**

Focus on:
- Speech patterns
- Vocabulary choices
- Sentence structure
- Unique verbal mannerisms

Format: Same JSON array structure as above.
"""
        
        # Add for other adapters (abbreviated for brevity)
        else:
            prompt += f"""
**Generate examples for {adapter_task}.**

Format: JSON array of {batch_size} examples with input/output/tags.
"""
        
        prompt += f"""

## Requirements
1. All examples must be in-character for {archetype_name}
2. Diverse scenarios (no repetition)
3. High quality writing
4. Appropriate for dark fantasy setting
5. Match The Body Broker universe tone
6. Each example 50-300 words

Output ONLY the JSON array, no other text.
"""
        
        return prompt
    
    def call_ai_api(self, prompt: str) -> str:
        """
        Call AI API for batch generation.
        
        TODO: Implement OpenRouter MCP or direct API call
        """
        logger.info("    Calling AI API for batch generation...")
        
        # TODO: Implement actual API call
        # response = mcp_openrouterai_chat_completion(
        #     model=self.config.model,
        #     messages=[{"role": "user", "content": prompt}],
        #     temperature=self.config.temperature
        # )
        # return response['choices'][0]['message']['content']
        
        logger.warning("    ⚠️ API call not implemented - returning template")
        
        # Return template for now
        template = [
            {
                "input": "TEMPLATE_INPUT",
                "output": "TEMPLATE_OUTPUT",
                "tags": ["TEMPLATE_TAG"]
            }
        ]
        
        return json.dumps(template)
    
    def parse_examples(self, response_json: str, adapter_task: str) -> List[Dict]:
        """Parse examples from AI response."""
        try:
            examples = json.loads(response_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON from AI: {e}")
        
        if not isinstance(examples, list):
            raise ValueError(f"Expected list of examples, got {type(examples)}")
        
        return examples
    
    def validate_examples(self, examples: List[Dict], profile: Dict, 
                         adapter_task: str) -> List[Dict]:
        """Validate and score examples."""
        validated = []
        
        for i, ex in enumerate(examples):
            # Check required fields
            if not all(k in ex for k in ['input', 'output', 'tags']):
                logger.warning(f"    Example {i+1} missing required fields, skipping")
                continue
            
            # Check for template placeholders
            if 'TEMPLATE' in ex['input'] or 'TEMPLATE' in ex['output']:
                logger.warning(f"    Example {i+1} contains placeholders, skipping")
                continue
            
            # Basic quality checks
            if len(ex['output']) < 50:
                logger.warning(f"    Example {i+1} output too short ({len(ex['output'])} chars), skipping")
                continue
            
            if len(ex['output']) > 2000:
                logger.warning(f"    Example {i+1} output too long ({len(ex['output'])} chars), skipping")
                continue
            
            # Score quality (simplified - real version would use AI)
            quality_score = 0.9  # Placeholder
            ex['quality_score'] = quality_score
            
            validated.append(ex)
        
        logger.info(f"    Validated {len(validated)}/{len(examples)} examples")
        
        return validated
    
    def calculate_quality_score(self, examples: List[Dict]) -> float:
        """Calculate overall quality score for example set."""
        if not examples:
            return 0.0
        
        scores = [ex.get('quality_score', 0.0) for ex in examples]
        return sum(scores) / len(scores)
    
    def save_adapter_data(self, data: Dict, archetype_name: str, adapter_task: str) -> None:
        """Save training data to file (atomic write)."""
        script_dir = Path(__file__).parent.resolve()
        output_dir = script_dir / "data"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create safe filename
        from narrative_design_ai import sanitize_filename
        safe_name = sanitize_filename(archetype_name)
        output_path = output_dir / f"{safe_name}_{adapter_task}_training.json"
        
        # Atomic write with fsync
        temp_fd, temp_path = tempfile.mkstemp(dir=output_dir, suffix=".json")
        
        try:
            with os.fdopen(temp_fd, 'w') as f:
                json.dump(data, f, indent=2)
                f.flush()
                os.fsync(f.fileno())
            
            os.replace(temp_path, output_path)
            
            # Fsync directory
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
            raise RuntimeError(f"Failed to save training data: {e}")
        
        logger.info(f"  Saved: {output_path}")


if __name__ == "__main__":
    # Test with template profile
    test_profile = {
        'archetype_name': 'werewolf',
        'core_identity': {'base_nature': 'Cursed human'},
        'behavioral_traits': {
            'personality': ['Volatile', 'Protective'],
            'dialogue_patterns': ['Growling', 'Short sentences']
        }
    }
    
    generator = TrainingDataGeneratorAI()
    
    # Generate for one adapter (test)
    examples = generator.generate_adapter_data(test_profile, 'werewolf', 'personality')
    print(f"\n✅ Generated {len(examples)} examples")

