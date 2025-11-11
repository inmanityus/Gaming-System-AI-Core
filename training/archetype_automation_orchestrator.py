"""
Archetype Automation Orchestrator - Master Controller
Coder: Claude Sonnet 4.5
Reviewer: GPT-Codex-2 (Pending)

Coordinates all 4 stages of archetype automation:
Stage 1: Narrative Design AI (profile generation)
Stage 2: Training Data Generator AI (10k+ examples)
Stage 3: Training Queue Manager (7 LoRA adapters)
Stage 4: Inspector AI + Behavioral Validator (quality validation)

Fully autonomous archetype creation from concept to production-ready.

Timeline: 2-4 hours per archetype (fully autonomous)
Cost: ~$10 per archetype
"""

import os
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

# Import automation stages
from narrative_design_ai import NarrativeDesignAI, ArchetypeConcept, ArchetypeProfile
from training_data_generator_ai import TrainingDataGeneratorAI, GenerationConfig
from train_lora_adapter import TrainingQueueManager, AdapterInspector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ArchetypeCreationJob:
    """Job specification for creating an archetype."""
    job_id: str
    concept: ArchetypeConcept
    status: str = "pending"  # pending, stage1, stage2, stage3, stage4, completed, failed
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None
    results: Dict = None


class ArchetypeAutomationOrchestrator:
    """
    Master orchestrator for end-to-end archetype creation.
    
    Coordinates all 4 stages:
    1. Narrative Design (Gemini 2.5 Pro)
    2. Training Data Generation (GPT-4 Turbo)
    3. Adapter Training (Queue System)
    4. Quality Validation (Inspector + Behavioral tests)
    
    Fully autonomous operation with checkpoints and recovery.
    """
    
    def __init__(self):
        self.narrative_ai = NarrativeDesignAI()
        self.data_generator = TrainingDataGeneratorAI()
        self.inspector = AdapterInspector()
        
        self.jobs = {}
        self.state_file = Path("archetype_automation_state.json")
        
        logger.info("Archetype Automation Orchestrator initialized")
    
    def create_archetype(self, concept: ArchetypeConcept) -> Dict:
        """
        Create complete archetype from concept (fully autonomous).
        
        Takes 2-4 hours, costs ~$10, requires zero human intervention.
        """
        job_id = f"{concept.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        job = ArchetypeCreationJob(
            job_id=job_id,
            concept=concept,
            status="pending",
            started_at=datetime.now().isoformat(),
            results={}
        )
        
        self.jobs[job_id] = job
        self.save_state()
        
        logger.info(f"\n{'='*60}\nCREATING ARCHETYPE: {concept.name}\n{'='*60}")
        logger.info(f"Job ID: {job_id}")
        
        try:
            # Stage 1: Narrative Design
            job.status = "stage1"
            self.save_state()
            
            try:
                profile = self.run_stage1(concept)
                job.results['profile'] = profile
                job.results['stage1_status'] = 'completed'
                logger.info("✅ Stage 1 complete: Narrative design")
            except Exception as e:
                logger.error(f"❌ Stage 1 failed: {e}")
                job.results['stage1_status'] = 'failed'
                job.results['stage1_error'] = str(e)
                raise  # Cannot continue without profile
            
            # Stage 2: Training Data Generation
            job.status = "stage2"
            self.save_state()
            
            try:
                training_data = self.run_stage2(profile, concept.name)
                job.results['training_data_stats'] = {
                    adapter: {
                        'examples': len(data['examples']),
                        'quality': data['quality_score']
                    }
                    for adapter, data in training_data.items()
                }
                job.results['stage2_status'] = 'completed'
                logger.info("✅ Stage 2 complete: Training data generated")
            except Exception as e:
                logger.error(f"❌ Stage 2 failed: {e}")
                job.results['stage2_status'] = 'failed'
                job.results['stage2_error'] = str(e)
                raise  # Cannot train without data
            
            # Stage 3: Adapter Training
            job.status = "stage3"
            self.save_state()
            
            try:
                adapters = self.run_stage3(concept.name, training_data)
                job.results['adapters'] = adapters
                job.results['stage3_status'] = 'completed'
                logger.info("✅ Stage 3 complete: Adapters trained")
            except Exception as e:
                logger.error(f"❌ Stage 3 failed: {e}")
                job.results['stage3_status'] = 'failed'
                job.results['stage3_error'] = str(e)
                raise  # Cannot validate without adapters
            
            # Stage 4: Quality Validation
            job.status = "stage4"
            self.save_state()
            
            try:
                validation = self.run_stage4(concept.name, adapters)
                job.results['validation'] = validation
                job.results['stage4_status'] = 'completed'
                logger.info("✅ Stage 4 complete: Quality validated")
                
                # Check if production ready
                if not validation['production_ready']:
                    logger.warning("⚠️ Archetype not production-ready (validation failed)")
                    # Continue anyway - mark as completed but flag quality issue
                    job.results['quality_warning'] = 'Not production-ready'
                
            except Exception as e:
                logger.error(f"❌ Stage 4 failed: {e}")
                job.results['stage4_status'] = 'failed'
                job.results['stage4_error'] = str(e)
                # Stage 4 failure is not fatal - adapters are trained
                logger.warning("⚠️ Continuing despite validation failure")
            
            # Mark complete (even if stage 4 failed - adapters exist)
            job.status = "completed"
            job.completed_at = datetime.now().isoformat()
            self.save_state()
            
            duration = self.calculate_duration(job)
            
            logger.info(f"\n{'='*60}\n✅ ARCHETYPE COMPLETE: {concept.name}\n{'='*60}")
            logger.info(f"Duration: {duration:.1f} minutes")
            
            if 'validation' in job.results:
                logger.info(f"Quality: {job.results['validation']['overall_quality']:.2f}")
                logger.info(f"Production Ready: {job.results['validation']['production_ready']}")
            
            return {
                'job_id': job_id,
                'archetype_name': concept.name,
                'status': 'completed',
                'duration_minutes': duration,
                'results': job.results,
                'production_ready': job.results.get('validation', {}).get('production_ready', False)
            }
        
        except Exception as e:
            logger.error(f"❌ Archetype creation failed at {job.status}: {e}")
            job.status = "failed"
            job.error = str(e)
            job.completed_at = datetime.now().isoformat()
            self.save_state()
            
            return {
                'job_id': job_id,
                'archetype_name': concept.name,
                'status': 'failed',
                'failed_at_stage': job.status,
                'error': str(e),
                'partial_results': job.results
            }
    
    def run_stage1(self, concept: ArchetypeConcept) -> Dict:
        """Stage 1: Generate archetype profile."""
        logger.info("\n--- Stage 1: Narrative Design ---")
        profile = self.narrative_ai.design_archetype(concept)
        
        # Convert to dict for JSON serialization
        return {
            'archetype_name': profile.archetype_name,
            'core_identity': profile.core_identity,
            'behavioral_traits': profile.behavioral_traits,
            'dark_world_integration': profile.dark_world_integration,
            'narrative_hooks': profile.narrative_hooks
        }
    
    def run_stage2(self, profile: Dict, archetype_name: str) -> Dict:
        """Stage 2: Generate training data for all 7 adapters."""
        logger.info("\n--- Stage 2: Training Data Generation ---")
        
        training_data = self.data_generator.generate_all_adapters(profile, archetype_name)
        
        return training_data
    
    def run_stage3(self, archetype_name: str, training_data: Dict) -> Dict:
        """Stage 3: Train all 7 adapters using queue system."""
        logger.info("\n--- Stage 3: Adapter Training ---")
        
        # Create queue file for this archetype
        queue_data = self.create_training_queue(archetype_name, training_data)
        queue_file = self.save_training_queue(queue_data, archetype_name)
        
        # Run training queue
        manager = TrainingQueueManager(queue_file)
        manager.process_queue()
        
        # Return adapter paths
        adapters = {}
        for adapter_task in ['personality', 'dialogue_style', 'action_policy',
                             'emotional_response', 'world_knowledge',
                             'social_dynamics', 'goal_prioritization']:
            adapters[adapter_task] = f"adapters/{archetype_name}/{adapter_task}"
        
        return adapters
    
    def run_stage4(self, archetype_name: str, adapters: Dict) -> Dict:
        """Stage 4: Validate all adapters."""
        logger.info("\n--- Stage 4: Quality Validation ---")
        
        validation_results = {}
        
        for adapter_task, adapter_path in adapters.items():
            report = self.inspector.validate_adapter(
                archetype_name, adapter_task, adapter_path
            )
            validation_results[adapter_task] = report
        
        # Calculate overall quality
        overall_quality = self.calculate_overall_quality(validation_results)
        production_ready = all(
            r['overall_status'] in ['passed', 'passed_with_warnings']
            for r in validation_results.values()
        )
        
        return {
            'adapter_validations': validation_results,
            'overall_quality': overall_quality,
            'production_ready': production_ready
        }
    
    def create_training_queue(self, archetype_name: str, training_data: Dict) -> Dict:
        """Create training queue configuration for archetype."""
        tasks = []
        task_id = 1
        
        for adapter_task in training_data.keys():
            tasks.append({
                "id": task_id,
                "archetype": archetype_name,
                "adapter": adapter_task,
                "status": "pending",
                "priority": 1,
                "retries": 0,
                "started_at": None,
                "completed_at": None,
                "error": None,
                "metrics": {}
            })
            task_id += 1
        
        return {
            "queue_name": f"{archetype_name}_training_queue",
            "created": datetime.now().isoformat(),
            "version": "1.0",
            "config": {
                "auto_start_next": True,
                "stop_on_error": False,
                "max_retries": 2,
                "validation_checkpoints": [7],  # Validate after all 7
                "save_checkpoint_after_each": True
            },
            "tasks": tasks,
            "summary": {
                "total_tasks": len(tasks),
                "pending": len(tasks),
                "in_progress": 0,
                "completed": 0,
                "failed": 0
            }
        }
    
    def save_training_queue(self, queue_data: Dict, archetype_name: str) -> str:
        """Save training queue to file."""
        from narrative_design_ai import sanitize_filename
        
        safe_name = sanitize_filename(archetype_name)
        queue_path = Path(f"{safe_name}_training_queue.json")
        
        with open(queue_path, 'w') as f:
            json.dump(queue_data, f, indent=2)
        
        return str(queue_path)
    
    def calculate_overall_quality(self, validation_results: Dict) -> float:
        """Calculate overall quality score across all adapters."""
        if not validation_results:
            return 0.0
        
        scores = []
        for result in validation_results.values():
            pass_rate = result['tests_passed'] / (result['tests_passed'] + result['tests_failed'])
            scores.append(pass_rate)
        
        return sum(scores) / len(scores)
    
    def calculate_duration(self, job: ArchetypeCreationJob) -> float:
        """Calculate job duration in minutes."""
        if not job.started_at or not job.completed_at:
            return 0.0
        
        start = datetime.fromisoformat(job.started_at)
        end = datetime.fromisoformat(job.completed_at)
        duration_seconds = (end - start).total_seconds()
        
        return duration_seconds / 60.0
    
    def save_state(self) -> None:
        """Save orchestrator state (for recovery)."""
        state = {
            'jobs': {
                job_id: {
                    'job_id': job.job_id,
                    'concept': {
                        'name': job.concept.name,
                        'concept': job.concept.concept,
                        'primary_trait': job.concept.primary_trait
                    },
                    'status': job.status,
                    'started_at': job.started_at,
                    'completed_at': job.completed_at,
                    'error': job.error,
                    'results': job.results
                }
                for job_id, job in self.jobs.items()
            },
            'last_updated': datetime.now().isoformat()
        }
        
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def create_batch(self, concepts: List[ArchetypeConcept], 
                    max_parallel: int = 1) -> List[Dict]:
        """
        Create multiple archetypes.
        
        Note: max_parallel=1 for now (sequential). Parallel support in future.
        """
        logger.info(f"\n{'='*60}\nBATCH CREATION: {len(concepts)} Archetypes\n{'='*60}")
        
        results = []
        
        for i, concept in enumerate(concepts):
            logger.info(f"\nArchetype {i+1}/{len(concepts)}: {concept.name}")
            
            try:
                result = self.create_archetype(concept)
                results.append(result)
                logger.info(f"✅ {concept.name} complete")
            except Exception as e:
                logger.error(f"❌ {concept.name} failed: {e}")
                results.append({
                    'archetype_name': concept.name,
                    'status': 'failed',
                    'error': str(e)
                })
        
        # Summary
        successful = sum(1 for r in results if r['status'] == 'completed')
        logger.info(f"\n{'='*60}\nBATCH COMPLETE\n{'='*60}")
        logger.info(f"Successful: {successful}/{len(concepts)}")
        logger.info(f"Failed: {len(concepts) - successful}/{len(concepts)}")
        
        return results


if __name__ == "__main__":
    # Test orchestrator
    concept = ArchetypeConcept(
        name="werewolf",
        concept="A cursed human who transforms under the full moon, torn between morality and primal hunger.",
        primary_trait="cursed"
    )
    
    orchestrator = ArchetypeAutomationOrchestrator()
    
    # This would run full pipeline (takes 2-4 hours)
    # result = orchestrator.create_archetype(concept)
    
    print("✅ Orchestrator initialized and ready")

