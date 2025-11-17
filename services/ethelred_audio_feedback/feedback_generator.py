"""
Audio feedback generator that produces recommendations for voice improvement.
Implements TAUD-10 (R-AUD-OUT-003).
"""
import logging
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
import numpy as np

logger = logging.getLogger(__name__)


class FeedbackGenerator:
    """
    Generates structured feedback recommendations based on audio metrics and reports.
    Does NOT auto-tune - only provides recommendations for manual adjustment.
    """
    
    def __init__(self):
        # Target ranges for different voice characteristics
        self.target_ranges = {
            'vampire_alpha': {
                'f0_range': (80, 150),
                'roughness': (0.3, 0.6),
                'breathiness': (0.1, 0.3),
                'spectral_tilt': (-8, -6)
            },
            'human_agent': {
                'f0_range': (100, 200),
                'roughness': (0.0, 0.2),
                'breathiness': (0.0, 0.1),
                'spectral_tilt': (-6, -4)
            },
            'corpse_tender': {
                'f0_range': (150, 300),
                'roughness': (0.2, 0.4),
                'breathiness': (0.3, 0.5),
                'spectral_tilt': (-5, -3)
            }
        }
        
        # Feedback templates
        self.feedback_templates = {
            'roughness_low': "Increase glottal roughness parameter by 10-15% for more gravelly texture",
            'roughness_high': "Reduce glottal roughness to avoid excessive harshness",
            'breathiness_low': "Add subtle breathiness (5-10%) for more organic quality",
            'breathiness_high': "Reduce breathiness to improve voice clarity",
            'f0_low': "Raise base pitch by 10-20 Hz to match archetype range",
            'f0_high': "Lower base pitch to achieve deeper tone",
            'spectral_dark': "Brighten spectral tilt by reducing low-frequency emphasis",
            'spectral_bright': "Darken tone by enhancing low frequencies",
            'monotone': "Increase pitch variation range (F0 modulation) by 20-30%",
            'robotic': "Add micro-variations to timing and pitch for naturalness",
            'unstable': "Check vocal fold parameters for extreme values causing instability",
            'misaligned': "Review archetype voice profile settings - significant deviation detected"
        }
    
    def generate_archetype_feedback(
        self,
        archetype_id: str,
        report_data: Dict[str, Any],
        detailed_metrics: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate feedback for a specific archetype based on report data.
        """
        feedback = {
            'build_id': report_data.get('build_id'),
            'archetype_id': archetype_id,
            'findings': [],
            'candidate_training_examples': [],
            'notes': ""
        }
        
        # Check if we have target ranges for this archetype
        if archetype_id not in self.target_ranges:
            feedback['notes'] = f"No target profile defined for archetype {archetype_id}"
            return feedback
        
        targets = self.target_ranges[archetype_id]
        
        # Analyze each dimension
        findings = []
        
        # 1. Analyze archetype conformity
        if 'archetype_conformity' in report_data.get('summary', {}):
            conformity_data = report_data['summary']['archetype_conformity']
            mean_score = conformity_data.get('mean', 0)
            
            if mean_score < 0.6:
                findings.append({
                    'dimension': 'overall_conformity',
                    'observed_mean': mean_score,
                    'target_range': [0.75, 0.85],
                    'recommendation': self.feedback_templates['misaligned']
                })
            
            # Check band distribution
            bands = conformity_data.get('band_distribution', {})
            if bands.get('too_clean', 0) > 0.3:
                findings.append({
                    'dimension': 'voice_texture',
                    'observed_mean': 1 - bands['too_clean'],
                    'target_range': [0.8, 1.0],
                    'recommendation': "Voice lacks character depth - increase texture parameters"
                })
        
        # 2. Analyze naturalness issues
        if 'naturalness' in report_data.get('summary', {}):
            naturalness_data = report_data['summary']['naturalness']
            bands = naturalness_data.get('band_distribution', {})
            
            if bands.get('monotone', 0) > 0.2:
                findings.append({
                    'dimension': 'pitch_variation',
                    'observed_mean': 1 - bands['monotone'],
                    'target_range': [0.8, 1.0],
                    'recommendation': self.feedback_templates['monotone']
                })
            
            if bands.get('robotic', 0) > 0.3:
                findings.append({
                    'dimension': 'prosody',
                    'observed_mean': 1 - bands['robotic'],
                    'target_range': [0.7, 1.0],
                    'recommendation': self.feedback_templates['robotic']
                })
        
        # 3. Analyze simulator stability
        if 'simulator_stability' in report_data.get('summary', {}):
            stability_data = report_data['summary']['simulator_stability']
            mean_score = stability_data.get('mean', 0)
            
            if mean_score < 0.8:
                findings.append({
                    'dimension': 'simulator_stability',
                    'observed_mean': mean_score,
                    'target_range': [0.9, 1.0],
                    'recommendation': self.feedback_templates['unstable']
                })
        
        # 4. Analyze detailed metrics if available
        if detailed_metrics:
            findings.extend(self._analyze_detailed_metrics(archetype_id, detailed_metrics))
        
        # 5. Identify training examples from poor segments
        training_examples = self._identify_training_examples(report_data)
        
        # Compile feedback
        feedback['findings'] = findings
        feedback['candidate_training_examples'] = training_examples
        
        # Generate notes based on severity
        if len(findings) >= 3:
            feedback['notes'] = "Multiple issues detected. Prioritize overall conformity before fine-tuning individual parameters."
        elif any(f['observed_mean'] < 0.5 for f in findings):
            feedback['notes'] = "Significant deviations detected. Review base archetype configuration."
        else:
            feedback['notes'] = "Minor adjustments recommended for optimal quality."
        
        # Add simulator-specific feedback if needed
        if archetype_id in ['vampire_alpha', 'corpse_tender']:
            feedback['simulator_profile_id'] = f"{archetype_id}_v1"
        
        return feedback
    
    def _analyze_detailed_metrics(
        self,
        archetype_id: str,
        detailed_metrics: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Analyze detailed voice characteristic metrics."""
        findings = []
        targets = self.target_ranges[archetype_id]
        
        # Check F0 range
        if 'mean_f0' in detailed_metrics:
            mean_f0 = detailed_metrics['mean_f0']
            target_f0 = targets['f0_range']
            
            if mean_f0 < target_f0[0]:
                findings.append({
                    'dimension': 'fundamental_frequency',
                    'observed_mean': mean_f0,
                    'target_range': list(target_f0),
                    'recommendation': self.feedback_templates['f0_low']
                })
            elif mean_f0 > target_f0[1]:
                findings.append({
                    'dimension': 'fundamental_frequency',
                    'observed_mean': mean_f0,
                    'target_range': list(target_f0),
                    'recommendation': self.feedback_templates['f0_high']
                })
        
        # Check roughness
        if 'roughness' in detailed_metrics:
            roughness = detailed_metrics['roughness']
            target_rough = targets['roughness']
            
            if roughness < target_rough[0]:
                findings.append({
                    'dimension': 'roughness',
                    'observed_mean': roughness,
                    'target_range': list(target_rough),
                    'recommendation': self.feedback_templates['roughness_low']
                })
            elif roughness > target_rough[1]:
                findings.append({
                    'dimension': 'roughness',
                    'observed_mean': roughness,
                    'target_range': list(target_rough),
                    'recommendation': self.feedback_templates['roughness_high']
                })
        
        # Check breathiness
        if 'breathiness' in detailed_metrics:
            breathiness = detailed_metrics['breathiness']
            target_breath = targets['breathiness']
            
            if breathiness < target_breath[0]:
                findings.append({
                    'dimension': 'breathiness',
                    'observed_mean': breathiness,
                    'target_range': list(target_breath),
                    'recommendation': self.feedback_templates['breathiness_low']
                })
            elif breathiness > target_breath[1]:
                findings.append({
                    'dimension': 'breathiness',
                    'observed_mean': breathiness,
                    'target_range': list(target_breath),
                    'recommendation': self.feedback_templates['breathiness_high']
                })
        
        # Check spectral tilt
        if 'spectral_tilt' in detailed_metrics:
            tilt = detailed_metrics['spectral_tilt']
            target_tilt = targets['spectral_tilt']
            
            if tilt < target_tilt[0]:
                findings.append({
                    'dimension': 'spectral_tilt',
                    'observed_mean': tilt,
                    'target_range': list(target_tilt),
                    'recommendation': self.feedback_templates['spectral_dark']
                })
            elif tilt > target_tilt[1]:
                findings.append({
                    'dimension': 'spectral_tilt',
                    'observed_mean': tilt,
                    'target_range': list(target_tilt),
                    'recommendation': self.feedback_templates['spectral_bright']
                })
        
        return findings
    
    def _identify_training_examples(
        self,
        report_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Identify segments that could be used as training examples."""
        examples = []
        
        # Look for common deviations
        deviations = report_data.get('common_deviations', [])
        
        # Scene analysis can help identify problematic segments
        scene_analysis = report_data.get('scene_analysis', {})
        
        for scene_id, metrics in scene_analysis.items():
            # Find scenes with consistently poor scores
            poor_metrics = []
            
            if metrics.get('naturalness_avg', 1) < 0.6:
                poor_metrics.append('unnatural')
            
            if metrics.get('archetype_conformity_avg', 1) < 0.6:
                poor_metrics.append('off_archetype')
            
            if metrics.get('intelligibility_avg', 1) < 0.7:
                poor_metrics.append('unclear')
            
            if poor_metrics:
                # This scene has issues - suggest as training example
                examples.append({
                    'segment_id': f"scene_{scene_id}_sample",  # Would be real segment ID
                    'media_uri': f"redalert://media/audio/{report_data['build_id']}/scene_{scene_id}.ogg",
                    'labels': poor_metrics
                })
                
                # Limit to 5 examples
                if len(examples) >= 5:
                    break
        
        return examples
    
    def generate_simulator_feedback(
        self,
        simulator_profile_id: str,
        aggregated_stability_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate feedback specific to simulator configuration.
        """
        feedback = {
            'simulator_profile_id': simulator_profile_id,
            'findings': [],
            'recommendations': []
        }
        
        # Analyze stability patterns
        if aggregated_stability_data.get('mean_stability', 1) < 0.8:
            # Identify common instability causes
            instability_types = aggregated_stability_data.get('instability_types', {})
            
            if instability_types.get('glitches', 0) > 0.1:
                feedback['findings'].append({
                    'issue': 'glitch_detection',
                    'frequency': instability_types['glitches'],
                    'severity': 'high'
                })
                feedback['recommendations'].append(
                    "Review glottal pulse generation for discontinuities"
                )
            
            if instability_types.get('parameter_jumps', 0) > 0.05:
                feedback['findings'].append({
                    'issue': 'parameter_instability',
                    'frequency': instability_types['parameter_jumps'],
                    'severity': 'medium'
                })
                feedback['recommendations'].append(
                    "Smooth parameter transitions with interpolation"
                )
            
            if instability_types.get('clipping', 0) > 0.01:
                feedback['findings'].append({
                    'issue': 'amplitude_clipping',
                    'frequency': instability_types['clipping'],
                    'severity': 'high'
                })
                feedback['recommendations'].append(
                    "Reduce gain or implement limiter in signal chain"
                )
        
        # Check for systematic issues
        if aggregated_stability_data.get('scene_correlation', 0) > 0.7:
            feedback['recommendations'].append(
                "Instability correlates with specific scenes - check scene-specific parameters"
            )
        
        return feedback
    
    def prioritize_feedback(
        self,
        all_feedback: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Prioritize feedback items by severity and impact.
        """
        # Sort by number of affected segments and severity
        for feedback in all_feedback:
            severity_score = 0
            
            for finding in feedback.get('findings', []):
                # Score based on deviation from target
                if 'observed_mean' in finding and 'target_range' in finding:
                    target_mid = np.mean(finding['target_range'])
                    deviation = abs(finding['observed_mean'] - target_mid) / target_mid
                    severity_score += deviation
            
            feedback['priority_score'] = severity_score
        
        # Sort by priority
        return sorted(all_feedback, key=lambda x: x.get('priority_score', 0), reverse=True)

