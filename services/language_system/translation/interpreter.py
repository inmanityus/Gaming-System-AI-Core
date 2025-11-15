from __future__ import annotations

# CROSS-SERVICE IMPORTS DISABLED IN DOCKER CONTAINER
"""
Interpretation Module
=====================

Provides contextual interpretation of language, extracting meaning, intent, and hidden information.
"""

import logging
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from dataclasses import dataclass, field

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

if TYPE_CHECKING:
    from services.language_system.core.language_definition import LanguageRegistry, LanguageDefinition
    from services.language_system.generation.ai_language_generator import AILanguageGenerator
else:
    from services.language_system.core.language_definition import LanguageRegistry, LanguageDefinition
    from services.language_system.generation.ai_language_generator import AILanguageGenerator

logger = logging.getLogger(__name__)


@dataclass
class InterpretationRequest:
    """Request for interpretation."""
    text: str
    language: str
    context: Dict[str, Any] = field(default_factory=dict)
    extract_hidden_meanings: bool = True
    analyze_emotion: bool = True
    detect_intent: bool = True


@dataclass
class InterpretationResult:
    """Result of interpretation."""
    literal_meaning: str
    contextual_meaning: str
    intent: str
    emotion: Optional[str] = None
    hidden_meanings: List[str] = field(default_factory=list)
    cultural_context: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0  # 0.0 to 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class Interpreter:
    """
    Contextual interpreter for extracting meaning from language.
    
    Provides:
    - Literal vs. contextual meaning
    - Intent detection
    - Emotion analysis
    - Hidden meaning extraction
    - Cultural context awareness
    """
    
    def __init__(
        self,
        ai_generator: Optional[AILanguageGenerator] = None
    ):
        """
        Initialize Interpreter.
        
        Args:
            ai_generator: AI language generator for interpretation
        """
        self.ai_generator = ai_generator
        
        logger.info("Interpreter initialized")
    
    async def interpret(
        self,
        request: InterpretationRequest,
        language: LanguageDefinition
    ) -> InterpretationResult:
        """
        Interpret text to extract meaning, intent, and context.
        
        Args:
            request: Interpretation request
            language: Language definition
            
        Returns:
            InterpretationResult with extracted information
        """
        logger.info(f"Interpreting text in {language.name}: {request.text[:50]}...")
        
        # Build interpretation prompt
        prompt = f"""Interpret the following text in {language.name}.

Text: {request.text}

Language Information:
- Type: {language.language_type.value}
- Culture: {language.culture}
- Grammar: {language.grammar_rules.word_order}

Context:
{self._format_context(request.context)}

Tasks:
1. Extract literal meaning (what the words say)
2. Extract contextual meaning (what the speaker means)
3. Detect intent (what the speaker wants)
4. Analyze emotion (emotional tone)
5. Identify hidden meanings (subtext, implications)
6. Note cultural context (cultural significance)

Provide a detailed interpretation."""
        
        # Use AI generator for interpretation
        lang_request = LanguageRequest(
            language=language,
            intent=f"interpret: {request.text}",
            context=request.context,
            complexity=4,  # High complexity for interpretation
        )
        
        if self.ai_generator:
            result = await self.ai_generator.generate_language_content(lang_request)
            interpretation_text = result.generated_text
        else:
            # Fallback to simple interpretation
            interpretation_text = self._simple_interpret(request.text, language)
        
        # Parse interpretation result
        parsed = self._parse_interpretation(interpretation_text, request)
        
        return parsed
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context dictionary for prompt."""
        if not context:
            return "No additional context provided."
        
        lines = []
        for key, value in context.items():
            lines.append(f"- {key}: {value}")
        
        return "\n".join(lines)
    
    def _simple_interpret(self, text: str, language: LanguageDefinition) -> str:
        """Simple fallback interpretation."""
        return f"""
Literal Meaning: {text}
Contextual Meaning: {text} (context-dependent)
Intent: Communication
Emotion: Neutral
Hidden Meanings: None detected
Cultural Context: {language.culture}
"""
    
    def _parse_interpretation(
        self,
        interpretation_text: str,
        request: InterpretationRequest
    ) -> InterpretationResult:
        """Parse AI-generated interpretation into structured result."""
        # Simple parsing (in production, use more sophisticated NLP)
        lines = interpretation_text.split("\n")
        
        literal_meaning = ""
        contextual_meaning = ""
        intent = ""
        emotion = None
        hidden_meanings = []
        cultural_context = {}
        
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detect section headers
            if "literal" in line.lower() and "meaning" in line.lower():
                current_section = "literal"
                literal_meaning = line.split(":", 1)[-1].strip()
            elif "contextual" in line.lower() and "meaning" in line.lower():
                current_section = "contextual"
                contextual_meaning = line.split(":", 1)[-1].strip()
            elif "intent" in line.lower():
                current_section = "intent"
                intent = line.split(":", 1)[-1].strip()
            elif "emotion" in line.lower():
                current_section = "emotion"
                emotion = line.split(":", 1)[-1].strip()
            elif "hidden" in line.lower() and "meaning" in line.lower():
                current_section = "hidden"
            elif "cultural" in line.lower() and "context" in line.lower():
                current_section = "cultural"
            else:
                # Add to current section
                if current_section == "literal" and not literal_meaning:
                    literal_meaning = line
                elif current_section == "contextual" and not contextual_meaning:
                    contextual_meaning = line
                elif current_section == "intent" and not intent:
                    intent = line
                elif current_section == "emotion" and not emotion:
                    emotion = line
                elif current_section == "hidden":
                    if line.startswith("-"):
                        hidden_meanings.append(line[1:].strip())
                elif current_section == "cultural":
                    if ":" in line:
                        key, value = line.split(":", 1)
                        cultural_context[key.strip()] = value.strip()
        
        # Fallbacks if parsing failed
        if not literal_meaning:
            literal_meaning = request.text
        if not contextual_meaning:
            contextual_meaning = request.text
        if not intent:
            intent = "communication"
        
        return InterpretationResult(
            literal_meaning=literal_meaning,
            contextual_meaning=contextual_meaning,
            intent=intent,
            emotion=emotion,
            hidden_meanings=hidden_meanings,
            cultural_context=cultural_context,
            confidence=0.7,  # Default confidence
            metadata={"parsing_method": "simple"}
        )


