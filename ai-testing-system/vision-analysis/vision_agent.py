#!/usr/bin/env python3
"""
Vision Analysis Agent
Multi-Model Consensus Engine for Game Screenshot Analysis
Part of AI-Driven Game Testing System (Tier 2)

Models:
- Gemini 2.5 Pro: Horror atmosphere specialist
- GPT-4o: UX and clarity specialist
- Claude Sonnet 4.5: Visual bug detective
"""

import os
import json
import logging
import base64
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import requests
from anthropic import Anthropic
import google.generativeai as genai
from openai import OpenAI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


class AnalysisCategory(str, Enum):
    ATMOSPHERE = "atmosphere"
    UX = "ux"
    VISUAL_BUG = "visual_bug"
    PERFORMANCE = "performance"


@dataclass
class AnalysisResult:
    """Vision analysis result from a single model"""
    model_name: str
    confidence: float  # 0.0-1.0
    is_issue: bool
    category: AnalysisCategory
    description: str
    recommendations: List[str]
    raw_response: Optional[Dict] = None


class VisionAnalysisAgent:
    """
    Multi-Model Vision Analysis Agent
    
    Specializations:
    - Gemini 2.5 Pro: Horror atmosphere (lighting, composition, color palette)
    - GPT-4o: UX/UI clarity (readability, navigation, objectives)
    - Claude Sonnet 4.5: Visual bugs (clipping, textures, animations)
    """
    
    def __init__(self):
        # Initialize API clients
        self.anthropic_client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.gemini_model = genai.GenerativeModel('gemini-2.5-pro')
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        logger.info("Vision Analysis Agent initialized with 3 models")
    
    async def analyze_capture(
        self,
        screenshot_url: str,
        telemetry_data: Dict
    ) -> List[AnalysisResult]:
        """
        Analyze game screenshot with all 3 vision models
        Returns list of analysis results for consensus evaluation
        """
        logger.info(f"Analyzing capture: {screenshot_url}")
        
        # Download screenshot
        screenshot_data = self._download_screenshot(screenshot_url)
        
        # Run analysis with all 3 models in parallel
        results = []
        
        # Gemini 2.5 Pro - Horror Atmosphere
        try:
            gemini_result = await self._analyze_with_gemini(
                screenshot_data,
                telemetry_data
            )
            results.append(gemini_result)
        except Exception as e:
            logger.error(f"Gemini analysis failed: {e}")
        
        # GPT-5 - UX/Clarity
        try:
            gpt_result = await self._analyze_with_gpt5(
                screenshot_data,
                telemetry_data
            )
            results.append(gpt_result)
        except Exception as e:
            logger.error(f"GPT-5 analysis failed: {e}")
        
        # Claude Sonnet 4.5 - Visual Bugs
        try:
            claude_result = await self._analyze_with_claude(
                screenshot_data,
                telemetry_data
            )
            results.append(claude_result)
        except Exception as e:
            logger.error(f"Claude analysis failed: {e}")
        
        logger.info(f"Analysis complete: {len(results)}/3 models responded")
        return results
    
    def _download_screenshot(self, url: str) -> bytes:
        """Download screenshot from S3 pre-signed URL"""
        response = requests.get(url)
        response.raise_for_status()
        return response.content
    
    async def _analyze_with_gemini(
        self,
        screenshot_data: bytes,
        telemetry_data: Dict
    ) -> AnalysisResult:
        """
        Gemini 2.5 Pro - Horror Atmosphere Specialist
        
        Evaluates:
        - Luminance histogram (chiaroscuro detection)
        - Color palette (desaturation for horror)
        - Compositional tension
        - Uncanny imagery
        """
        prompt = f"""You are analyzing a screenshot from The Body Broker, a dark fantasy horror game about harvesting human body parts to sell to Dark World creatures.

**Game Context:**
- Zone: {telemetry_data.get('world_data', {}).get('zone_name', 'Unknown')}
- Event: {telemetry_data.get('event_type', 'Unknown')}
- FPS: {telemetry_data.get('rendering_data', {}).get('current_fps', 'Unknown')}

**Your Task: Evaluate Horror Atmosphere Effectiveness**

Analyze the screenshot for:

1. **LIGHTING ANALYSIS**
   - Luminance histogram: Successful horror shows bimodal distribution (deep blacks + focused highlights)
   - Chiaroscuro: Dramatic light/dark contrast
   - **FAILURE**: Flat, even lighting (mid-tone clustering)

2. **COLOR PALETTE**
   - Expected: Desaturated colors, muted palette with symbolic saturated accents
   - Goreforge should have: deep reds, fleshy pinks, bone whites, steely blues
   - **FAILURE**: Oversaturated, vibrant gamut

3. **COMPOSITION**
   - Check for negative space (where threats can hide)
   - Evaluate focal point clarity
   - Detect claustrophobic framing
   - **FAILURE**: Cluttered, noisy composition

4. **UNCANNY IMAGERY**
   - Detect asymmetry in humanoid figures
   - Identify juxtaposition of mundane + grotesque
   - Check for visceral, organic elements

**Output Format (JSON):**
{{
  "horror_effectiveness": 0-100,
  "confidence": 0.0-1.0,
  "is_issue": true/false,
  "issues": ["..."],
  "successes": ["..."],
  "recommendations": ["..."]
}}"""

        # Encode image
        import PIL.Image
        import io
        image = PIL.Image.open(io.BytesIO(screenshot_data))
        
        # Generate content
        response = self.gemini_model.generate_content([prompt, image])
        
        # Parse response
        try:
            result_json = json.loads(response.text)
            
            return AnalysisResult(
                model_name="gemini-2.5-pro",
                confidence=result_json.get("confidence", 0.8),
                is_issue=result_json.get("is_issue", False),
                category=AnalysisCategory.ATMOSPHERE,
                description=f"Horror effectiveness: {result_json.get('horror_effectiveness', 0)}/100. " + 
                            ", ".join(result_json.get("issues", [])),
                recommendations=result_json.get("recommendations", []),
                raw_response=result_json
            )
        except json.JSONDecodeError:
            # Fallback if model doesn't return valid JSON
            return AnalysisResult(
                model_name="gemini-2.5-pro",
                confidence=0.5,
                is_issue=False,
                category=AnalysisCategory.ATMOSPHERE,
                description=response.text[:500],
                recommendations=[]
            )
    
    async def _analyze_with_gpt5(
        self,
        screenshot_data: bytes,
        telemetry_data: Dict
    ) -> AnalysisResult:
        """
        GPT-5 - UX and Clarity Specialist
        
        Evaluates:
        - UI readability (OCR + WCAG contrast)
        - Objective clarity
        - UI obtrusiveness
        - Navigation clarity
        """
        # Encode image to base64
        image_base64 = base64.b64encode(screenshot_data).decode('utf-8')
        
        prompt = f"""You are analyzing a screenshot from The Body Broker game for UX and clarity issues.

**Game Context:**
- Zone: {telemetry_data.get('world_data', {}).get('zone_name', 'Unknown')}
- Objective: {telemetry_data.get('world_data', {}).get('current_objective_id', 'None')}
- In Combat: {telemetry_data.get('player_data', {}).get('is_in_combat', False)}

**Your Task: Identify UX/Clarity Issues**

Evaluate:

1. **UI READABILITY**
   - Text contrast (WCAG AA/AAA compliance)
   - Font sizes (comfortable reading at typical viewing distance)
   - Visibility against backgrounds

2. **OBJECTIVE CLARITY**
   - Is the current objective visible on screen?
   - Is it visually distinct (glow, color, unique silhouette)?
   - Can player determine where to go?

3. **UI OBTRUSIVENESS**
   - Does UI block critical gameplay elements?
   - Are important objects obscured?
   - Is player character visible during combat?

4. **NAVIGATION CLARITY**
   - Are interactive objects obvious?
   - Is the path forward clear?
   - Are important details hidden?

**Output Format (JSON):**
{{
  "confidence": 0.0-1.0,
  "is_issue": true/false,
  "issues_found": ["..."],
  "severity": "low|medium|high",
  "recommendations": ["..."]
}}"""

        response = self.openai_client.chat.completions.create(
            model="gpt-5-turbo",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/png;base64,{image_base64}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=1000
        )
        
        # Parse response
        try:
            result_json = json.loads(response.choices[0].message.content)
            
            return AnalysisResult(
                model_name="gpt-5",
                confidence=result_json.get("confidence", 0.8),
                is_issue=result_json.get("is_issue", False),
                category=AnalysisCategory.UX,
                description=", ".join(result_json.get("issues_found", [])),
                recommendations=result_json.get("recommendations", []),
                raw_response=result_json
            )
        except json.JSONDecodeError:
            return AnalysisResult(
                model_name="gpt-5",
                confidence=0.5,
                is_issue=False,
                category=AnalysisCategory.UX,
                description=response.choices[0].message.content[:500],
                recommendations=[]
            )
    
    async def _analyze_with_claude(
        self,
        screenshot_data: bytes,
        telemetry_data: Dict
    ) -> AnalysisResult:
        """
        Claude Sonnet 4.5 - Visual Bug Detective
        
        Evaluates:
        - Clipping (geometry overlap)
        - Texture issues (missing, low-res, streaming)
        - Lighting problems (bleeding, shadow popping)
        - Animation glitches (T-pose, skating)
        """
        # Encode image to base64
        image_base64 = base64.b64encode(screenshot_data).decode('utf-8')
        
        prompt = f"""You are analyzing a screenshot from The Body Broker game for visual bugs and rendering issues.

**Game Context:**
- FPS: {telemetry_data.get('rendering_data', {}).get('current_fps', 'Unknown')}
- Player Velocity: {telemetry_data.get('player_data', {}).get('velocity', {})}
- Zone: {telemetry_data.get('world_data', {}).get('zone_name', 'Unknown')}

**Your Task: Detect Visual Bugs**

Look for:

1. **CLIPPING**
   - Player/NPC body parts inside walls/objects
   - Weapons clipping through geometry
   - Illogical geometry overlap

2. **TEXTURE ISSUES**
   - Missing textures (checkerboard, bright magenta)
   - Blurry textures (streaming/LOD problems)
   - Texture corruption or artifacts

3. **LIGHTING PROBLEMS**
   - Light bleeding through solid objects
   - Shadow popping (sudden changes not matching movement)
   - Incorrect shadow directions

4. **ANIMATION GLITCHES**
   - T-pose or A-pose (default rig position)
   - Skating (movement without animation)
   - Broken transitions or frozen animations
   - Limb deformation

**Output Format (JSON):**
{{
  "confidence": 0.0-1.0,
  "is_issue": true/false,
  "bugs_detected": ["..."],
  "severity": "low|medium|high|critical",
  "recommendations": ["..."]
}}"""

        response = self.anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_base64
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        )
        
        # Parse response
        try:
            result_json = json.loads(response.content[0].text)
            
            return AnalysisResult(
                model_name="claude-sonnet-4.5",
                confidence=result_json.get("confidence", 0.8),
                is_issue=result_json.get("is_issue", False),
                category=AnalysisCategory.VISUAL_BUG,
                description=", ".join(result_json.get("bugs_detected", [])),
                recommendations=result_json.get("recommendations", []),
                raw_response=result_json
            )
        except json.JSONDecodeError:
            return AnalysisResult(
                model_name="claude-sonnet-4.5",
                confidence=0.5,
                is_issue=False,
                category=AnalysisCategory.VISUAL_BUG,
                description=response.content[0].text[:500],
                recommendations=[]
            )
    
    def evaluate_consensus(
        self,
        results: List[AnalysisResult]
    ) -> Tuple[bool, float, List[str]]:
        """
        Evaluate consensus across models
        
        Issue flagged only if:
        - ≥2 models agree (is_issue=True)
        - Average confidence >0.85
        
        Returns: (issue_flagged, average_confidence, consensus_models)
        """
        issue_results = [r for r in results if r.is_issue]
        
        # Check: ≥2 models agree
        if len(issue_results) < 2:
            return (False, 0.0, [])
        
        # Calculate average confidence
        avg_confidence = sum(r.confidence for r in issue_results) / len(issue_results)
        
        # Check: average confidence >0.85
        if avg_confidence <= 0.85:
            return (False, avg_confidence, [r.model_name for r in issue_results])
        
        # Consensus reached!
        return (True, avg_confidence, [r.model_name for r in issue_results])


async def main():
    """Test the vision analysis agent"""
    agent = VisionAnalysisAgent()
    
    # Test with sample data
    screenshot_url = "https://example.com/test.png"
    telemetry_data = {
        "event_type": "OnPlayerDamage",
        "world_data": {"zone_name": "TheGoreforge"},
        "rendering_data": {"current_fps": 58}
    }
    
    results = await agent.analyze_capture(screenshot_url, telemetry_data)
    
    issue_flagged, confidence, models = agent.evaluate_consensus(results)
    
    print(f"Consensus: {issue_flagged}")
    print(f"Confidence: {confidence:.2f}")
    print(f"Models: {models}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())

