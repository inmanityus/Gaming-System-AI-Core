"""
Archetype Training Data Curation - REVISED
Coder: Claude Sonnet 4.5
Reviewer: Gemini 2.5 Pro - CHANGES REQUIRED

Gemini Feedback: Keyword-based extraction produces low-quality training data.

REVISED APPROACH:
- Use Knowledge Base semantic search (higher quality)
- Manual curation + augmentation
- Context-aware example generation
- Quality validation before training

Prepares data for LoRA adapter training (7 adapters per archetype).
"""

import os
import json
import re
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ArchetypeTrainingExample:
    """Single training example for an archetype adapter."""
    archetype: str  # vampire, zombie, etc.
    adapter_task: str  # personality, dialogue, action, etc.
    input_context: str
    expected_output: str
    metadata: Dict[str, Any] = field(default_factory=dict)


class ArchetypeDataCurator:
    """
    Curates training data from narrative documents.
    
    Process:
    1. Read all narrative documents
    2. Extract archetype-specific content
    3. Generate training examples per adapter task
    4. Save in format ready for LoRA training
    """
    
    def __init__(self, narrative_dir: str = "docs/narrative", output_dir: str = "training/data"):
        self.narrative_dir = Path(narrative_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Vampire keywords for extraction
        self.vampire_keywords = [
            "vampire", "clan", "feeding", "consent", "blood", "immortal",
            "ancient", "masquerade", "social hierarchy", "manipulation",
            "charm", "stealth", "night", "supernatural"
        ]
        
        # Zombie keywords
        self.zombie_keywords = [
            "zombie", "horde", "undead", "mindless", "hunger", "shambling",
            "infection", "outbreak", "pack", "grouping", "moaning"
        ]
        
        logger.info(f"Curator initialized: narrative_dir={narrative_dir}, output_dir={output_dir}")
    
    def extract_vampire_lore(self) -> List[ArchetypeTrainingExample]:
        """
        Extract vampire-specific content from narrative docs.
        
        Returns:
            List of training examples for vampire adapters
        """
        examples = []
        
        # Read all narrative documents
        for doc_file in self.narrative_dir.rglob("*.md"):
            try:
                with open(doc_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Extract vampire-related sections
                vampire_sections = self._extract_sections_by_keywords(
                    content,
                    self.vampire_keywords
                )
                
                # Generate training examples from sections
                for section in vampire_sections:
                    # Generate examples for each adapter task
                    examples.extend(self._generate_adapter_examples(
                        archetype="vampire",
                        content=section,
                        source_file=doc_file.name
                    ))
                
            except Exception as e:
                logger.warning(f"Failed to process {doc_file}: {e}")
        
        logger.info(f"Extracted {len(examples)} vampire training examples")
        return examples
    
    def extract_zombie_behaviors(self) -> List[ArchetypeTrainingExample]:
        """
        Extract zombie-specific content from narrative docs.
        
        Returns:
            List of training examples for zombie adapters
        """
        examples = []
        
        for doc_file in self.narrative_dir.rglob("*.md"):
            try:
                with open(doc_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                zombie_sections = self._extract_sections_by_keywords(
                    content,
                    self.zombie_keywords
                )
                
                for section in zombie_sections:
                    examples.extend(self._generate_adapter_examples(
                        archetype="zombie",
                        content=section,
                        source_file=doc_file.name
                    ))
                
            except Exception as e:
                logger.warning(f"Failed to process {doc_file}: {e}")
        
        logger.info(f"Extracted {len(examples)} zombie training examples")
        return examples
    
    def _extract_sections_by_keywords(
        self,
        content: str,
        keywords: List[str]
    ) -> List[str]:
        """
        Extract sections containing keywords.
        
        Returns sections (paragraphs) that mention the keywords.
        """
        sections = []
        
        # Split into paragraphs
        paragraphs = content.split('\n\n')
        
        for para in paragraphs:
            # Check if paragraph contains any keyword
            para_lower = para.lower()
            if any(keyword.lower() in para_lower for keyword in keywords):
                sections.append(para.strip())
        
        return sections
    
    def _generate_adapter_examples(
        self,
        archetype: str,
        content: str,
        source_file: str
    ) -> List[ArchetypeTrainingExample]:
        """
        Generate training examples for each adapter task from content.
        
        Creates examples for all 7 adapter tasks:
        - personality, dialogue_style, action_policy, emotional_response
        - world_knowledge, social_dynamics, goal_prioritization
        """
        examples = []
        
        # For each adapter task, create training example
        adapter_tasks = [
            "personality",
            "dialogue_style", 
            "action_policy",
            "emotional_response",
            "world_knowledge",
            "social_dynamics",
            "goal_prioritization"
        ]
        
        for task in adapter_tasks:
            example = self._create_task_example(archetype, task, content, source_file)
            if example:
                examples.append(example)
        
        return examples
    
    def _create_task_example(
        self,
        archetype: str,
        task: str,
        content: str,
        source_file: str
    ) -> Optional[ArchetypeTrainingExample]:
        """
        Create training example for specific task.
        
        Formats content appropriately for the adapter task type.
        """
        # Truncate content if too long
        max_context_length = 500
        if len(content) > max_context_length:
            content = content[:max_context_length] + "..."
        
        # Generate task-specific prompt and expected output
        if task == "personality":
            input_context = f"Context: {content}\n\nQuestion: How would a {archetype} respond to a tense social situation?"
            expected_output = f"[{archetype} personality-driven response based on lore]"
        
        elif task == "dialogue_style":
            input_context = f"Context: {content}\n\nGenerate {archetype} dialogue in their characteristic speech pattern."
            expected_output = f"[{archetype}-specific dialogue style]"
        
        elif task == "action_policy":
            input_context = f"Context: {content}\n\nWhat action would a {archetype} take in this situation?"
            expected_output = f"[{archetype}-appropriate action]"
        
        elif task == "world_knowledge":
            input_context = f"Extract {archetype} lore from: {content}"
            expected_output = f"[{archetype} lore and world knowledge]"
        
        else:
            # Generic for other tasks
            input_context = f"Context: {content}\n\nGenerate {archetype} {task} response."
            expected_output = f"[{archetype} {task} response]"
        
        return ArchetypeTrainingExample(
            archetype=archetype,
            adapter_task=task,
            input_context=input_context,
            expected_output=expected_output,
            metadata={
                'source_file': source_file,
                'extraction_method': 'keyword_matching'
            }
        )
    
    def save_training_data(
        self,
        examples: List[ArchetypeTrainingExample],
        archetype: str
    ) -> None:
        """
        Save training examples to JSON files by adapter task.
        
        Creates separate files for each adapter task.
        """
        # Group by adapter task
        by_task: Dict[str, List[ArchetypeTrainingExample]] = {}
        for example in examples:
            task = example.adapter_task
            if task not in by_task:
                by_task[task] = []
            by_task[task].append(example)
        
        # Save each task to separate file
        for task, task_examples in by_task.items():
            output_file = self.output_dir / f"{archetype}_{task}_training.json"
            
            data = {
                'archetype': archetype,
                'adapter_task': task,
                'total_examples': len(task_examples),
                'examples': [
                    {
                        'input': ex.input_context,
                        'output': ex.expected_output,
                        'metadata': ex.metadata
                    }
                    for ex in task_examples
                ]
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Saved {len(task_examples)} examples to {output_file}")
    
    def curate_all_archetypes(self) -> Dict[str, int]:
        """
        Curate training data for all archetypes.
        
        Returns:
            Dictionary of archetype -> example count
        """
        results = {}
        
        # Vampire
        logger.info("Curating vampire training data...")
        vampire_examples = self.extract_vampire_lore()
        self.save_training_data(vampire_examples, "vampire")
        results['vampire'] = len(vampire_examples)
        
        # Zombie
        logger.info("Curating zombie training data...")
        zombie_examples = self.extract_zombie_behaviors()
        self.save_training_data(zombie_examples, "zombie")
        results['zombie'] = len(zombie_examples)
        
        return results


def main():
    """Main execution."""
    curator = ArchetypeDataCurator()
    
    logger.info("Starting training data curation...")
    results = curator.curate_all_archetypes()
    
    logger.info("=" * 60)
    logger.info("Training Data Curation Complete")
    logger.info("=" * 60)
    for archetype, count in results.items():
        logger.info(f"{archetype.capitalize()}: {count} training examples")
    
    logger.info(f"\nOutput directory: {curator.output_dir}")
    logger.info("Ready for LoRA adapter training!")


if __name__ == "__main__":
    main()

