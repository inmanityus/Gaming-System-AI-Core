#!/usr/bin/env python3
"""
Golden Master Screenshot Comparison System
Protects visual perfection - prevents quality degradation
Priority #1 for "Most Realistic Game Ever"
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import imagehash
from PIL import Image
import io
import numpy as np
from sklearn metrics.pairwise import cosine_similarity
import cv2

logger = logging.getLogger(__name__)

@dataclass
class GoldenMaster:
    """Reference screenshot representing perfection"""
    scene_id: str
    screenshot_path: str
    perceptual_hash: str
    approved_by: str  # Which AI model(s) approved this
    approved_at: str
    metadata: Dict
    quality_metrics: Dict  # Histogram, contrast, etc.

class GoldenMasterSystem:
    """
    Golden Master Screenshot Comparison
    
    Purpose: Protect visual perfection once achieved
    Method: Compare new screenshots against approved "golden" versions
    Alert: Any degradation detected immediately
    
    For The Body Broker:
    - 50+ scenes each have golden master
    - Every build compares against golden
    - Any regression (>5% difference) triggers alert
    - Prevents accidental quality loss
    """
    
    def __init__(self, golden_masters_dir: str = "golden-masters/"):
        self.golden_masters_dir = Path(golden_masters_dir)
        self.golden_masters_dir.mkdir(parents=True, exist_ok=True)
        self.golden_masters: Dict[str, GoldenMaster] = {}
        self.load_golden_masters()
        
        logger.info(f"Golden Master System initialized with {len(self.golden_masters)} masters")
    
    def load_golden_masters(self):
        """Load all approved golden master screenshots"""
        manifest_file = self.golden_masters_dir / "manifest.json"
        
        if manifest_file.exists():
            with open(manifest_file, 'r') as f:
                data = json.load(f)
            
            for entry in data['golden_masters']:
                gm = GoldenMaster(**entry)
                self.golden_masters[gm.scene_id] = gm
                
            logger.info(f"Loaded {len(self.golden_masters)} golden masters")
    
    def approve_as_golden_master(
        self,
        scene_id: str,
        screenshot_path: str,
        approved_by: List[str],
        metadata: Dict
    ) -> GoldenMaster:
        """
        Approve screenshot as golden master (perfect reference)
        
        Requires: 3+ AI models must approve
        Process: Vision models analyze, consensus reached, approved
        Result: This screenshot becomes the quality baseline
        """
        if len(approved_by) < 3:
            raise ValueError(f"Minimum 3 AI models must approve golden master (got {len(approved_by)})")
        
        # Load image
        image = Image.open(screenshot_path)
        
        # Compute perceptual hash
        phash = str(imagehash.phash(image, hash_size=16))
        
        # Extract quality metrics
        quality_metrics = self._extract_quality_metrics(image)
        
        # Create golden master
        gm = GoldenMaster(
            scene_id=scene_id,
            screenshot_path=str(screenshot_path),
            perceptual_hash=phash,
            approved_by=", ".join(approved_by),
            approved_at=datetime.utcnow().isoformat(),
            metadata=metadata,
            quality_metrics=quality_metrics
        )
        
        # Copy to golden masters directory
        golden_path = self.golden_masters_dir / f"{scene_id}_golden.png"
        image.save(golden_path)
        
        # Store
        self.golden_masters[scene_id] = gm
        self._save_manifest()
        
        logger.info(f"Approved golden master: {scene_id} (by {len(approved_by)} models)")
        return gm
    
    def compare_against_golden(
        self,
        scene_id: str,
        new_screenshot_path: str
    ) -> Dict:
        """
        Compare new screenshot against golden master
        
        Returns:
        - difference_percentage: 0-100 (0 = identical, 100 = completely different)
        - passed: bool (difference within acceptable threshold)
        - details: breakdown of differences
        - recommendation: what to do
        """
        if scene_id not in self.golden_masters:
            return {
                "status": "no_golden_master",
                "message": f"No golden master exists for scene '{scene_id}'",
                "recommendation": "Approve this screenshot as golden master if quality is perfect"
            }
        
        golden = self.golden_masters[scene_id]
        
        # Load images
        golden_img = Image.open(golden.screenshot_path)
        new_img = Image.open(new_screenshot_path)
        
        # Compute perceptual difference
        perceptual_diff = self._perceptual_difference(golden_img, new_img)
        
        # Compute quality metrics difference
        golden_metrics = golden.quality_metrics
        new_metrics = self._extract_quality_metrics(new_img)
        metrics_diff = self._compare_metrics(golden_metrics, new_metrics)
        
        # Determine if passed
        threshold = 5.0  # 5% difference allowed
        passed = perceptual_diff < threshold
        
        # Classification
        if perceptual_diff < 2.0:
            classification = "IDENTICAL"
            recommendation = "✅ Perfect - matches golden master"
        elif perceptual_diff < 5.0:
            classification = "ACCEPTABLE"
            recommendation = "✅ Minor differences - within tolerance"
        elif perceptual_diff < 15.0:
            classification = "WARNING"
            recommendation = "⚠️ Noticeable degradation - investigate changes"
        else:
            classification = "FAILED"
            recommendation = "❌ VISUAL REGRESSION - quality degraded significantly"
        
        result = {
            "status": "compared",
            "scene_id": scene_id,
            "passed": passed,
            "classification": classification,
            "difference_percentage": round(perceptual_diff, 2),
            "threshold": threshold,
            "perceptual_hash_distance": self._hamming_distance(
                golden.perceptual_hash,
                str(imagehash.phash(new_img, hash_size=16))
            ),
            "quality_metrics_diff": metrics_diff,
            "golden_master": {
                "approved_by": golden.approved_by,
                "approved_at": golden.approved_at
            },
            "recommendation": recommendation
        }
        
        # Log if failed
        if not passed:
            logger.warning(f"Golden Master FAILED: {scene_id} - {perceptual_diff:.1f}% difference")
            logger.warning(f"  Recommendation: {recommendation}")
        else:
            logger.info(f"Golden Master PASSED: {scene_id} - {perceptual_diff:.1f}% difference")
        
        return result
    
    def _perceptual_difference(self, img1: Image.Image, img2: Image.Image) -> float:
        """
        Calculate perceptual difference between images (0-100%)
        
        Uses multiple algorithms:
        - Perceptual hash (pHash) distance
        - Structural similarity (SSIM)
        - Histogram comparison
        
        Returns weighted average as percentage
        """
        # Ensure same size
        if img1.size != img2.size:
            img2 = img2.resize(img1.size, Image.LANCZOS)
        
        # pHash distance
        hash1 = imagehash.phash(img1, hash_size=16)
        hash2 = imagehash.phash(img2, hash_size=16)
        hash_diff = (hash1 - hash2) / 256.0 * 100  # Normalize to 0-100%
        
        # Convert to numpy for OpenCV
        img1_cv = cv2.cvtColor(np.array(img1), cv2.COLOR_RGB2BGR)
        img2_cv = cv2.cvtColor(np.array(img2), cv2.COLOR_RGB2BGR)
        img1_gray = cv2.cvtColor(img1_cv, cv2.COLOR_BGR2GRAY)
        img2_gray = cv2.cvtColor(img2_cv, cv2.COLOR_BGR2GRAY)
        
        # SSIM (Structural Similarity Index)
        from skimage.metrics import structural_similarity as ssim
        ssim_score = ssim(img1_gray, img2_gray)
        ssim_diff = (1 - ssim_score) * 100  # Convert to difference percentage
        
        # Histogram comparison
        hist1 = cv2.calcHist([img1_cv], [0, 1, 2], None, [256, 256, 256], [0, 256, 0, 256, 0, 256])
        hist2 = cv2.calcHist([img2_cv], [0, 1, 2], None, [256, 256, 256], [0, 256, 0, 256, 0, 256])
        hist1 = cv2.normalize(hist1, hist1).flatten()
        hist2 = cv2.normalize(hist2, hist2).flatten()
        hist_corr = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
        hist_diff = (1 - hist_corr) * 100
        
        # Weighted average (SSIM most important for visual perception)
        weighted_diff = (ssim_diff * 0.6) + (hash_diff * 0.3) + (hist_diff * 0.1)
        
        return weighted_diff
    
    def _extract_quality_metrics(self, image: Image.Image) -> Dict:
        """Extract quality metrics for comparison"""
        img_cv = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        img_gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
        
        # Luminance histogram
        hist = cv2.calcHist([img_gray], [0], None, [256], [0, 256])
        hist = hist.flatten()
        
        # Contrast
        contrast = img_gray.std()
        
        # Brightness
        brightness = img_gray.mean()
        
        # Edge density (sharpness proxy)
        edges = cv2.Canny(img_gray, 100, 200)
        edge_density = np.sum(edges > 0) / edges.size
        
        return {
            "luminance_histogram": hist.tolist(),
            "contrast": float(contrast),
            "brightness": float(brightness),
            "edge_density": float(edge_density),
            "mean_rgb": [float(x) for x in np.array(image).mean(axis=(0, 1))]
        }
    
    def _compare_metrics(self, metrics1: Dict, metrics2: Dict) -> Dict:
        """Compare quality metrics between golden and new"""
        return {
            "contrast_delta": metrics2["contrast"] - metrics1["contrast"],
            "brightness_delta": metrics2["brightness"] - metrics1["brightness"],
            "edge_density_delta": metrics2["edge_density"] - metrics1["edge_density"],
            "contrast_change_pct": (metrics2["contrast"] / metrics1["contrast"] - 1) * 100 if metrics1["contrast"] > 0 else 0
        }
    
    def _hamming_distance(self, hash1: str, hash2: str) -> int:
        """Hamming distance between hashes"""
        return sum(c1 != c2 for c1, c2 in zip(hash1, hash2))
    
    def _save_manifest(self):
        """Save golden masters manifest"""
        manifest = {
            "version": "1.0.0",
            "updated_at": datetime.utcnow().isoformat(),
            "golden_masters": [
                {
                    "scene_id": gm.scene_id,
                    "screenshot_path": gm.screenshot_path,
                    "perceptual_hash": gm.perceptual_hash,
                    "approved_by": gm.approved_by,
                    "approved_at": gm.approved_at,
                    "metadata": gm.metadata,
                    "quality_metrics": gm.quality_metrics
                }
                for gm in self.golden_masters.values()
            ]
        }
        
        manifest_file = self.golden_masters_dir / "manifest.json"
        with open(manifest_file, 'w') as f:
            json.dump(manifest, f, indent=2)

# Example usage
if __name__ == "__main__":
    system = GoldenMasterSystem()
    print(f"Managing {len(system.golden_masters)} golden masters")

