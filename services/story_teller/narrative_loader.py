"""
Narrative Loader - Loads world history from docs/narrative/ folder.
Loads files in order starting with 00-OVERVIEW.md.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class NarrativeLoader:
    """
    Loads and manages narrative content from docs/narrative/ folder.
    Loads files in numeric order starting with 00-OVERVIEW.md.
    """
    
    def __init__(self, narrative_dir: Optional[str] = None):
        """
        Initialize narrative loader.
        
        Args:
            narrative_dir: Path to narrative directory. Defaults to docs/narrative/
        """
        if narrative_dir is None:
            # Default to docs/narrative/ relative to project root
            project_root = Path(__file__).parent.parent.parent
            narrative_dir = project_root / "docs" / "narrative"
        
        self.narrative_dir = Path(narrative_dir)
        self.narratives: Dict[str, str] = {}
        self._load_narratives()
    
    def _load_narratives(self) -> None:
        """Load all narrative markdown files in order."""
        if not self.narrative_dir.exists():
            logger.warning(f"Narrative directory not found: {self.narrative_dir}")
            return
        
        # Find all markdown files
        md_files = sorted(self.narrative_dir.glob("*.md"))
        
        # Sort by filename (00-OVERVIEW.md comes first)
        md_files = sorted(md_files, key=lambda p: p.name)
        
        logger.info(f"Loading {len(md_files)} narrative files from {self.narrative_dir}")
        
        for md_file in md_files:
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Use filename without extension as key
                key = md_file.stem
                self.narratives[key] = content
                
                logger.info(f"Loaded narrative: {key} ({len(content)} chars)")
            except Exception as e:
                logger.error(f"Failed to load {md_file}: {e}")
    
    def get_all_narratives(self) -> Dict[str, str]:
        """Get all loaded narratives."""
        return self.narratives.copy()
    
    def get_narrative(self, key: str) -> Optional[str]:
        """
        Get a specific narrative by key (filename without extension).
        
        Args:
            key: Narrative key (e.g., "00-OVERVIEW", "01-DARK-WORLD-HISTORY")
        
        Returns:
            Narrative content or None if not found
        """
        return self.narratives.get(key)
    
    def get_narrative_summary(self) -> str:
        """
        Get a summary of all loaded narratives for context.
        
        Returns:
            Formatted summary string
        """
        if not self.narratives:
            return "No narratives loaded."
        
        summary = "Narrative Content Loaded:\n\n"
        for key, content in self.narratives.items():
            # Get first 200 chars as preview
            preview = content[:200].replace('\n', ' ')
            if len(content) > 200:
                preview += "..."
            
            summary += f"**{key}**: {len(content)} characters\n"
            summary += f"  Preview: {preview}\n\n"
        
        return summary
    
    def get_full_context(self) -> str:
        """
        Get full narrative context for story generation.
        
        Returns:
            Complete narrative content as formatted string
        """
        if not self.narratives:
            return "No narratives loaded."
        
        context = "=== WORLD HISTORY & NARRATIVE CONTEXT ===\n\n"
        
        # Add narratives in order
        for key in sorted(self.narratives.keys()):
            context += f"\n{'='*60}\n"
            context += f"# {key}\n"
            context += f"{'='*60}\n\n"
            context += self.narratives[key]
            context += "\n\n"
        
        return context
    
    def reload(self) -> None:
        """Reload narratives from disk."""
        self.narratives.clear()
        self._load_narratives()











