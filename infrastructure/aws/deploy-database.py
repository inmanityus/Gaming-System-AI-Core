#!/usr/bin/env python3
"""
Deploy Aurora PostgreSQL database to AWS.
Handles CloudFormation deployment, parameter configuration, and post-deployment setup.
"""
import boto3
import argparse
import json
import time
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional
import psycopg2
from botocore.exceptions import ClientError


class AuroraDatabaseDeployer:
    """Deploy and configure Aurora PostgreSQL for Gaming System."""
    
    def __init__(self, region: str, stack_name: str):
        self.region = region
        self.stack_name = stack_name
        self.cf_client = boto3.client('cloudformation', region_name=region)
        self.rds_client = boto3.client('rds', region_name=region)
        self.secrets_client = boto3.client('secretsmanager', region_name=region)
        self.ec2_client = boto3.client('ec2', region_name=region)
    
    def get_vpc_info(self) -> Dict[str, Any]:
        """Get VPC information for deployment."""
        # Get default VPC or first available VPC
        vpcs = self.ec2_client.describe_vpcs(
            Filters=[{'Name': 'isDefault', 'Values': ['true']}]
        )
        
        if not vpcs['Vpcs']:
            # No default VPC, get first available
            vpcs = self.ec2_client.describe_vpcs(MaxResults=1)
        
        if not vpcs['Vpcs']:
            raise ValueError("No VPC found in the region")
        
        vpc_id = vpcs['Vpcs'][0]['VpcId']
        
        # Get private subnets (at least 2 in different AZs)
        subnets = self.ec2_client.describe_subnets(
            Filters=[
                {'Name': 'vpc-id', 'Values': [vpc_id]},
                {'Name': 'map-public-ip-on-launch', 'Values': ['false']}
            ]
        )
        
        if len(subnets['Subnets']) < 2:
            # Fall back to any subnets
            subnets = self.ec2_client.describe_subnets(
                Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
            )
        
        # Group by AZ and select one from each
        by_az = {}
        for subnet in subnets['Subnets']:
            az = subnet['AvailabilityZone']
            if az not in by_az:
                by_az[az] = subnet
        
        subnet_ids = [s['SubnetId'] for s in list(by_az.values())[:3]]
        
        if len(subnet_ids) < 2:
            raise ValueError("Need at least 2 subnets in different AZs")
        
        # Get or create application security group
        try:
            sg_response = self.ec2_client.describe_security_groups(
                GroupNames=['gaming-system-app-sg'],
                Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
            )
            app_sg_id = sg_response['SecurityGroups'][0]['GroupId']
        except ClientError:
            # Create application security group
            sg_response = self.ec2_client.create_security_group(
                GroupName='gaming-system-app-sg',
                Description='Security group for Gaming System application tier',
                VpcId=vpc_id
            )
            app_sg_id = sg_response['GroupId']
        
        return {
            'vpc_id': vpc_id,
            'subnet_ids': subnet_ids,
            'app_security_group_id': app_sg_id
        }
    
    def deploy_stack(
        self,
        template_path: str,
        environment: str,
        parameters: Optional[Dict[str, str]] = None
    ) -> str:
        """Deploy CloudFormation stack."""
        # Read template
        with open(template_path, 'r') as f:
            template_body = f.read()
        
        # Get VPC information
        vpc_info = self.get_vpc_info()
        
        # Build parameters
        stack_parameters = [
            {'ParameterKey': 'Environment', 'ParameterValue': environment},
            {'ParameterKey': 'VPCId', 'ParameterValue': vpc_info['vpc_id']},
            {
                'ParameterKey': 'PrivateSubnetIds',
                'ParameterValue': ','.join(vpc_info['subnet_ids'])
            },
            {
                'ParameterKey': 'ApplicationSecurityGroupId',
                'ParameterValue': vpc_info['app_security_group_id']
            }
        ]
        
        # Add custom parameters
        if parameters:
            for key, value in parameters.items():
                stack_parameters.append({
                    'ParameterKey': key,
                    'ParameterValue': value
                })
        
        # Check if stack exists
        try:
            self.cf_client.describe_stacks(StackName=self.stack_name)
            stack_exists = True
        except ClientError:
            stack_exists = False
        
        # Create or update stack
        try:
            if stack_exists:
                print(f"Updating stack: {self.stack_name}")
                self.cf_client.update_stack(
                    StackName=self.stack_name,
                    TemplateBody=template_body,
                    Parameters=stack_parameters,
                    Capabilities=['CAPABILITY_NAMED_IAM'],
                    Tags=[
                        {'Key': 'Project', 'Value': 'GamingSystemAICore'},
                        {'Key': 'Environment', 'Value': environment},
                        {'Key': 'ManagedBy', 'Value': 'CloudFormation'}
                    ]
                )
                waiter = self.cf_client.get_waiter('stack_update_complete')
            else:
                print(f"Creating stack: {self.stack_name}")
                self.cf_client.create_stack(
                    StackName=self.stack_name,
                    TemplateBody=template_body,
                    Parameters=stack_parameters,
                    Capabilities=['CAPABILITY_NAMED_IAM'],
                    Tags=[
                        {'Key': 'Project', 'Value': 'GamingSystemAICore'},
                        {'Key': 'Environment', 'Value': environment},
                        {'Key': 'ManagedBy', 'Value': 'CloudFormation'}
                    ],
                    EnableTerminationProtection=environment == 'production'
                )
                waiter = self.cf_client.get_waiter('stack_create_complete')
            
            # Wait for stack operation to complete
            print("Waiting for stack operation to complete...")
            waiter.wait(
                StackName=self.stack_name,
                WaiterConfig={'Delay': 30, 'MaxAttempts': 120}  # 60 minutes max
            )
            
            print("Stack operation completed successfully!")
            
        except ClientError as e:
            if 'No updates are to be performed' in str(e):
                print("Stack is already up to date")
            else:
                raise
        
        # Get stack outputs
        response = self.cf_client.describe_stacks(StackName=self.stack_name)
        outputs = response['Stacks'][0].get('Outputs', [])
        
        output_dict = {o['OutputKey']: o['OutputValue'] for o in outputs}
        return output_dict
    
    def get_db_credentials(self, secret_arn: str) -> Dict[str, str]:
        """Get database credentials from Secrets Manager."""
        try:
            response = self.secrets_client.get_secret_value(SecretId=secret_arn)
            credentials = json.loads(response['SecretString'])
            return credentials
        except ClientError as e:
            print(f"Error retrieving credentials: {e}")
            raise
    
    def wait_for_cluster_available(self, cluster_id: str, timeout: int = 600):
        """Wait for cluster to be available."""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                response = self.rds_client.describe_db_clusters(
                    DBClusterIdentifier=cluster_id
                )
                cluster = response['DBClusters'][0]
                
                if cluster['Status'] == 'available':
                    print(f"Cluster {cluster_id} is available")
                    return True
                
                print(f"Cluster status: {cluster['Status']}, waiting...")
                time.sleep(30)
                
            except ClientError as e:
                print(f"Error checking cluster status: {e}")
                time.sleep(30)
        
        raise TimeoutError(f"Cluster {cluster_id} not available after {timeout} seconds")
    
    def initialize_database(self, outputs: Dict[str, str], credentials: Dict[str, str]):
        """Initialize database schema and data."""
        # Wait a bit for DNS to propagate
        print("Waiting for DNS propagation...")
        time.sleep(30)
        
        # Use proxy endpoint if available, otherwise direct cluster endpoint
        endpoint = outputs.get('DBProxyEndpoint', outputs['DBClusterEndpoint'])
        
        print(f"Connecting to database at {endpoint}...")
        
        try:
            # Connect to database
            conn = psycopg2.connect(
                host=endpoint,
                port=5432,
                database=outputs['DBName'],
                user=credentials['username'],
                password=credentials['password'],
                connect_timeout=30,
                options='-c statement_timeout=60000'  # 60 second timeout
            )
            conn.autocommit = False
            cur = conn.cursor()
            
            print("Connected to database. Running initialization script...")
            
            # Read and execute SQL file
            sql_file = Path(__file__).parent.parent / "database" / "create_gaming_system_db.sql"
            with open(sql_file, 'r') as f:
                sql_content = f.read()
            
            # Remove database creation commands (already created by CloudFormation)
            sql_lines = []
            skip_until_connect = False
            for line in sql_content.split('\n'):
                if 'CREATE DATABASE' in line:
                    skip_until_connect = True
                elif '\\c gaming_system_ai_core' in line:
                    skip_until_connect = False
                    continue
                elif not skip_until_connect:
                    sql_lines.append(line)
            
            sql_content = '\n'.join(sql_lines)
            
            # Execute initialization
            cur.execute(sql_content)
            conn.commit()
            
            print("Database initialized successfully!")
            
            # Verify initialization
            cur.execute("""
                SELECT 
                    schema_name,
                    (SELECT COUNT(*) FROM information_schema.tables 
                     WHERE table_schema = s.schema_name) as table_count
                FROM information_schema.schemata s
                WHERE schema_name NOT IN ('pg_catalog', 'information_schema', 'public')
                ORDER BY schema_name
            """)
            
            print("\nDatabase schema summary:")
            for row in cur.fetchall():
                print(f"  - {row[0]}: {row[1]} tables")
            
            cur.close()
            conn.close()
            
        except Exception as e:
            print(f"Error initializing database: {e}")
            raise
    
    def enable_performance_features(self, cluster_id: str):
        """Enable performance features on the cluster."""
        try:
            # Get cluster instances
            response = self.rds_client.describe_db_clusters(
                DBClusterIdentifier=cluster_id
            )
            
            for member in response['DBClusters'][0]['DBClusterMembers']:
                instance_id = member['DBInstanceIdentifier']
                
                # Enable query insights if not already enabled
                instance_response = self.rds_client.describe_db_instances(
                    DBInstanceIdentifier=instance_id
                )
                instance = instance_response['DBInstances'][0]
                
                if not instance.get('PerformanceInsightsEnabled', False):
                    print(f"Enabling Performance Insights on {instance_id}...")
                    self.rds_client.modify_db_instance(
                        DBInstanceIdentifier=instance_id,
                        EnablePerformanceInsights=True,
                        PerformanceInsightsRetentionPeriod=7,
                        ApplyImmediately=True
                    )
            
            print("Performance features enabled")
            
        except Exception as e:
            print(f"Warning: Could not enable all performance features: {e}")
    
    def print_connection_info(self, outputs: Dict[str, str], credentials: Dict[str, str]):
        """Print connection information for developers."""
        print("\n" + "="*60)
        print("DATABASE DEPLOYMENT COMPLETE")
        print("="*60)
        
        print("\nConnection Endpoints:")
        print(f"  Writer Endpoint: {outputs['DBClusterEndpoint']}")
        print(f"  Reader Endpoint: {outputs['DBClusterReadEndpoint']}")
        print(f"  Proxy Endpoint: {outputs['DBProxyEndpoint']}")
        
        print("\nConnection String:")
        print(f"  postgresql://{credentials['username']}:<password>@{outputs['DBProxyEndpoint']}:5432/{outputs['DBName']}")
        
        print("\nPython Connection Example:")
        print("""
import asyncpg
import os

# Using environment variables (recommended)
DATABASE_URL = os.getenv('DATABASE_URL')

# Or construct from parts
async def get_connection():
    return await asyncpg.connect(
        host=os.getenv('DB_PROXY_ENDPOINT'),
        port=5432,
        database=os.getenv('DB_NAME'),
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        ssl='require'
    )
""")
        
        print("\nEnvironment Variables to Set:")
        print(f"  export DB_PROXY_ENDPOINT={outputs['DBProxyEndpoint']}")
        print(f"  export DB_CLUSTER_ENDPOINT={outputs['DBClusterEndpoint']}")
        print(f"  export DB_READ_ENDPOINT={outputs['DBClusterReadEndpoint']}")
        print(f"  export DB_NAME={outputs['DBName']}")
        print(f"  export DB_SECRET_ARN={outputs['DBSecretArn']}")
        print("  export DB_USER=<from-secrets-manager>")
        print("  export DB_PASSWORD=<from-secrets-manager>")
        
        print("\nTo retrieve credentials:")
        print(f"  aws secretsmanager get-secret-value --secret-id {outputs['DBSecretArn']} --query SecretString --output text | jq")
        
        print("\n" + "="*60)


def main():
    parser = argparse.ArgumentParser(description='Deploy Aurora PostgreSQL Database')
    parser.add_argument(
        '--region',
        default='us-east-1',
        help='AWS region for deployment'
    )
    parser.add_argument(
        '--stack-name',
        default='gaming-system-aurora-db',
        help='CloudFormation stack name'
    )
    parser.add_argument(
        '--environment',
        choices=['development', 'staging', 'production'],
        default='production',
        help='Deployment environment'
    )
    parser.add_argument(
        '--template',
        default='infrastructure/aws/database/rds-aurora-postgresql-v2.yaml',
        help='CloudFormation template path'
    )
    parser.add_argument(
        '--enable-global-db',
        action='store_true',
        help='Enable Aurora Global Database for cross-region HA'
    )
    parser.add_argument(
        '--performance-insights-retention',
        type=int,
        default=7,
        choices=[7, 31, 62, 93, 124, 155, 186, 217, 248, 279, 310, 341, 372, 403, 434, 465, 496, 527, 558, 589, 620, 651, 682, 713, 731],
        help='Performance Insights retention in days'
    )
    parser.add_argument(
        '--skip-init',
        action='store_true',
        help='Skip database initialization'
    )
    
    args = parser.parse_args()
    
    # Verify AWS credentials
    try:
        boto3.client('sts').get_caller_identity()
    except Exception as e:
        print(f"Error: Unable to authenticate with AWS: {e}")
        print("Please configure AWS credentials")
        sys.exit(1)
    
    # Deploy
    deployer = AuroraDatabaseDeployer(args.region, args.stack_name)
    
    try:
        # Deploy CloudFormation stack
        print(f"Deploying Aurora PostgreSQL to {args.region}...")
        outputs = deployer.deploy_stack(
            args.template,
            args.environment,
            {
                'EnableGlobalDatabase': 'true' if args.enable_global_db else 'false',
                'PerformanceInsightsRetention': str(args.performance_insights_retention)
            }
        )
        
        # Get credentials
        print("\nRetrieving database credentials...")
        credentials = deployer.get_db_credentials(outputs['DBSecretArn'])
        
        # Wait for cluster
        cluster_id = outputs['DBClusterEndpoint'].split('.')[0]
        deployer.wait_for_cluster_available(cluster_id)
        
        # Initialize database
        if not args.skip_init:
            print("\nInitializing database schema...")
            deployer.initialize_database(outputs, credentials)
        
        # Enable performance features
        deployer.enable_performance_features(cluster_id)
        
        # Print connection info
        deployer.print_connection_info(outputs, credentials)
        
        print("\nDeployment completed successfully!")
        
    except Exception as e:
        print(f"\nError during deployment: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
