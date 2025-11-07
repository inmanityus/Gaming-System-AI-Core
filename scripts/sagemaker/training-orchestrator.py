#!/usr/bin/env python3
"""
SageMaker Training Orchestrator
Purpose: Coordinate training jobs across all tiers (Gold, Silver, Bronze)
Features: Dependency management, sequential/parallel execution, status monitoring
"""

import json
import boto3
import argparse
import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional
from enum import Enum

# SageMaker client
sagemaker_client = boto3.client('sagemaker')


class TrainingTier(Enum):
    """Training tier enumeration."""
    GOLD = "gold"
    SILVER = "silver"
    BRONZE = "bronze"


class TrainingStatus(Enum):
    """Training job status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


def load_tier_config(tier: TrainingTier, config_dir: Path) -> Dict[str, Any]:
    """Load training configuration for a specific tier."""
    config_file = config_dir / f"sagemaker-{tier.value}-tier" / "training-job-config.json"
    
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_file}")
    
    with open(config_file, 'r') as f:
        return json.load(f)


def create_training_job_for_tier(
    tier: TrainingTier,
    config: Dict[str, Any],
    job_name_suffix: str = ""
) -> str:
    """Create a training job for a specific tier."""
    from train_gold_tier import create_training_job as create_gold_job
    from train_silver_tier import create_training_job as create_silver_job
    from train_bronze_tier import create_training_job as create_bronze_job
    
    timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
    job_name = f"srl-rlvr-{tier.value}-{timestamp}{job_name_suffix}"
    
    # Extract common configuration
    role_arn = config.get('RoleArn')
    training_image = config.get('AlgorithmSpecification', {}).get('TrainingImage')
    instance_type = config.get('ResourceConfig', {}).get('InstanceType')
    checkpoint_s3_uri = config.get('CheckpointConfig', {}).get('S3Uri')
    output_s3_uri = config.get('OutputDataConfig', {}).get('S3OutputPath')
    training_data_s3_uri = config.get('InputDataConfig', [{}])[0].get('DataSource', {}).get('S3DataSource', {}).get('S3Uri')
    hyperparameters = config.get('HyperParameters', {})
    max_runtime_seconds = config.get('MaxRuntimeInSeconds')
    
    # Create tier-specific training job
    if tier == TrainingTier.GOLD:
        return create_gold_job(
            job_name=job_name,
            role_arn=role_arn,
            training_image=training_image,
            instance_type=instance_type,
            checkpoint_s3_uri=checkpoint_s3_uri,
            output_s3_uri=output_s3_uri,
            training_data_s3_uri=training_data_s3_uri,
            hyperparameters=hyperparameters,
            max_runtime_seconds=max_runtime_seconds
        )
    elif tier == TrainingTier.SILVER:
        return create_silver_job(
            job_name=job_name,
            role_arn=role_arn,
            training_image=training_image,
            instance_type=instance_type,
            checkpoint_s3_uri=checkpoint_s3_uri,
            output_s3_uri=output_s3_uri,
            training_data_s3_uri=training_data_s3_uri,
            hyperparameters=hyperparameters,
            max_runtime_seconds=max_runtime_seconds
        )
    elif tier == TrainingTier.BRONZE:
        instance_count = config.get('ResourceConfig', {}).get('InstanceCount', 2)
        distributed_strategy = hyperparameters.get('distributed_strategy', 'FSDP')
        return create_bronze_job(
            job_name=job_name,
            role_arn=role_arn,
            training_image=training_image,
            instance_type=instance_type,
            instance_count=instance_count,
            checkpoint_s3_uri=checkpoint_s3_uri,
            output_s3_uri=output_s3_uri,
            training_data_s3_uri=training_data_s3_uri,
            hyperparameters=hyperparameters,
            distributed_strategy=distributed_strategy,
            max_runtime_seconds=max_runtime_seconds
        )


def get_training_job_status(job_name: str) -> TrainingStatus:
    """Get the current status of a training job."""
    try:
        response = sagemaker_client.describe_training_job(TrainingJobName=job_name)
        status = response['TrainingJobStatus']
        
        if status == 'Completed':
            return TrainingStatus.COMPLETED
        elif status == 'Failed':
            return TrainingStatus.FAILED
        elif status in ['Stopped', 'Stopping']:
            return TrainingStatus.STOPPED
        elif status == 'InProgress':
            return TrainingStatus.RUNNING
        else:
            return TrainingStatus.PENDING
    except Exception as e:
        print(f"✗ Error getting training job status: {e}")
        return TrainingStatus.FAILED


def wait_for_job_completion(job_name: str, tier: TrainingTier, poll_interval: int = 60) -> bool:
    """Wait for a training job to complete."""
    print(f"\nWaiting for {tier.value.upper()} tier training job '{job_name}'...")
    
    while True:
        status = get_training_job_status(job_name)
        
        if status == TrainingStatus.COMPLETED:
            print(f"✓ {tier.value.upper()} tier training job completed successfully!")
            return True
        elif status == TrainingStatus.FAILED:
            print(f"✗ {tier.value.upper()} tier training job failed!")
            return False
        elif status == TrainingStatus.STOPPED:
            print(f"⚠ {tier.value.upper()} tier training job stopped")
            return False
        elif status == TrainingStatus.RUNNING:
            print(f"  {tier.value.upper()} tier: Running...", end='\r')
        
        time.sleep(poll_interval)


def orchestrate_training(
    tiers: List[TrainingTier],
    config_dir: Path,
    sequential: bool = True,
    wait: bool = False
) -> Dict[str, Any]:
    """
    Orchestrate training jobs across multiple tiers.
    
    Args:
        tiers: List of tiers to train
        config_dir: Directory containing Terraform configuration files
        sequential: If True, run tiers sequentially; if False, run in parallel
        wait: If True, wait for all jobs to complete
    
    Returns:
        Dictionary mapping tier names to job names and statuses
    """
    results = {}
    
    if sequential:
        # Run tiers sequentially (Gold → Silver → Bronze)
        for tier in tiers:
            print(f"\n=== Starting {tier.value.upper()} Tier Training ===")
            
            try:
                config = load_tier_config(tier, config_dir)
                job_name = create_training_job_for_tier(tier, config)
                results[tier.value] = {
                    'job_name': job_name,
                    'status': TrainingStatus.PENDING.value
                }
                
                if wait:
                    success = wait_for_job_completion(job_name, tier)
                    results[tier.value]['status'] = TrainingStatus.COMPLETED.value if success else TrainingStatus.FAILED.value
                    
                    if not success:
                        print(f"✗ {tier.value.upper()} tier failed. Stopping orchestration.")
                        break
                else:
                    print(f"✓ {tier.value.upper()} tier training job launched: {job_name}")
                    
            except Exception as e:
                print(f"✗ Failed to start {tier.value.upper()} tier training: {e}")
                results[tier.value] = {
                    'job_name': None,
                    'status': TrainingStatus.FAILED.value,
                    'error': str(e)
                }
                if wait:
                    break
    else:
        # Run tiers in parallel
        print("\n=== Starting Parallel Training ===")
        
        for tier in tiers:
            try:
                config = load_tier_config(tier, config_dir)
                job_name = create_training_job_for_tier(tier, config)
                results[tier.value] = {
                    'job_name': job_name,
                    'status': TrainingStatus.PENDING.value
                }
                print(f"✓ {tier.value.upper()} tier training job launched: {job_name}")
            except Exception as e:
                print(f"✗ Failed to start {tier.value.upper()} tier training: {e}")
                results[tier.value] = {
                    'job_name': None,
                    'status': TrainingStatus.FAILED.value,
                    'error': str(e)
                }
        
        if wait:
            # Wait for all jobs to complete
            for tier in tiers:
                if tier.value in results and results[tier.value]['job_name']:
                    wait_for_job_completion(results[tier.value]['job_name'], tier)
    
    return results


def main():
    parser = argparse.ArgumentParser(description='Orchestrate SageMaker Training Jobs Across All Tiers')
    parser.add_argument('--config-dir', type=str, default='infrastructure/terraform',
                       help='Directory containing Terraform configuration files')
    parser.add_argument('--tiers', type=str, nargs='+',
                       choices=['gold', 'silver', 'bronze'],
                       default=['gold', 'silver', 'bronze'],
                       help='Tiers to train (default: all)')
    parser.add_argument('--sequential', action='store_true', default=True,
                       help='Run tiers sequentially (default: True)')
    parser.add_argument('--parallel', action='store_true',
                       help='Run tiers in parallel (overrides --sequential)')
    parser.add_argument('--wait', action='store_true',
                       help='Wait for all training jobs to complete')
    
    args = parser.parse_args()
    
    # Parse tiers
    tiers = [TrainingTier(tier) for tier in args.tiers]
    
    # Determine execution mode
    sequential = not args.parallel if args.parallel else args.sequential
    
    # Load configuration directory
    config_dir = Path(args.config_dir)
    if not config_dir.exists():
        print(f"✗ Configuration directory not found: {config_dir}")
        sys.exit(1)
    
    # Orchestrate training
    results = orchestrate_training(
        tiers=tiers,
        config_dir=config_dir,
        sequential=sequential,
        wait=args.wait
    )
    
    # Print summary
    print("\n=== Training Orchestration Summary ===")
    for tier, result in results.items():
        status = result.get('status', 'unknown')
        job_name = result.get('job_name', 'N/A')
        print(f"  {tier.upper()}: {status} - {job_name}")


if __name__ == '__main__':
    main()




