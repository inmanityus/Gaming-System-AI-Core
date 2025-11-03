"""
Verifier (Model C)
==================

Validates expert trajectories, enforces rules, and produces verification scores.

Role: Ensures generated trajectories are structurally correct, follow game rules,
      and meet quality standards before being used for training.
"""

import logging
import json
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from .cloud_llm_client import CloudLLMClient
from .rules_engine_client import RulesEngineClient
from .teacher_planner import ExpertTrajectory

logger = logging.getLogger(__name__)


@dataclass
class VerificationResult:
    """Result of trajectory verification."""
    is_valid: bool
    score: float  # 0.0 to 1.0
    issues: List[str]
    corrected_trajectory: Optional[Dict[str, Any]] = None


class Verifier:
    """
    Verifies and validates expert trajectories.
    
    This is Model C in the three-model collaboration system.
    Uses cloud LLMs and rules engine to validate trajectories.
    """
    
    def __init__(
        self,
        rules_engine_url: str,
        cloud_llm_client: Optional[CloudLLMClient] = None,
        model: str = "openai/gpt-5-pro",
        min_score: float = 0.7
    ):
        """
        Initialize Verifier.
        
        Args:
            rules_engine_url: URL to dynamic rules engine
            cloud_llm_client: Client for cloud LLM validation (defaults to new)
            model: Model identifier for OpenRouter API
            min_score: Minimum score for trajectory to be valid
        """
        self.rules_engine_client = RulesEngineClient(rules_engine_url)
        self.llm_client = cloud_llm_client or CloudLLMClient()
        self.model = model
        self.min_score = min_score
        logger.info(f"Verifier initialized with model {model}, min_score={min_score}")
    
    async def verify_trajectory(
        self,
        trajectory: ExpertTrajectory,
        model_type: str,
        rules: Optional[Dict[str, Any]] = None,
        monster_species: Optional[str] = None
    ) -> VerificationResult:
        """
        Verify an expert trajectory against rules and quality standards.
        
        Args:
            trajectory: Expert trajectory to verify
            model_type: Type of model being trained
            rules: Dynamic rules to enforce (fetched if None)
            monster_species: Monster species for rules lookup
        
        Returns:
            VerificationResult: Validation result with score and issues
        """
        logger.info(f"Verifying trajectory for {model_type}")
        
        issues = []
        score = 1.0
        
        # 1. Validate structure
        structure_issues, structure_score = self._validate_structure(trajectory)
        issues.extend(structure_issues)
        score = min(score, structure_score)
        
        # 2. Validate rules compliance
        if rules is None and monster_species:
            # Fetch rules from rules engine
            try:
                rules = await self.rules_engine_client.get_rules(monster_species, model_type)
            except Exception as e:
                logger.warning(f"Could not fetch rules: {e}")
                rules = {}
        
        if rules:
            rules_issues, rules_score = await self._validate_rules_compliance(
                trajectory, rules, model_type
            )
            issues.extend(rules_issues)
            score = min(score, rules_score)
        
        # 3. Validate quality using LLM
        quality_issues, quality_score = await self._validate_quality_llm(
            trajectory, model_type, monster_species
        )
        issues.extend(quality_issues)
        score = min(score, quality_score)
        
        # Determine validity
        is_valid = score >= self.min_score and len([i for i in issues if "critical" in i.lower()]) == 0
        
        # Generate corrected trajectory if needed
        corrected_trajectory = None
        if not is_valid:
            corrected_trajectory = await self._correct_trajectory(trajectory, issues)
        
        result = VerificationResult(
            is_valid=is_valid,
            score=max(0.0, score),  # Ensure non-negative
            issues=issues,
            corrected_trajectory=corrected_trajectory
        )
        
        logger.info(f"Verification complete: valid={is_valid}, score={score:.2f}, issues={len(issues)}")
        return result
    
    def _validate_structure(self, trajectory: ExpertTrajectory) -> Tuple[List[str], float]:
        """Validate trajectory structure."""
        issues = []
        score = 1.0
        
        if not trajectory.steps:
            issues.append("CRITICAL: Trajectory has no steps")
            score -= 0.5
            return issues, score
        
        if len(trajectory.steps) < 3:
            issues.append("Warning: Trajectory has fewer than 3 steps")
            score -= 0.1
        
        if len(trajectory.steps) > 20:
            issues.append("Warning: Trajectory has more than 20 steps (may be too verbose)")
            score -= 0.1
        
        # Validate each step
        total_reward = 0.0
        for i, step in enumerate(trajectory.steps):
            if not isinstance(step, dict):
                issues.append(f"CRITICAL: Step {i+1} is not a dictionary")
                score -= 0.2
                continue
            
            if "action" not in step or not step["action"]:
                issues.append(f"CRITICAL: Step {i+1} missing action")
                score -= 0.2
            
            if "reasoning" not in step or not step["reasoning"]:
                issues.append(f"Warning: Step {i+1} missing reasoning")
                score -= 0.05
            
            if "reward" not in step:
                issues.append(f"CRITICAL: Step {i+1} missing reward")
                score -= 0.15
            else:
                reward = float(step["reward"])
                if reward < 0.0 or reward > 1.0:
                    issues.append(f"Warning: Step {i+1} reward out of range [0,1]: {reward}")
                    score -= 0.05
                total_reward += reward
        
        # Check reward normalization
        if abs(total_reward - 1.0) > 0.2:
            issues.append(f"Warning: Total reward sum is {total_reward:.2f}, expected ~1.0")
            score -= 0.1
        
        if not trajectory.expected_outcome:
            issues.append("Warning: Missing expected outcome")
            score -= 0.05
        
        return issues, max(0.0, score)
    
    async def _validate_rules_compliance(
        self,
        trajectory: ExpertTrajectory,
        rules: Dict[str, Any],
        model_type: str
    ) -> Tuple[List[str], float]:
        """Validate trajectory compliance with rules."""
        issues = []
        score = 1.0
        
        # Extract rules relevant to model type
        model_rules = rules.get("rules", {}).get(model_type, {})
        if not model_rules:
            return issues, score
        
        # Basic rule checking
        # More sophisticated rule validation would require rule engine integration
        if "required_fields" in model_rules:
            required = model_rules["required_fields"]
            for field in required:
                if field not in trajectory.metadata:
                    issues.append(f"Missing required field: {field}")
                    score -= 0.1
        
        return issues, max(0.0, score)
    
    async def _validate_quality_llm(
        self,
        trajectory: ExpertTrajectory,
        model_type: str,
        monster_species: Optional[str]
    ) -> Tuple[List[str], float]:
        """Validate trajectory quality using cloud LLM."""
        issues = []
        score = 1.0
        
        # Build prompt for quality validation
        prompt = self._build_quality_prompt(trajectory, model_type, monster_species)
        
        messages = [
            {"role": "system", "content": self._get_validation_system_prompt()},
            {"role": "user", "content": prompt}
        ]
        
        try:
            validation_text = await self.llm_client.generate(
                messages=messages,
                model=self.model,
                temperature=0.3,  # Lower temperature for more consistent validation
                max_tokens=1000
            )
            
            if validation_text:
                llm_issues, llm_score = self._parse_validation_response(validation_text)
                issues.extend(llm_issues)
                score = min(score, llm_score)
            else:
                logger.warning("LLM validation failed - skipping quality check")
                issues.append("Warning: Could not perform LLM quality validation")
                score -= 0.1
        
        except Exception as e:
            logger.error(f"Error in LLM validation: {e}")
            issues.append("Warning: LLM validation error")
            score -= 0.1
        
        return issues, max(0.0, score)
    
    def _get_validation_system_prompt(self) -> str:
        """Get system prompt for trajectory validation."""
        return """You are an expert validator for AI training trajectories.

Your role is to evaluate the quality and correctness of expert trajectories used for training AI models.

Evaluate:
1. Logical flow: Do steps build on each other logically?
2. Completeness: Is the trajectory complete and coherent?
3. Correctness: Are the actions and reasoning correct?
4. Relevance: Is the trajectory relevant to the model type and game context?
5. Reward distribution: Are rewards appropriately distributed?

Output format (JSON):
{
  "score": 0.85,
  "issues": ["minor issue 1", "minor issue 2"],
  "critical_issues": ["critical issue if any"]
}"""
    
    def _build_quality_prompt(
        self,
        trajectory: ExpertTrajectory,
        model_type: str,
        monster_species: Optional[str]
    ) -> str:
        """Build prompt for quality validation."""
        prompt_parts = [
            f"Model Type: {model_type}",
            f"Problem: {trajectory.problem}",
            f"Expected Outcome: {trajectory.expected_outcome}",
            f"\nTrajectory Steps ({len(trajectory.steps)}):",
        ]
        
        for i, step in enumerate(trajectory.steps, 1):
            prompt_parts.append(
                f"\nStep {i}:\n"
                f"  Action: {step.get('action', 'N/A')}\n"
                f"  Reasoning: {step.get('reasoning', 'N/A')}\n"
                f"  Reward: {step.get('reward', 0.0)}"
            )
        
        if monster_species:
            prompt_parts.append(f"\nMonster Species: {monster_species}")
        
        prompt_parts.append(
            "\nEvaluate this trajectory and provide a score (0.0-1.0) and list any issues."
        )
        
        return "\n".join(prompt_parts)
    
    def _parse_validation_response(self, response_text: str) -> Tuple[List[str], float]:
        """Parse LLM validation response."""
        issues = []
        score = 1.0
        
        try:
            # Try to extract JSON
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            else:
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                json_text = response_text[json_start:json_end] if json_start >= 0 else ""
            
            if json_text:
                parsed = json.loads(json_text)
                score = float(parsed.get("score", 1.0))
                issues.extend(parsed.get("issues", []))
                issues.extend([f"CRITICAL: {i}" for i in parsed.get("critical_issues", [])])
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning(f"Could not parse validation response: {e}")
            # Try to extract score from text
            if "score" in response_text.lower():
                try:
                    score_part = response_text.lower().split("score")[1].strip()[:20]
                    import re
                    score_match = re.search(r'0?\.\d+', score_part)
                    if score_match:
                        score = float(score_match.group())
                except Exception:
                    pass
        
        return issues, max(0.0, min(1.0, score))
    
    async def _correct_trajectory(
        self,
        trajectory: ExpertTrajectory,
        issues: List[str]
    ) -> Optional[Dict[str, Any]]:
        """Attempt to correct trajectory issues using LLM."""
        logger.info(f"Attempting to correct trajectory with {len(issues)} issues")
        
        # Build correction prompt
        prompt = self._build_correction_prompt(trajectory, issues)
        
        messages = [
            {"role": "system", "content": "You are an expert trajectory corrector. Fix issues in trajectories while maintaining their core structure."},
            {"role": "user", "content": prompt}
        ]
        
        try:
            corrected_text = await self.llm_client.generate(
                messages=messages,
                model=self.model,
                temperature=0.5,
                max_tokens=2000
            )
            
            if corrected_text:
                # Parse corrected trajectory
                try:
                    if "```json" in corrected_text:
                        json_start = corrected_text.find("```json") + 7
                        json_end = corrected_text.find("```", json_start)
                        json_text = corrected_text[json_start:json_end].strip()
                    else:
                        json_start = corrected_text.find("{")
                        json_end = corrected_text.rfind("}") + 1
                        json_text = corrected_text[json_start:json_end]
                    
                    corrected = json.loads(json_text)
                    return corrected
                except Exception as e:
                    logger.error(f"Could not parse corrected trajectory: {e}")
                    return None
        
        except Exception as e:
            logger.error(f"Error correcting trajectory: {e}")
            return None
        
        return None
    
    def _build_correction_prompt(self, trajectory: ExpertTrajectory, issues: List[str]) -> str:
        """Build prompt for trajectory correction."""
        prompt_parts = [
            "Original Trajectory:",
            json.dumps(trajectory.to_training_example(), indent=2),
            f"\nIssues to fix ({len(issues)}):",
        ]
        
        for issue in issues:
            prompt_parts.append(f"- {issue}")
        
        prompt_parts.append(
            "\nGenerate a corrected version of this trajectory that fixes all issues "
            "while maintaining the same structure and core approach."
        )
        
        return "\n".join(prompt_parts)
    
    async def verify_batch(
        self,
        trajectories: List[ExpertTrajectory],
        model_type: str,
        rules: Optional[Dict[str, Any]] = None,
        monster_species: Optional[str] = None
    ) -> List[Tuple[ExpertTrajectory, VerificationResult]]:
        """
        Verify a batch of trajectories concurrently.
        
        Args:
            trajectories: List of trajectories to verify
            model_type: Type of model being trained
            rules: Dynamic rules to enforce (shared across batch)
            monster_species: Monster species for rules lookup
        
        Returns:
            List of (trajectory, verification_result) tuples
        """
        logger.info(f"Verifying batch of {len(trajectories)} trajectories")
        
        # Verify all trajectories concurrently
        tasks = [
            self.verify_trajectory(traj, model_type, rules, monster_species)
            for traj in trajectories
        ]
        
        results_list = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine trajectories with results
        results = []
        for traj, result in zip(trajectories, results_list):
            if isinstance(result, Exception):
                logger.error(f"Error verifying trajectory: {result}")
                # Create failure result
                failure_result = VerificationResult(
                    is_valid=False,
                    score=0.0,
                    issues=[f"Verification error: {str(result)}"],
                    corrected_trajectory=None
                )
                results.append((traj, failure_result))
            else:
                results.append((traj, result))
        
        # Log statistics
        valid_count = sum(1 for _, r in results if r.is_valid)
        avg_score = sum(r.score for _, r in results) / len(results) if results else 0.0
        logger.info(f"Batch verification complete: {valid_count}/{len(results)} valid, avg_score={avg_score:.2f}")
        
        return results
    
    async def close(self) -> None:
        """Close all client connections."""
        await self.rules_engine_client.close()
        await self.llm_client.close()

