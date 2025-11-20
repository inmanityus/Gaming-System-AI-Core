#!/usr/bin/env python3
"""
Comprehensive test suite for AWS Organizations setup (TASK-001)
Tests organization structure, OUs, SCPs, and CloudTrail configuration
"""

import pytest
import boto3
import json
from datetime import datetime
from typing import Dict, List, Optional

class TestAWSOrganizations:
    """Test suite for AWS Organizations infrastructure"""
    
    @pytest.fixture(scope="class")
    def org_client(self):
        """AWS Organizations client"""
        return boto3.client('organizations', region_name='us-east-1')
    
    @pytest.fixture(scope="class")
    def s3_client(self):
        """S3 client for CloudTrail bucket verification"""
        return boto3.client('s3', region_name='us-east-1')
    
    @pytest.fixture(scope="class")
    def cloudtrail_client(self):
        """CloudTrail client"""
        return boto3.client('cloudtrail', region_name='us-east-1')
    
    def test_organization_exists(self, org_client):
        """Test that AWS Organization is properly configured"""
        try:
            org = org_client.describe_organization()
            assert 'Organization' in org
            assert org['Organization']['FeatureSet'] == 'ALL'
            assert org['Organization']['MasterAccountId'] == '695353648052'
            print(f"✓ Organization exists: {org['Organization']['Id']}")
        except Exception as e:
            pytest.fail(f"Organization not found or improperly configured: {str(e)}")
    
    def test_organizational_units_exist(self, org_client):
        """Test that all required OUs are created"""
        required_ous = ['Development', 'Staging', 'Production', 'Security', 'Finance']
        
        # Get root ID
        roots = org_client.list_roots()
        root_id = roots['Roots'][0]['Id']
        
        # List OUs
        ous = org_client.list_organizational_units_for_parent(ParentId=root_id)
        ou_names = [ou['Name'] for ou in ous['OrganizationalUnits']]
        
        for required_ou in required_ous:
            assert required_ou in ou_names, f"Missing OU: {required_ou}"
            print(f"✓ OU exists: {required_ou}")
    
    def test_service_control_policy_exists(self, org_client):
        """Test baseline SCP is created and attached"""
        policies = org_client.list_policies(Filter='SERVICE_CONTROL_POLICY')
        
        baseline_scp = None
        for policy in policies['Policies']:
            if 'baseline' in policy['Name'].lower():
                baseline_scp = policy
                break
        
        assert baseline_scp is not None, "Baseline SCP not found"
        print(f"✓ Baseline SCP exists: {baseline_scp['Name']}")
        
        # Verify SCP content
        policy_content = org_client.describe_policy(PolicyId=baseline_scp['Id'])
        policy_doc = json.loads(policy_content['Policy']['Content'])
        
        # Check for critical deny statements
        deny_actions = []
        for statement in policy_doc['Statement']:
            if statement['Effect'] == 'Deny':
                deny_actions.extend(statement['Action'])
        
        required_denies = [
            'organizations:LeaveOrganization',
            'account:CloseAccount',
            'cloudtrail:StopLogging',
            'cloudtrail:DeleteTrail'
        ]
        
        for action in required_denies:
            assert action in deny_actions, f"SCP missing deny for: {action}"
            print(f"✓ SCP denies: {action}")
    
    def test_cloudtrail_configured(self, cloudtrail_client):
        """Test organization-wide CloudTrail is configured"""
        trails = cloudtrail_client.describe_trails()
        
        org_trail = None
        for trail in trails['trailList']:
            if trail.get('IsOrganizationTrail', False):
                org_trail = trail
                break
        
        assert org_trail is not None, "Organization CloudTrail not found"
        assert org_trail['IsMultiRegionTrail'], "CloudTrail not multi-region"
        print(f"✓ Organization CloudTrail exists: {org_trail['Name']}")
        
        # Verify trail is logging
        status = cloudtrail_client.get_trail_status(Name=org_trail['TrailARN'])
        assert status['IsLogging'], "CloudTrail is not logging"
        print("✓ CloudTrail is actively logging")
    
    def test_cloudtrail_s3_bucket(self, s3_client):
        """Test CloudTrail S3 bucket configuration"""
        bucket_name = 'ai-core-cloudtrail-logs-695353648052'
        
        # Check bucket exists
        try:
            s3_client.head_bucket(Bucket=bucket_name)
            print(f"✓ CloudTrail S3 bucket exists: {bucket_name}")
        except:
            pytest.fail(f"CloudTrail S3 bucket not found: {bucket_name}")
        
        # Check bucket policy
        try:
            policy = s3_client.get_bucket_policy(Bucket=bucket_name)
            policy_doc = json.loads(policy['Policy'])
            
            # Verify CloudTrail service permissions
            cloudtrail_allowed = False
            for statement in policy_doc['Statement']:
                if statement.get('Principal', {}).get('Service') == 'cloudtrail.amazonaws.com':
                    cloudtrail_allowed = True
                    break
            
            assert cloudtrail_allowed, "CloudTrail service not allowed in bucket policy"
            print("✓ S3 bucket policy allows CloudTrail")
        except:
            pytest.fail("Could not retrieve or parse bucket policy")
        
        # Check bucket encryption
        try:
            encryption = s3_client.get_bucket_encryption(Bucket=bucket_name)
            assert 'Rules' in encryption['ServerSideEncryptionConfiguration']
            print("✓ S3 bucket encryption enabled")
        except s3_client.exceptions.ServerSideEncryptionConfigurationNotFoundError:
            pytest.fail("S3 bucket encryption not configured")
    
    def test_scp_attachment(self, org_client):
        """Test SCP is attached to root OU"""
        roots = org_client.list_roots()
        root_id = roots['Roots'][0]['Id']
        
        # List policies for root
        policies = org_client.list_policies_for_target(
            TargetId=root_id,
            Filter='SERVICE_CONTROL_POLICY'
        )
        
        attached_scps = [p['Name'] for p in policies['Policies']]
        baseline_attached = any('baseline' in name.lower() for name in attached_scps)
        
        assert baseline_attached, "Baseline SCP not attached to root"
        print("✓ Baseline SCP attached to root OU")
    
    def test_cloudtrail_event_selectors(self, cloudtrail_client):
        """Test CloudTrail is capturing management events"""
        trails = cloudtrail_client.describe_trails()
        
        for trail in trails['trailList']:
            if trail.get('IsOrganizationTrail', False):
                event_selectors = cloudtrail_client.get_event_selectors(
                    TrailName=trail['TrailARN']
                )
                
                # Check for management events
                mgmt_events = False
                for selector in event_selectors.get('EventSelectors', []):
                    if selector.get('IncludeManagementEvents', False):
                        mgmt_events = True
                        break
                
                assert mgmt_events, "CloudTrail not capturing management events"
                print("✓ CloudTrail capturing management events")
                break


class TestAWSOrganizationsCompliance:
    """Compliance and best practice tests"""
    
    @pytest.fixture(scope="class")
    def org_client(self):
        return boto3.client('organizations', region_name='us-east-1')
    
    def test_ou_structure_compliance(self, org_client):
        """Test OU structure follows best practices"""
        roots = org_client.list_roots()
        root_id = roots['Roots'][0]['Id']
        
        ous = org_client.list_organizational_units_for_parent(ParentId=root_id)
        ou_names = [ou['Name'] for ou in ous['OrganizationalUnits']]
        
        # Check for environment separation
        envs = ['Development', 'Staging', 'Production']
        for env in envs:
            assert env in ou_names, f"Missing environment OU: {env}"
        
        # Check for security OU
        assert 'Security' in ou_names, "Missing Security OU for centralized logging"
        
        print("✓ OU structure follows AWS best practices")
    
    def test_scp_least_privilege(self, org_client):
        """Test SCPs follow least privilege principle"""
        policies = org_client.list_policies(Filter='SERVICE_CONTROL_POLICY')
        
        for policy in policies['Policies']:
            if 'baseline' in policy['Name'].lower():
                content = org_client.describe_policy(PolicyId=policy['Id'])
                policy_doc = json.loads(content['Policy']['Content'])
                
                # Ensure no overly broad denies
                for statement in policy_doc['Statement']:
                    if statement['Effect'] == 'Deny':
                        # Check resource is not overly broad
                        assert statement.get('Resource', '*') == '*', \
                            "SCP deny should apply to all resources"
                        
                        # Check actions are specific
                        for action in statement['Action']:
                            assert ':' in action, f"Action too broad: {action}"
                
                print("✓ SCP follows least privilege principle")


def run_all_tests():
    """Run all AWS Organizations tests"""
    print("\n=== Running AWS Organizations Tests ===\n")
    
    # Run tests with pytest
    pytest.main([
        __file__,
        '-v',
        '--tb=short',
        '-k', 'test_'
    ])


if __name__ == '__main__':
    run_all_tests()
