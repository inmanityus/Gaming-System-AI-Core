#!/usr/bin/env python3
"""
SageMaker Bronze Tier Training Script
Purpose: Launch SageMaker training jobs for Bronze tier models (671B MoE)
Instance: p5.48xlarge multi-node (SMDDP/FSDP)
Distributed Training: PyTorch FSDP or SageMaker DDP
Checkpointing: Every 30 minutes
"""

import json
import boto3
import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# SageMaker client
sagemaker_client = boto3.client('sagemaker')
s3_client = boto3.client('s3')


def load_training_config(config_path: str) -> Dict[str, Any]:
    """Load training job configuration from Terraform output."""
    with open(config_path, 'r') as f:
        return json.load(f)


def create_training_job(
    job_name: str,
    role_arn: str,
    training_image: str,
    instance_type: str,
    instance_count: int,
    checkpoint_s3_uri: str,
    output_s3_uri: str,
    training_data_s3_uri: str,
    hyperparameters: Dict[str, str],
    distributed_strategy: str = "FSDP",
    max_runtime_seconds: int = 172800  # 48 hours for Bronze tier
) -> str:
    """
    Create a SageMaker training job for Bronze tier with distributed training.
    
    Args:
        job_name: Unique name for the training job
        role_arn: IAM role ARN for SageMaker
        training_image: Docker image URI
        instance_type: EC2 instance type (p5.48xlarge)
        instance_count: Number of instances for distributed training
        checkpoint_s3_uri: S3 URI for checkpoints
        output_s3_uri: S3 URI for output
        training_data_s3_uri: S3 URI for training data
        hyperparameters: Training hyperparameters
        distributed_strategy: Distributed training strategy (FSDP, SMDDP, DDP)
        max_runtime_seconds: Maximum runtime in seconds
    
    Returns:
        Training job name
    """
    training_job_config = {
        'TrainingJobName': job_name,
        'RoleArn': role_arn,
        'AlgorithmSpecification': {
            'TrainingImage': training_image,
            'TrainingInputMode': 'File'
        },
        'ResourceConfig': {
            'InstanceType': instance_type,
            'InstanceCount': instance_count,  # Multi-node for Bronze tier
            'VolumeSizeInGB': 1000  # Large volume for Bronze tier
        },
        'EnableManagedSpotTraining': False,  # On-demand for stability in Bronze tier
        'MaxRuntimeInSeconds': max_runtime_seconds,
        'CheckpointConfig': {
            'S3Uri': checkpoint_s3_uri,
            'LocalPath': '/opt/ml/checkpoints'
        },
        'StoppingCondition': {
            'MaxRuntimeInSeconds': max_runtime_seconds
        },
        'InputDataConfig': [
            {
                'ChannelName': 'training',
                'DataSource': {
                    'S3DataSource': {
                        'S3DataType': 'S3Prefix',
                        'S3Uri': training_data_s3_uri,
                        'S3DataDistributionType': 'ShardedByS3Key'  # Sharded for distributed training
                    }
                },
                'ContentType': 'application/json'
            }
        ],
        'OutputDataConfig': {
            'S3OutputPath': output_s3_uri
        },
        'HyperParameters': {
            **hyperparameters,
            'distributed_strategy': distributed_strategy,
            'world_size': str(instance_count * 8),  # 8 GPUs per p5.48xlarge
            'checkpoint_frequency': '1800'  # 30 minutes
        },
        'Tags': [
            {'Key': 'Tier', 'Value': 'Bronze'},
            {'Key': 'Purpose', 'Value': 'SRL-RLVR-Training'},
            {'Key': 'Environment', 'Value': 'production'},
            {'Key': 'DistributedStrategy', 'Value': distributed_strategy}
        ]
    }
    
    try:
        response = sagemaker_client.create_training_job(**training_job_config)
        print(f"✓ Training job created: {job_name}")
        print(f"  ARN: {response['TrainingJobArn']}")
        print(f"  Instance Count: {instance_count}")
        print(f"  Distributed Strategy: {distributed_strategy}")
        print(f"  Total GPUs: {instance_count * 8}")
        return job_name
    except Exception as e:
        print(f"✗ Failed to create training job: {e}")
        sys.exit(1)


def wait_for_training_job(job_name: str, poll_interval: int = 120):
    """Wait for training job to complete (longer interval for multi-node jobs)."""
    print(f"\nWaiting for training job '{job_name}' to complete...")
    print("  (This may take many hours for multi-node distributed training)")
    
    while True:
        try:
            response = sagemaker_client.describe_training_job(TrainingJobName=job_name)
            status = response['TrainingJobStatus']
            
            if status == 'Completed':
                print(f"\n✓ Training job completed successfully!")
                print(f"  Final model: {response.get('ModelArtifacts', {}).get('S3ModelArtifacts', 'N/A')}")
                return True
            elif status == 'Failed':
                print(f"\n✗ Training job failed!")
                print(f"  Failure reason: {response.get('FailureReason', 'Unknown')}")
                return False
            elif status in ['Stopped', 'Stopping']:
                print(f"\n⚠ Training job stopped")
                return False
            else:
                print(f"  Status: {status}...", end='\r')
                
        except Exception as e:
            print(f"\n✗ Error checking training job status: {e}")
            return False
        
        import time
        time.sleep(poll_interval)


def main():
    parser = argparse.ArgumentParser(description='Launch SageMaker Bronze Tier Training Job (Distributed)')
    parser.add_argument('--config', type=str, required=True,
                       help='Path to training job configuration file (from Terraform)')
    parser.add_argument('--job-name', type=str, default=None,
                       help='Training job name (default: auto-generated)')
    parser.add_argument('--instance-count', type=int, default=2,
                       help='Number of instances for distributed training (default: 2)')
    parser.add_argument('--distributed-strategy', type=str, default='FSDP',
                       choices=['FSDP', 'SMDDP', 'DDP'],
                       help='Distributed training strategy (default: FSDP)')
    parser.add_argument('--wait', action='store_true',
                       help='Wait for training job to complete')
    
    args = parser.parse_args()
    
    # Load configuration
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"✗ Configuration file not found: {config_path}")
        sys.exit(1)
    
    config = load_training_config(str(config_path))
    
    # Generate job name if not provided
    job_name = args.job_name or f"srl-rlvr-bronze-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    # Extract configuration
    role_arn = config.get('RoleArn')
    training_image = config.get('AlgorithmSpecification', {}).get('TrainingImage')
    instance_type = config.get('ResourceConfig', {}).get('InstanceType', 'ml.p5.48xlarge')
    instance_count = args.instance_count or config.get('ResourceConfig', {}).get('InstanceCount', 2)
    checkpoint_s3_uri = config.get('CheckpointConfig', {}).get('S3Uri')
    output_s3_uri = config.get('OutputDataConfig', {}).get('S3OutputPath')
    training_data_s3_uri = config.get('InputDataConfig', [{}])[0].get('DataSource', {}).get('S3DataSource', {}).get('S3Uri')
    hyperparameters = config.get('HyperParameters', {})
    distributed_strategy = args.distributed_strategy or config.get('HyperParameters', {}).get('distributed_strategy', 'FSDP')
    max_runtime_seconds = config.get('MaxRuntimeInSeconds', 172800)
    
    # Validate required fields
    if not all([role_arn, training_image, checkpoint_s3_uri, output_s3_uri, training_data_s3_uri]):
        print("✗ Missing required configuration fields")
        sys.exit(1)
    
    # Validate instance count for distributed training
    if instance_count < 2:
        print("✗ Bronze tier requires at least 2 instances for distributed training")
        sys.exit(1)
    
    # Create training job
    create_training_job(
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
    
    # Wait for completion if requested
    if args.wait:
        wait_for_training_job(job_name)
    else:
        print(f"\nTraining job '{job_name}' launched successfully")
        print(f"Monitor progress: aws sagemaker describe-training-job --training-job-name {job_name}")


if __name__ == '__main__':
    main()


