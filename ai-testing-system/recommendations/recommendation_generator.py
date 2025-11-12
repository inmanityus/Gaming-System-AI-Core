#!/usr/bin/env python3
"""
Structured Recommendation Generator
Generates safe, validated JSON recommendations (NOT direct code generation)
Part of AI-Driven Game Testing System (Tier 3)

Critical Design: Per Gemini 2.5 Pro's warning, AI-generated code is HIGH RISK
Solution: Structured JSON recommendations that humans can validate quickly
"""

import json
import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)


class RecommendationType(str, Enum):
    UASSET_MODIFICATION = "UASSET_MODIFICATION"  # Blueprint asset change
    CONFIG_CHANGE = "CONFIG_CHANGE"              # Configuration file update
    MATERIAL_ADJUSTMENT = "MATERIAL_ADJUSTMENT"  # Material/shader tweaks
    LIGHTING_CHANGE = "LIGHTING_CHANGE"          # Lighting adjustments
    POST_PROCESS_CHANGE = "POST_PROCESS_CHANGE"  # Post-process volume settings
    COMPONENT_PROPERTY = "COMPONENT_PROPERTY"    # Component property change
    ASSET_REPLACEMENT = "ASSET_REPLACEMENT"      # Replace with different asset


class Severity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class StructuredRecommendation:
    """
    Structured, safe recommendation that humans can validate
    
    Example:
    {
        "issueID": "UI-007",
        "confidence": 0.92,
        "severity": "high",
        "git_commit": "a4f8c1d",
        "test_case": "MainMenu_ResolutionSwitch",
        "category": "UX",
        "analysis": "The 'Quit Game' button is partially obscured by the 'Options' panel on a 21:9 aspect ratio.",
        "screenshot_path": "s3://...",
        "telemetry_path": "s3://...",
        "models_consensus": {
            "gemini_2.5_pro": {"agrees": true, "confidence": 0.95},
            "gpt_4o": {"agrees": true, "confidence": 0.89},
            "claude_sonnet_4.5": {"agrees": false, "confidence": 0.62}
        },
        "recommendation": {
            "type": "UASSET_MODIFICATION",
            "asset_path": "/Game/UI/WBP_MainMenu.WBP_MainMenu",
            "component": "Button_Quit",
            "property": "CanvasPanelSlot.Anchors",
            "current_value": "Min: (0.5, 0.8), Max: (0.6, 0.9)",
            "suggested_value": "Min: (0.8, 0.9), Max: (0.9, 0.95)",
            "rationale": "Moving anchor to bottom-right ensures correct scaling with aspect ratio",
            "alternative_approaches": [...]
        }
    }
    """
    issue_id: str
    confidence: float  # 0.0-1.0
    severity: Severity
    git_commit: str
    test_case: str
    category: str
    analysis: str
    screenshot_path: str
    telemetry_path: str
    models_consensus: Dict[str, Dict]
    recommendation: Dict
    created_at: str
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


class RecommendationGenerator:
    """
    Generates structured, safe recommendations from vision analysis
    
    Benefits over direct code generation:
    - Human can validate quickly (< 30 seconds review time)
    - No risk of logic flaws, race conditions, security issues
    - Clear rationale and alternatives provided
    - Can pre-populate Jira tickets automatically
    - Provides confidence metrics for prioritization
    """
    
    def __init__(self):
        self.recommendations_db = []
        logger.info("Recommendation Generator initialized")
    
    def generate_recommendation(
        self,
        capture_id: str,
        consensus_result: Dict,
        analysis_results: List[Dict],
        git_commit: str,
        test_case: str
    ) -> StructuredRecommendation:
        """
        Generate structured recommendation from consensus result
        """
        # Determine severity based on category and confidence
        severity = self._determine_severity(
            consensus_result["category"],
            consensus_result["average_confidence"]
        )
        
        # Build models consensus dict
        models_consensus = {}
        for result in analysis_results:
            models_consensus[result["model_name"]] = {
                "agrees": result["is_issue"],
                "confidence": result["confidence"]
            }
        
        # Generate specific recommendation based on category
        recommendation_details = self._generate_recommendation_details(
            consensus_result,
            analysis_results
        )
        
        # Create structured recommendation
        recommendation = StructuredRecommendation(
            issue_id=f"{consensus_result['category'].upper()}-{str(uuid.uuid4())[:8]}",
            confidence=consensus_result["average_confidence"],
            severity=severity,
            git_commit=git_commit,
            test_case=test_case,
            category=consensus_result["category"],
            analysis=consensus_result["description"],
            screenshot_path=f"s3://captures/{capture_id}.png",  # Placeholder
            telemetry_path=f"s3://captures/{capture_id}.json",  # Placeholder
            models_consensus=models_consensus,
            recommendation=recommendation_details,
            created_at=datetime.utcnow().isoformat()
        )
        
        # Store recommendation
        self.recommendations_db.append(recommendation)
        
        logger.info(f"Generated recommendation: {recommendation.issue_id} ({severity.value})")
        
        return recommendation
    
    def _determine_severity(self, category: str, confidence: float) -> Severity:
        """Determine severity based on category and confidence"""
        if category == "visual_bug" and confidence > 0.95:
            return Severity.CRITICAL
        elif category == "visual_bug":
            return Severity.HIGH
        elif category == "ux" and confidence > 0.92:
            return Severity.HIGH
        elif category == "ux":
            return Severity.MEDIUM
        elif category == "atmosphere":
            return Severity.MEDIUM
        else:
            return Severity.LOW
    
    def _generate_recommendation_details(
        self,
        consensus_result: Dict,
        analysis_results: List[Dict]
    ) -> Dict:
        """
        Generate specific recommendation based on issue category
        
        Returns structured dict with:
        - type: Recommendation type (enum)
        - asset_path: Path to asset to modify
        - component/property: Specific property to change
        - current_value: Current value (if known)
        - suggested_value: Suggested new value
        - rationale: Why this change will fix the issue
        - alternative_approaches: Other ways to solve the problem
        """
        category = consensus_result["category"]
        description = consensus_result["description"]
        recommendations_list = consensus_result.get("recommendations", [])
        
        # Parse recommendations from vision models
        # and structure them into actionable format
        
        if category == "atmosphere":
            return self._generate_atmosphere_recommendation(
                description,
                recommendations_list
            )
        elif category == "ux":
            return self._generate_ux_recommendation(
                description,
                recommendations_list
            )
        elif category == "visual_bug":
            return self._generate_bug_recommendation(
                description,
                recommendations_list
            )
        else:
            return {
                "type": "CONFIG_CHANGE",
                "details": description,
                "recommendations": recommendations_list
            }
    
    def _generate_atmosphere_recommendation(
        self,
        description: str,
        recommendations: List[str]
    ) -> Dict:
        """Generate recommendation for atmosphere issues"""
        # Example: Flat lighting detected
        if "flat" in description.lower() or "lighting" in description.lower():
            return {
                "type": RecommendationType.LIGHTING_CHANGE.value,
                "asset_path": "/Game/Maps/TheGoreforge/Lighting",
                "changes": [
                    {
                        "component": "DirectionalLight_Main",
                        "property": "Intensity",
                        "current_value": "1.0",
                        "suggested_value": "0.3-0.5",
                        "rationale": "Reduce overall light intensity to create more dramatic shadows"
                    },
                    {
                        "component": "PointLights_Additional",
                        "property": "Add focused highlights",
                        "suggested_value": "3-5 point lights with falloff",
                        "rationale": "Create chiaroscuro effect with focused light sources"
                    }
                ],
                "alternative_approaches": [
                    "Add post-process volume with exposure compensation",
                    "Use IES light profiles for more realistic falloff",
                    "Implement dynamic shadows with higher resolution"
                ],
                "rationale": "Horror atmosphere requires high contrast lighting with deep shadows and focused highlights"
            }
        
        # Example: Color palette too saturated
        elif "color" in description.lower() or "saturated" in description.lower():
            return {
                "type": RecommendationType.POST_PROCESS_CHANGE.value,
                "asset_path": "/Game/Maps/TheGoreforge/PostProcess/PPV_Goreforge",
                "property": "Color Grading",
                "changes": [
                    {
                        "setting": "Saturation",
                        "current_value": "1.0",
                        "suggested_value": "0.3-0.5",
                        "rationale": "Desaturate colors for horror aesthetic"
                    },
                    {
                        "setting": "Contrast",
                        "current_value": "1.0",
                        "suggested_value": "1.3-1.5",
                        "rationale": "Increase contrast for dramatic effect"
                    }
                ],
                "alternative_approaches": [
                    "Create custom LUT (Lookup Table) with horror color grading",
                    "Adjust material base colors to be less saturated",
                    "Use color temperature shift toward cold tones"
                ],
                "rationale": "Horror games require desaturated, muted color palettes with symbolic color accents"
            }
        
        else:
            return {
                "type": "POST_PROCESS_CHANGE",
                "details": description,
                "recommendations": recommendations
            }
    
    def _generate_ux_recommendation(
        self,
        description: str,
        recommendations: List[str]
    ) -> Dict:
        """Generate recommendation for UX issues"""
        # Example: UI readability issue
        if "contrast" in description.lower() or "readability" in description.lower():
            return {
                "type": RecommendationType.UASSET_MODIFICATION.value,
                "asset_path": "/Game/UI/WBP_HUD.WBP_HUD",
                "component": "Text_Objective",
                "changes": [
                    {
                        "property": "Color and Opacity",
                        "current_value": "RGB(200, 200, 200)",
                        "suggested_value": "RGB(255, 255, 255) with shadow/outline",
                        "rationale": "Improve contrast to meet WCAG AA standards"
                    },
                    {
                        "property": "Font Size",
                        "current_value": "14",
                        "suggested_value": "18-20",
                        "rationale": "Increase size for comfortable reading distance"
                    }
                ],
                "alternative_approaches": [
                    "Add background panel with semi-transparent dark background",
                    "Use stroke/outline on text for better visibility",
                    "Implement dynamic contrast adjustment based on background"
                ],
                "rationale": "UI text must meet WCAG contrast ratios for accessibility and readability"
            }
        
        else:
            return {
                "type": "UASSET_MODIFICATION",
                "details": description,
                "recommendations": recommendations
            }
    
    def _generate_bug_recommendation(
        self,
        description: str,
        recommendations: List[str]
    ) -> Dict:
        """Generate recommendation for visual bugs"""
        # Example: Clipping detected
        if "clipping" in description.lower():
            return {
                "type": RecommendationType.COMPONENT_PROPERTY.value,
                "component": "Character Collision",
                "changes": [
                    {
                        "property": "Collision Presets",
                        "suggested_value": "BlockAll",
                        "rationale": "Ensure proper collision to prevent clipping through geometry"
                    },
                    {
                        "property": "Capsule Component Size",
                        "suggested_action": "Increase radius by 10-20%",
                        "rationale": "Larger collision capsule prevents intersection"
                    }
                ],
                "alternative_approaches": [
                    "Implement push-back system when collision detected",
                    "Adjust level geometry to have thicker walls",
                    "Use physics constraints to prevent interpenetration"
                ],
                "rationale": "Clipping breaks immersion and is a critical visual bug"
            }
        
        else:
            return {
                "type": "COMPONENT_PROPERTY",
                "details": description,
                "recommendations": recommendations
            }
    
    def get_recommendations(
        self,
        severity_filter: Optional[Severity] = None,
        category_filter: Optional[str] = None
    ) -> List[StructuredRecommendation]:
        """Get recommendations with optional filters"""
        filtered = self.recommendations_db
        
        if severity_filter:
            filtered = [r for r in filtered if r.severity == severity_filter]
        
        if category_filter:
            filtered = [r for r in filtered if r.category == category_filter]
        
        # Sort by severity (Critical > High > Medium > Low) and confidence
        severity_order = {
            Severity.CRITICAL: 0,
            Severity.HIGH: 1,
            Severity.MEDIUM: 2,
            Severity.LOW: 3
        }
        
        filtered.sort(
            key=lambda r: (severity_order[r.severity], -r.confidence)
        )
        
        return filtered


# Example usage
if __name__ == "__main__":
    generator = RecommendationGenerator()
    
    # Example consensus result
    consensus = {
        "capture_id": "test_001",
        "category": "atmosphere",
        "description": "Flat lighting detected - mid-tone clustering in luminance histogram",
        "average_confidence": 0.92,
        "recommendations": [
            "Reduce directional light intensity",
            "Add focused point lights",
            "Increase contrast"
        ]
    }
    
    analysis_results = [
        {"model_name": "gemini-2.5-pro", "is_issue": True, "confidence": 0.95},
        {"model_name": "gpt-4o", "is_issue": True, "confidence": 0.89}
    ]
    
    recommendation = generator.generate_recommendation(
        capture_id="test_001",
        consensus_result=consensus,
        analysis_results=analysis_results,
        git_commit="abc123",
        test_case="Goreforge_Lighting"
    )
    
    print(recommendation.to_json())

