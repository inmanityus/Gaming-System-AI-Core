#!/usr/bin/env python3
"""
SageMaker Silver Tier Training Script
Purpose: Launch SageMaker training jobs for Silver tier models (7B-13B)
Instance: p5.48xlarge (8× H100) single-node
Managed Spot Training: 80%+
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
    checkpoint_s3_uri: str,
    output_s3_uri: str,
    training_data_s3_uri: str,
    hyperparameters: Dict[str, str],
    max_runtime_seconds: int = 86400  # 24 hours for Silver tier
) -> str:
    """
    Create a SageMaker training job for Silver tier.
    
    Args:
        job_name: Unique name for the training job
        role_arn: IAM role ARN for SageMaker
        training_image: Docker image URI
        instance_type: EC2 instance type (p5.48xlarge)
        checkpoint_s3_uri: S3 URI for checkpoints
        output_s3_uri: S3 URI for output
        training_data_s3_uri: S3 URI for training data
        hyperparameters: Training hyperparameters
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
            'InstanceCount': 1,  # Single-node for Silver tier
            'VolumeSizeInGB': 500  # Larger volume for Silver tier
        },
        'EnableManagedSpotTraining': True,
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
                        'S3DataDistributionType': 'FullyReplicated'
                    }
                },
                'ContentType': 'application/json'
            }
        ],
        'OutputDataConfig': {
            'S3OutputPath': output_s3_uri
        },
        'HyperParameters': hyperparameters,
        'Tags': [
            {'Key': 'Tier', 'Value': 'Silver'},
            {'Key': 'Purpose', 'Value': 'SRL-RLVR-Training'},
            {'Key': 'Environment', 'Value': 'production'}
        ]
    }
    
    try:
        response = sagemaker_client.create_training_job(**training_job_config)
        print(f"✓ Training job created: {job_name}")
        print(f"  ARN: {response['TrainingJobArn']}")
        return job_name
    except Exception as e:
        print(f"✗ Failed to create training job: {e}")
        sys.exit(1)


def wait_for_training_job(job_name: str, poll_interval: int = 60):
    """Wait for training job to complete."""
    print(f"\nWaiting for training job '{job_name}' to complete...")
    print("  (This may take several hours)")
    
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
    parser = argparse.ArgumentParser(description='Launch SageMaker Silver Tier Training Job')
    parser.add_argument('--config', type=str, required=True,
                       help='Path to training job configuration file (from Terraform)')
    parser.add_argument('--job-name', type=str, default=None,
                       help='Training job name (default: auto-generated)')
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
    job_name = args.job_name or f"srl-rlvr-silver-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    # Extract configuration
    role_arn = config.get('RoleArn')
    training_image = config.get('AlgorithmSpecification', {}).get('TrainingImage')
    instance_type = config.get('ResourceConfig', {}).get('InstanceType', 'ml.p5.48xlarge')
    checkpoint_s3_uri = config.get('CheckpointConfig', {}).get('S3Uri')
    output_s3_uri = config.get('OutputDataConfig', {}).get('S3OutputPath')
    training_data_s3_uri = config.get('InputDataConfig', [{}])[0].get('DataSource', {}).get('S3DataSource', {}).get('S3Uri')
    hyperparameters = config.get('HyperParameters', {})
    max_runtime_seconds = config.get('MaxRuntimeInSeconds', 86400)
    
    # Validate required fields
    if not all([role_arn, training_image, checkpoint_s3_uri, output_s3_uri, training_data_s3_uri]):
        print("✗ Missing required configuration fields")
        sys.exit(1)
    
    # Create training job
    create_training_job(
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
    
    # Wait for completion if requested
    if args.wait:
        wait_for_training_job(job_name)
    else:
        print(f"\nTraining job '{job_name}' launched successfully")
        print(f"Monitor progress: aws sagemaker describe-training-job --training-job-name {job_name}")


if __name__ == '__main__':
    main()




