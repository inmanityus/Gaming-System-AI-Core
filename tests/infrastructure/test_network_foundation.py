#!/usr/bin/env python3
"""
Comprehensive test suite for Network Foundation (TASK-002)
Tests VPC, subnets, security groups, routing, and high availability
"""

import pytest
import boto3
import ipaddress
from typing import Dict, List, Set

class TestNetworkFoundation:
    """Test suite for VPC and network infrastructure"""
    
    @pytest.fixture(scope="class")
    def ec2_client(self):
        """EC2 client for network testing"""
        return boto3.client('ec2', region_name='us-east-1')
    
    @pytest.fixture(scope="class")
    def rds_client(self):
        """RDS client for DB subnet group testing"""
        return boto3.client('rds', region_name='us-east-1')
    
    @pytest.fixture(scope="class")
    def vpc_id(self):
        """The VPC ID we're testing"""
        return 'vpc-0684c566fb7cc6b12'
    
    def test_vpc_configuration(self, ec2_client, vpc_id):
        """Test VPC exists with correct configuration"""
        vpcs = ec2_client.describe_vpcs(VpcIds=[vpc_id])
        assert len(vpcs['Vpcs']) == 1, "VPC not found"
        
        vpc = vpcs['Vpcs'][0]
        assert vpc['CidrBlock'] == '10.0.0.0/16', "Incorrect VPC CIDR"
        
        # Check DNS attributes separately as they're not included in describe_vpcs
        dns_hostnames = ec2_client.describe_vpc_attribute(
            VpcId=vpc_id,
            Attribute='enableDnsHostnames'
        )
        assert dns_hostnames['EnableDnsHostnames']['Value'] == True, "DNS hostnames not enabled"
        
        dns_support = ec2_client.describe_vpc_attribute(
            VpcId=vpc_id,
            Attribute='enableDnsSupport'
        )
        assert dns_support['EnableDnsSupport']['Value'] == True, "DNS support not enabled"
        
        print(f"✓ VPC configured correctly: {vpc_id}")
    
    def test_availability_zones(self, ec2_client, vpc_id):
        """Test resources span 3 availability zones"""
        subnets = ec2_client.describe_subnets(
            Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
        )
        
        azs = set()
        for subnet in subnets['Subnets']:
            azs.add(subnet['AvailabilityZone'])
        
        assert len(azs) >= 3, f"Not enough AZs: {azs}"
        print(f"✓ Resources span {len(azs)} availability zones: {sorted(azs)}")
    
    def test_subnet_configuration(self, ec2_client, vpc_id):
        """Test all subnet tiers exist with correct CIDR blocks"""
        subnets = ec2_client.describe_subnets(
            Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
        )
        
        # Expected subnet configurations
        expected_subnets = {
            'public': ['10.0.1.0/24', '10.0.2.0/24', '10.0.3.0/24'],
            'private': ['10.0.11.0/24', '10.0.12.0/24', '10.0.13.0/24'],
            'database': ['10.0.21.0/24', '10.0.22.0/24', '10.0.23.0/24']
        }
        
        actual_cidrs = {subnet['SubnetId']: subnet['CidrBlock'] 
                        for subnet in subnets['Subnets']}
        
        # Verify all expected subnets exist
        all_expected = []
        for tier, cidrs in expected_subnets.items():
            all_expected.extend(cidrs)
        
        for cidr in all_expected:
            assert cidr in actual_cidrs.values(), f"Missing subnet: {cidr}"
            print(f"✓ Subnet exists: {cidr}")
        
        # Test no overlapping CIDR blocks
        cidr_networks = [ipaddress.ip_network(cidr) for cidr in actual_cidrs.values()]
        for i, net1 in enumerate(cidr_networks):
            for net2 in cidr_networks[i+1:]:
                assert not net1.overlaps(net2), f"Overlapping subnets: {net1} and {net2}"
        
        print("✓ No overlapping subnet CIDR blocks")
    
    def test_internet_gateway(self, ec2_client, vpc_id):
        """Test Internet Gateway is attached"""
        igws = ec2_client.describe_internet_gateways(
            Filters=[
                {'Name': 'attachment.vpc-id', 'Values': [vpc_id]}
            ]
        )
        
        assert len(igws['InternetGateways']) > 0, "No Internet Gateway attached"
        igw = igws['InternetGateways'][0]
        
        # Verify attachment state
        attachments = igw['Attachments']
        assert len(attachments) > 0, "IGW not attached"
        assert attachments[0]['State'] == 'available', "IGW not available"
        
        print(f"✓ Internet Gateway attached: {igw['InternetGatewayId']}")
    
    def test_nat_gateways_high_availability(self, ec2_client, vpc_id):
        """Test NAT Gateways exist in each AZ for HA"""
        nats = ec2_client.describe_nat_gateways(
            Filters=[
                {'Name': 'vpc-id', 'Values': [vpc_id]},
                {'Name': 'state', 'Values': ['available']}
            ]
        )
        
        assert len(nats['NatGateways']) >= 3, "Not enough NAT Gateways for HA"
        
        # Verify NAT Gateway in each AZ
        nat_azs = set()
        for nat in nats['NatGateways']:
            subnet_id = nat['SubnetId']
            subnet = ec2_client.describe_subnets(SubnetIds=[subnet_id])
            nat_azs.add(subnet['Subnets'][0]['AvailabilityZone'])
        
        assert len(nat_azs) >= 3, f"NAT Gateways not distributed across AZs: {nat_azs}"
        print(f"✓ NAT Gateways in {len(nat_azs)} AZs for high availability")
    
    def test_route_tables(self, ec2_client, vpc_id):
        """Test route tables are correctly configured"""
        route_tables = ec2_client.describe_route_tables(
            Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
        )
        
        public_routes = 0
        private_routes = 0
        
        for rt in route_tables['RouteTables']:
            for route in rt['Routes']:
                # Check for IGW route (public)
                if route.get('GatewayId', '').startswith('igw-'):
                    public_routes += 1
                # Check for NAT route (private)
                elif route.get('NatGatewayId', '').startswith('nat-'):
                    private_routes += 1
        
        assert public_routes >= 1, "No public route to IGW"
        assert private_routes >= 3, "Not enough private routes through NAT"
        
        print(f"✓ Route tables configured: {public_routes} public, {private_routes} private")
    
    def test_security_groups(self, ec2_client, vpc_id):
        """Test all required security groups exist"""
        required_sgs = {
            'ai-core-production-alb-sg': {'ports': [80, 443], 'source': '0.0.0.0/0'},
            'ai-core-production-ecs-sg': {'from_sg': 'alb'},
            'ai-core-production-rds-sg': {'ports': [5432], 'from_sg': 'ecs'},
            'ai-core-production-elasticache-sg': {'ports': [6379], 'from_sg': 'ecs'},
            'ai-core-production-opensearch-sg': {'ports': [9200], 'from_sg': 'ecs'},
            'ai-core-production-bastion-sg': {'ports': [22]}
        }
        
        sgs = ec2_client.describe_security_groups(
            Filters=[
                {'Name': 'vpc-id', 'Values': [vpc_id]},
                {'Name': 'tag:Project', 'Values': ['AI-Core']}
            ]
        )
        
        sg_map = {sg['GroupName']: sg for sg in sgs['SecurityGroups']}
        
        for sg_name in required_sgs:
            assert sg_name in sg_map, f"Missing security group: {sg_name}"
            print(f"✓ Security group exists: {sg_name}")
    
    def test_security_group_rules(self, ec2_client, vpc_id):
        """Test security group rules follow least privilege"""
        sgs = ec2_client.describe_security_groups(
            Filters=[
                {'Name': 'vpc-id', 'Values': [vpc_id]},
                {'Name': 'tag:Project', 'Values': ['AI-Core']}
            ]
        )
        
        for sg in sgs['SecurityGroups']:
            # Check no overly permissive rules
            for rule in sg.get('IpPermissions', []):
                if rule.get('IpProtocol') == '-1':  # All protocols
                    # Should only be from security groups, not CIDR
                    assert len(rule.get('IpRanges', [])) == 0, \
                        f"Overly permissive rule in {sg['GroupName']}"
            
            print(f"✓ Security group {sg['GroupName']} follows least privilege")
    
    def test_db_subnet_group(self, rds_client):
        """Test RDS DB subnet group is configured"""
        try:
            response = rds_client.describe_db_subnet_groups(
                DBSubnetGroupName='ai-core-database-subnet-group'
            )
            
            assert len(response['DBSubnetGroups']) > 0, "DB subnet group not found"
            
            db_subnet_group = response['DBSubnetGroups'][0]
            assert db_subnet_group['SubnetGroupStatus'] == 'Complete'
            assert len(db_subnet_group['Subnets']) >= 3, "Not enough subnets in DB group"
            
            # Verify subnets span multiple AZs
            azs = {subnet['SubnetAvailabilityZone']['Name'] 
                   for subnet in db_subnet_group['Subnets']}
            assert len(azs) >= 3, f"DB subnets not in multiple AZs: {azs}"
            
            print(f"✓ DB subnet group configured with {len(azs)} AZs")
        except rds_client.exceptions.DBSubnetGroupNotFoundFault:
            pytest.fail("DB subnet group not found")


class TestNetworkSecurity:
    """Security-focused network tests"""
    
    @pytest.fixture(scope="class")
    def ec2_client(self):
        return boto3.client('ec2', region_name='us-east-1')
    
    @pytest.fixture(scope="class")
    def vpc_id(self):
        return 'vpc-0684c566fb7cc6b12'
    
    def test_no_default_security_group_rules(self, ec2_client, vpc_id):
        """Test default SG has no permissive rules"""
        sgs = ec2_client.describe_security_groups(
            Filters=[
                {'Name': 'vpc-id', 'Values': [vpc_id]},
                {'Name': 'group-name', 'Values': ['default']}
            ]
        )
        
        if sgs['SecurityGroups']:
            default_sg = sgs['SecurityGroups'][0]
            
            # Default SG should have minimal rules
            ingress_rules = default_sg.get('IpPermissions', [])
            
            for rule in ingress_rules:
                # Check no rules from 0.0.0.0/0
                ip_ranges = rule.get('IpRanges', [])
                for ip_range in ip_ranges:
                    assert ip_range['CidrIp'] != '0.0.0.0/0', \
                        "Default SG has permissive ingress from internet"
            
            print("✓ Default security group properly restricted")
    
    def test_private_subnets_no_public_ips(self, ec2_client, vpc_id):
        """Test private subnets don't auto-assign public IPs"""
        subnets = ec2_client.describe_subnets(
            Filters=[
                {'Name': 'vpc-id', 'Values': [vpc_id]},
                {'Name': 'tag:Type', 'Values': ['private', 'database']}
            ]
        )
        
        for subnet in subnets['Subnets']:
            assert not subnet.get('MapPublicIpOnLaunch', False), \
                f"Private subnet auto-assigns public IPs: {subnet['SubnetId']}"
        
        print("✓ Private subnets don't auto-assign public IPs")
    
    def test_network_acls(self, ec2_client, vpc_id):
        """Test Network ACLs are not overly permissive"""
        nacls = ec2_client.describe_network_acls(
            Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
        )
        
        for nacl in nacls['NetworkAcls']:
            # Check inbound rules
            for entry in nacl['Entries']:
                if not entry['Egress'] and entry['RuleAction'] == 'allow':
                    # Verify not allowing all traffic from anywhere
                    if entry['Protocol'] == '-1' and entry.get('CidrBlock') == '0.0.0.0/0':
                        # This is typically OK for default NACL, but flag custom ones
                        if not nacl['IsDefault']:
                            pytest.fail(f"Custom NACL allows all traffic: {nacl['NetworkAclId']}")
        
        print("✓ Network ACLs properly configured")


class TestHighAvailability:
    """High availability and resilience tests"""
    
    @pytest.fixture(scope="class")
    def ec2_client(self):
        return boto3.client('ec2', region_name='us-east-1')
    
    @pytest.fixture(scope="class") 
    def vpc_id(self):
        return 'vpc-0684c566fb7cc6b12'
    
    def test_multi_az_deployment(self, ec2_client, vpc_id):
        """Test resources are deployed across multiple AZs"""
        # Check subnets
        subnets = ec2_client.describe_subnets(
            Filters=[{'Name': 'vpc-id', 'Values': [vpc_id]}]
        )
        
        subnet_types = {}
        for subnet in subnets['Subnets']:
            tags = {tag['Key']: tag['Value'] for tag in subnet.get('Tags', [])}
            subnet_type = tags.get('Type', 'unknown')
            
            if subnet_type not in subnet_types:
                subnet_types[subnet_type] = set()
            subnet_types[subnet_type].add(subnet['AvailabilityZone'])
        
        # Each subnet type should span at least 3 AZs
        for subnet_type, azs in subnet_types.items():
            if subnet_type in ['public', 'private', 'database']:
                assert len(azs) >= 3, f"{subnet_type} subnets not in 3 AZs: {azs}"
                print(f"✓ {subnet_type} subnets span {len(azs)} AZs")
    
    def test_nat_gateway_redundancy(self, ec2_client, vpc_id):
        """Test NAT Gateways provide redundancy"""
        nats = ec2_client.describe_nat_gateways(
            Filters=[
                {'Name': 'vpc-id', 'Values': [vpc_id]},
                {'Name': 'state', 'Values': ['available']}
            ]
        )
        
        # Map NAT Gateways to their AZs
        nat_to_az = {}
        for nat in nats['NatGateways']:
            subnet = ec2_client.describe_subnets(
                SubnetIds=[nat['SubnetId']]
            )['Subnets'][0]
            nat_to_az[nat['NatGatewayId']] = subnet['AvailabilityZone']
        
        # Check each private subnet has a NAT in same AZ
        private_subnets = ec2_client.describe_subnets(
            Filters=[
                {'Name': 'vpc-id', 'Values': [vpc_id]},
                {'Name': 'tag:Type', 'Values': ['private', 'database']}
            ]
        )
        
        for subnet in private_subnets['Subnets']:
            subnet_az = subnet['AvailabilityZone']
            nat_in_az = any(az == subnet_az for az in nat_to_az.values())
            assert nat_in_az, f"No NAT Gateway in AZ: {subnet_az}"
        
        print("✓ NAT Gateways provide redundancy across all AZs")


def run_all_tests():
    """Run all network foundation tests"""
    print("\n=== Running Network Foundation Tests ===\n")
    
    # Run tests with pytest
    pytest.main([
        __file__,
        '-v',
        '--tb=short',
        '-k', 'test_'
    ])


if __name__ == '__main__':
    run_all_tests()
