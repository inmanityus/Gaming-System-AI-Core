"""
AI Language Generator Module
=============================

Integrates language generation with AI models using:
- LLMClient for model inference
- CostBenefitRouter for optimal model selection
- SRL→RLVR training system for continuous improvement
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from services.ai_integration.llm_client import LLMClient
from services.model_management.cost_benefit_router import CostBenefitRouter, RoutingDecision
from services.language_system.core.language_definition import LanguageDefinition
from .training_integration import LanguageTrainingPipeline, LanguageTrainingData

logger = logging.getLogger(__name__)


@dataclass
class LanguageRequest:
    """Request for AI-powered language generation."""
    language: LanguageDefinition
    intent: str  # What to express
    context: Dict[str, Any] = field(default_factory=dict)
    emotion: Optional[str] = None
    complexity: int = 1  # 1-5, affects model tier selection
    max_latency_ms: float = 500.0  # Maximum acceptable latency
    use_srl_model: bool = True  # Use SRL-trained models if available
    task_type: str = "language_generation"  # For routing


@dataclass
class LanguageGenerationResult:
    """Result of AI language generation."""
    generated_text: str
    language: str
    model_used: str
    model_tier: str  # gold, silver, bronze
    latency_ms: float
    cost_estimate: float
    confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)


class AILanguageGenerator:
    """
    AI-powered language generator using multi-tier model architecture.
    
    Integrates with:
    - LLMClient for model inference
    - CostBenefitRouter for optimal model selection
    - SRL→RLVR training system for continuous improvement
    """
    
    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        cost_benefit_router: Optional[CostBenefitRouter] = None,
        training_pipeline: Optional[LanguageTrainingPipeline] = None
    ):
        """
        Initialize AI Language Generator.
        
        Args:
            llm_client: LLM client instance (created if None)
            cost_benefit_router: Cost-benefit router instance (created if None)
            training_pipeline: Training pipeline for SRL→RLVR integration
        """
        self.llm_client = llm_client or LLMClient()
        self.router = cost_benefit_router or CostBenefitRouter(
            model_registry=self.llm_client.model_registry
        )
        self.training_pipeline = training_pipeline
        
        # Task type mapping for routing
        self.task_type_mapping = {
            "simple": "interaction",  # Gold tier
            "complex": "customization",  # Silver tier
            "expert": "coordination",  # Bronze tier
        }
        
        logger.info("AILanguageGenerator initialized")
    
    async def generate_language_content(
        self,
        request: LanguageRequest
    ) -> LanguageGenerationResult:
        """
        Generate language content using AI models.
        
        Args:
            request: Language generation request
            
        Returns:
            LanguageGenerationResult with generated content and metadata
        """
        import time
        start_time = time.time()
        
        logger.info(
            f"Generating language content: {request.language.name}, "
            f"intent={request.intent}, complexity={request.complexity}"
        )
        
        # Step 1: Determine task type based on complexity
        task_type = self._determine_task_type(request.complexity)
        
        # Step 2: Route to optimal model using CostBenefitRouter
        routing_decision = await self._route_to_model(request, task_type)
        
        # Step 3: Build prompt for language generation
        prompt = self._build_language_prompt(request, routing_decision)
        
        # Step 4: Generate using LLMClient
        try:
            # Map task type to layer
            layer_map = {
                "interaction": "interaction",
                "customization": "customization",
                "coordination": "coordination",
            }
            layer = layer_map.get(task_type, "interaction")
            
            # Build context for LLMClient
            context = {
                "language": request.language.name,
                "language_type": request.language.language_type.value,
                "intent": request.intent,
                "emotion": request.emotion,
                "complexity": request.complexity,
                "priority": "balanced",
                "use_srl_model": request.use_srl_model,
            }
            
            response = await self.llm_client.generate_text(
                layer=layer,
                prompt=prompt,
                context=context,
                max_tokens=500,
                temperature=0.7
            )
            
            # Extract generated text
            generated_text = response.get("text", "") if isinstance(response, dict) else str(response)
            
            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            
            # Create result
            result = LanguageGenerationResult(
                generated_text=generated_text.strip(),
                language=request.language.name,
                model_used=routing_decision.selected_model_name,
                model_tier=routing_decision.reasoning.split("tier:")[-1].split()[0] if "tier:" in routing_decision.reasoning else "unknown",
                latency_ms=latency_ms,
                cost_estimate=routing_decision.cost_estimate,
                confidence=routing_decision.confidence,
                metadata={
                    "task_type": task_type,
                    "routing_decision": routing_decision.reasoning,
                    "prompt_length": len(prompt),
                    "response_length": len(generated_text),
                }
            )
            
            logger.info(
                f"Generated language content: {len(generated_text)} chars, "
                f"latency={latency_ms:.2f}ms, tier={result.model_tier}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating language content: {e}", exc_info=True)
            raise
    
    async def generate_batch(
        self,
        requests: List[LanguageRequest]
    ) -> List[LanguageGenerationResult]:
        """
        Generate language content for multiple requests in parallel.
        
        Args:
            requests: List of language generation requests
            
        Returns:
            List of generation results
        """
        tasks = [self.generate_language_content(req) for req in requests]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and log them
        valid_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error in batch generation for request {i}: {result}")
            else:
                valid_results.append(result)
        
        return valid_results
    
    def _determine_task_type(self, complexity: int) -> str:
        """Determine task type based on complexity."""
        if complexity <= 2:
            return "interaction"  # Gold tier
        elif complexity <= 4:
            return "customization"  # Silver tier
        else:
            return "coordination"  # Bronze tier
    
    async def _route_to_model(
        self,
        request: LanguageRequest,
        task_type: str
    ) -> RoutingDecision:
        """
        Route to optimal model using CostBenefitRouter.
        
        Args:
            request: Language generation request
            task_type: Task type for routing
            
        Returns:
            RoutingDecision with selected model
        """
        # Map task type to routing parameters
        routing_params = {
            "task_type": task_type,
            "complexity": request.complexity,
            "latency_requirement": request.max_latency_ms,
            "use_case": "language_generation",
            "language_type": request.language.language_type.value,
        }
        
        # Get routing decision
        decision = await self.router.select_model(**routing_params)
        
        logger.debug(
            f"Routed to model: {decision.selected_model_name} "
            f"(tier={decision.reasoning}, confidence={decision.confidence:.2f})"
        )
        
        return decision
    
    def _build_language_prompt(
        self,
        request: LanguageRequest,
        routing_decision: RoutingDecision
    ) -> str:
        """
        Build prompt for language generation.
        
        Args:
            request: Language generation request
            routing_decision: Routing decision with model info
            
        Returns:
            Formatted prompt string
        """
        language = request.language
        
        # Build language context
        language_context = f"""
Language: {language.name}
Type: {language.language_type.value}
Family: {language.language_family}
Culture: {language.culture}

Phoneme Inventory:
- Vowels: {', '.join(language.phoneme_inventory.vowels[:10])}
- Consonants: {', '.join(language.phoneme_inventory.consonants[:10])}

Grammar:
- Word Order: {language.grammar_rules.word_order}
- Morphological Type: {language.grammar_rules.morphological_type}

Vocabulary (sample):
{self._format_vocabulary_sample(language.lexicon)}

AI Model Hints:
{language.ai_model_hints or "Generate authentic language content consistent with the language definition."}
"""
        
        # Build intent and context
        intent_section = f"""
Intent: {request.intent}
"""
        
        if request.emotion:
            intent_section += f"Emotion: {request.emotion}\n"
        
        if request.context:
            context_section = "\nContext:\n"
            for key, value in request.context.items():
                context_section += f"- {key}: {value}\n"
        else:
            context_section = ""
        
        # Build full prompt
        prompt = f"""You are a language generation system for a game. Generate text in the specified language that expresses the given intent.

{language_context}

{intent_section}
{context_section}

Instructions:
1. Generate text ONLY in the specified language ({language.name})
2. Use the phoneme inventory and grammar rules provided
3. Express the intent naturally and authentically
4. Maintain consistency with the language's vocabulary and structure
5. If the language is a made-up language (monster/ritual/ancient), create new words following the phonotactics
6. If the language is a real language, use authentic grammar and vocabulary

Generate the text now:"""
        
        return prompt.strip()
    
    def _format_vocabulary_sample(self, lexicon) -> str:
        """Format vocabulary sample for prompt."""
        sample = []
        
        # Add root words
        if lexicon.root_words:
            root_sample = list(lexicon.root_words.items())[:5]
            sample.append("Root words:")
            for concept, word in root_sample:
                sample.append(f"  - {concept}: {word}")
        
        # Add semantic domains
        if lexicon.semantic_domains:
            sample.append("\nSemantic domains:")
            for domain, words in list(lexicon.semantic_domains.items())[:3]:
                sample.append(f"  - {domain}: {', '.join(words[:5])}")
        
        return "\n".join(sample) if sample else "No vocabulary defined yet."


class LanguageGenerator:
    """
    Main interface for language generation.
    
    Combines procedural generation (SentenceGenerator) with AI generation (AILanguageGenerator).
    """
    
    def __init__(
        self,
        ai_generator: Optional[AILanguageGenerator] = None,
        use_ai: bool = True
    ):
        """
        Initialize Language Generator.
        
        Args:
            ai_generator: AI language generator instance
            use_ai: Whether to use AI generation (True) or procedural only (False)
        """
        from .sentence_generator import SentenceGenerator
        
        self.sentence_generator = SentenceGenerator()
        self.ai_generator = ai_generator or AILanguageGenerator()
        self.use_ai = use_ai
        
        logger.info(f"LanguageGenerator initialized (use_ai={use_ai})")
    
    async def generate_sentence(
        self,
        language: LanguageDefinition,
        intent: str,
        context: Optional[Dict[str, Any]] = None,
        emotion: Optional[str] = None,
        complexity: int = 1,
        use_ai: Optional[bool] = None
    ) -> str:
        """
        Generate a sentence in the specified language.
        
        Args:
            language: Language definition
            intent: What the sentence should express
            context: Additional context
            emotion: Emotion to convey
            complexity: Complexity level (1-5)
            use_ai: Override default AI usage
            
        Returns:
            Generated sentence
        """
        use_ai_generation = use_ai if use_ai is not None else self.use_ai
        
        if use_ai_generation and complexity >= 2:
            # Use AI generation for complex sentences
            request = LanguageRequest(
                language=language,
                intent=intent,
                context=context or {},
                emotion=emotion,
                complexity=complexity
            )
            
            result = await self.ai_generator.generate_language_content(request)
            return result.generated_text
        else:
            # Use procedural generation for simple sentences
            from .sentence_generator import SentenceRequest
            
            request = SentenceRequest(
                language=language,
                intent=intent,
                context=context,
                emotion=emotion,
                complexity=complexity
            )
            
            return self.sentence_generator.generate(request)

