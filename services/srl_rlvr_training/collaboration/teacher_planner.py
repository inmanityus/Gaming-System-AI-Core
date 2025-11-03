"""
Teacher Planner (Model B)
==========================

Generates expert step-by-step strategies with reasoning for training examples.

Role: Creates expert trajectories that demonstrate the correct approach to solving
      problems specific to each model type (personality, facial, buildings, etc.).
"""

import logging
import json
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .cloud_llm_client import CloudLLMClient

logger = logging.getLogger(__name__)


@dataclass
class ExpertTrajectory:
    """An expert trajectory with step-by-step reasoning."""
    problem: str
    steps: List[Dict[str, Any]]  # Each step: {"action": str, "reasoning": str, "reward": float}
    expected_outcome: Any
    metadata: Dict[str, Any]
    
    def to_training_example(self) -> Dict[str, Any]:
        """Convert trajectory to training example format."""
        return {
            "problem": self.problem,
            "steps": self.steps,
            "expected_outcome": self.expected_outcome,
            "metadata": self.metadata
        }


class TeacherPlanner:
    """
    Generates expert trajectories for SRL→RLVR training.
    
    This is Model B in the three-model collaboration system.
    Uses cloud LLMs to generate expert step-by-step strategies with reasoning.
    """
    
    def __init__(
        self,
        cloud_llm_client: Optional[CloudLLMClient] = None,
        model: str = "openai/gpt-5-pro"
    ):
        """
        Initialize Teacher Planner.
        
        Args:
            cloud_llm_client: Client for cloud LLM (defaults to new CloudLLMClient)
            model: Model identifier for OpenRouter API
        """
        self.llm_client = cloud_llm_client or CloudLLMClient()
        self.model = model
        logger.info(f"TeacherPlanner initialized with model {model}")
    
    async def generate_trajectory(
        self,
        lore_context: 'LoreContext',  # From LoreRetriever
        model_type: str,
        problem_description: str
    ) -> ExpertTrajectory:
        """
        Generate an expert trajectory for a given problem.
        
        Args:
            lore_context: Context from Lore Retriever
            model_type: Type of model being trained (personality, facial, etc.)
            problem_description: Description of the problem to solve
        
        Returns:
            ExpertTrajectory: Complete expert trajectory with step-by-step reasoning
        """
        logger.info(f"Generating expert trajectory for {model_type}: {problem_description}")
        
        # Build prompt for expert trajectory generation
        prompt = self._build_trajectory_prompt(lore_context, model_type, problem_description)
        
        # Call cloud LLM
        messages = [
            {"role": "system", "content": self._get_system_prompt(model_type)},
            {"role": "user", "content": prompt}
        ]
        
        generated_text = await self.llm_client.generate(
            messages=messages,
            model=self.model,
            temperature=0.7,
            max_tokens=2000
        )
        
        if not generated_text:
            logger.error("Failed to generate trajectory - returning fallback")
            return self._create_fallback_trajectory(problem_description, model_type, lore_context)
        
        # Parse LLM response
        trajectory = self._parse_trajectory_response(
            generated_text, problem_description, model_type, lore_context
        )
        
        return trajectory
    
    def _get_system_prompt(self, model_type: str) -> str:
        """Get system prompt for the specific model type."""
        base_prompt = f"""You are an expert AI trainer generating step-by-step expert trajectories for training {model_type} models in a gaming system.

Your role is to create expert demonstrations that show the CORRECT way to solve problems specific to {model_type} generation.

Requirements:
1. Generate 5-15 detailed steps
2. Each step must have:
   - action: What action to take
   - reasoning: Why this action is correct
   - reward: A reward value between 0.0 and 1.0 (cumulative, should sum to ~1.0)
3. Steps should build on each other logically
4. Final step should produce the expected outcome
5. Use game-specific context and rules

Output format (JSON):
{{
  "steps": [
    {{
      "action": "description of action",
      "reasoning": "why this is correct",
      "reward": 0.15
    }},
    ...
  ],
  "expected_outcome": "description of final result"
}}"""
        
        return base_prompt
    
    def _build_trajectory_prompt(
        self,
        lore_context: 'LoreContext',
        model_type: str,
        problem_description: str
    ) -> str:
        """Build the user prompt for trajectory generation."""
        prompt_parts = [
            f"Problem: {problem_description}",
            f"Model Type: {model_type}",
        ]
        
        if lore_context:
            if lore_context.monster_species:
                prompt_parts.append(f"Monster Species: {lore_context.monster_species}")
            
            if lore_context.game_rules:
                prompt_parts.append(f"\nGame Rules:\n{json.dumps(lore_context.game_rules, indent=2)}")
            
            if lore_context.related_lore:
                prompt_parts.append(f"\nRelated Lore ({len(lore_context.related_lore)} entries):")
                for i, lore in enumerate(lore_context.related_lore[:5], 1):  # Limit to 5
                    prompt_parts.append(f"{i}. {lore}")
        
        prompt_parts.append(
            "\nGenerate an expert trajectory (steps with actions, reasoning, and rewards) "
            "that demonstrates the correct approach to solving this problem. "
            "Ensure the trajectory is specific to the game context and model type."
        )
        
        return "\n".join(prompt_parts)
    
    def _parse_trajectory_response(
        self,
        generated_text: str,
        problem_description: str,
        model_type: str,
        lore_context: Optional['LoreContext']
    ) -> ExpertTrajectory:
        """Parse LLM response into ExpertTrajectory."""
        try:
            # Try to extract JSON from response
            # LLM might wrap JSON in markdown code blocks
            if "```json" in generated_text:
                json_start = generated_text.find("```json") + 7
                json_end = generated_text.find("```", json_start)
                json_text = generated_text[json_start:json_end].strip()
            elif "```" in generated_text:
                json_start = generated_text.find("```") + 3
                json_end = generated_text.find("```", json_start)
                json_text = generated_text[json_start:json_end].strip()
            else:
                # Try to find JSON object in response
                json_start = generated_text.find("{")
                json_end = generated_text.rfind("}") + 1
                if json_start >= 0 and json_end > json_start:
                    json_text = generated_text[json_start:json_end]
                else:
                    raise ValueError("No JSON found in response")
            
            parsed = json.loads(json_text)
            
            steps = parsed.get("steps", [])
            expected_outcome = parsed.get("expected_outcome", "Generated solution")
            
            # Validate and normalize steps
            normalized_steps = []
            for step in steps:
                if isinstance(step, dict):
                    normalized_steps.append({
                        "action": step.get("action", ""),
                        "reasoning": step.get("reasoning", ""),
                        "reward": float(step.get("reward", 0.1))
                    })
            
            if not normalized_steps:
                logger.warning("No valid steps parsed - using fallback")
                return self._create_fallback_trajectory(problem_description, model_type, lore_context)
            
            return ExpertTrajectory(
                problem=problem_description,
                steps=normalized_steps,
                expected_outcome=expected_outcome,
                metadata={
                    "model_type": model_type,
                    "monster_species": lore_context.monster_species if lore_context else None,
                    "num_steps": len(normalized_steps)
                }
            )
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.error(f"Error parsing trajectory response: {e}")
            logger.debug(f"Response text: {generated_text[:500]}")
            return self._create_fallback_trajectory(problem_description, model_type, lore_context)
    
    def _create_fallback_trajectory(
        self,
        problem_description: str,
        model_type: str,
        lore_context: Optional['LoreContext']
    ) -> ExpertTrajectory:
        """Create a fallback trajectory when LLM generation fails."""
        logger.warning("Creating fallback trajectory")
        return ExpertTrajectory(
            problem=problem_description,
            steps=[
                {
                    "action": "analyze_context",
                    "reasoning": "Understanding the problem context and game rules",
                    "reward": 0.2
                },
                {
                    "action": "apply_game_rules",
                    "reasoning": "Applying game-specific rules and constraints",
                    "reward": 0.3
                },
                {
                    "action": "generate_solution",
                    "reasoning": "Generating the solution based on context and rules",
                    "reward": 0.5
                }
            ],
            expected_outcome="Correct solution generated",
            metadata={
                "model_type": model_type,
                "monster_species": lore_context.monster_species if lore_context else None,
                "fallback": True
            }
        )
    
    async def generate_batch(
        self,
        lore_contexts: List['LoreContext'],
        model_type: str,
        num_examples: int = 10,
        problem_descriptions: Optional[List[str]] = None
    ) -> List[ExpertTrajectory]:
        """
        Generate a batch of expert trajectories.
        
        Args:
            lore_contexts: List of lore contexts
            model_type: Type of model being trained
            num_examples: Number of trajectories to generate
            problem_descriptions: Optional list of specific problem descriptions
        
        Returns:
            List[ExpertTrajectory]: Batch of expert trajectories
        """
        logger.info(f"Generating batch of {num_examples} trajectories for {model_type}")
        
        # Generate problem descriptions if not provided
        if not problem_descriptions:
            problem_descriptions = self._generate_problem_descriptions(model_type, num_examples)
        
        # Generate trajectories concurrently (but with rate limiting consideration)
        tasks = []
        for i in range(num_examples):
            lore_context = lore_contexts[i % len(lore_contexts)] if lore_contexts else None
            problem = problem_descriptions[i] if i < len(problem_descriptions) else f"Problem {i+1}"
            tasks.append(
                self.generate_trajectory(lore_context, model_type, problem)
            )
        
        trajectories = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions
        valid_trajectories = []
        for i, traj in enumerate(trajectories):
            if isinstance(traj, Exception):
                logger.error(f"Error generating trajectory {i}: {traj}")
            else:
                valid_trajectories.append(traj)
        
        logger.info(f"Generated {len(valid_trajectories)}/{num_examples} trajectories")
        return valid_trajectories
    
    def _generate_problem_descriptions(self, model_type: str, count: int) -> List[str]:
        """Generate diverse problem descriptions for the model type."""
        # Base problem templates by model type
        templates = {
            "personality": [
                "Generate emotional response for a {species} character feeling anger",
                "Create personality trait expression for {species} showing fear",
                "Design emotional state transition for {species} from neutral to aggressive",
                "Generate personality-appropriate action for {species} encountering a threat",
                "Create emotional dialogue response for {species} in negotiation",
            ],
            "facial": [
                "Generate facial expression for {species} showing surprise",
                "Create emotion blend for {species} (anger + fear)",
                "Design facial animation sequence for {species} emotional transition",
                "Generate micro-expression for {species} subtle emotion",
                "Create facial expression matching {species} personality trait",
            ],
            # Add more templates as needed
        }
        
        base_templates = templates.get(model_type, [
            f"Generate {model_type} output for scenario {{i}}",
            f"Create {model_type} response for situation {{i}}",
        ])
        
        # Repeat and vary templates
        descriptions = []
        for i in range(count):
            template = base_templates[i % len(base_templates)]
            descriptions.append(template.format(species="monster", i=i+1))
        
        return descriptions

