#!/usr/bin/env python3
"""
Comprehensive test runner for AWS infrastructure (TASK-001 and TASK-002)
Executes all test suites and provides detailed reporting
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

class InfrastructureTestRunner:
    """Orchestrates running all infrastructure tests"""
    
    def __init__(self):
        self.test_results = {}
        self.start_time = datetime.now()
        self.test_dir = Path(__file__).parent
        
    def run_test_suite(self, test_file: str) -> Tuple[bool, Dict]:
        """Run a specific test suite and capture results"""
        print(f"\n{'='*60}")
        print(f"Running: {test_file}")
        print(f"{'='*60}\n")
        
        cmd = [
            sys.executable,
            "-m", "pytest",
            str(self.test_dir / test_file),
            "-v",
            "--tb=short",
            "--json-report",
            "--json-report-file=test_report.json"
        ]
        
        try:
            # Run tests
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.test_dir
            )
            
            # Parse results
            success = result.returncode == 0
            
            # Try to load JSON report
            report_data = {}
            report_file = self.test_dir / "test_report.json"
            if report_file.exists():
                with open(report_file, 'r') as f:
                    report_data = json.load(f)
                report_file.unlink()  # Clean up
            
            return success, {
                'success': success,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'report': report_data,
                'return_code': result.returncode
            }
            
        except Exception as e:
            return False, {
                'success': False,
                'error': str(e),
                'stdout': '',
                'stderr': str(e)
            }
    
    def run_all_tests(self):
        """Execute all infrastructure test suites"""
        test_suites = [
            'test_aws_organizations.py',
            'test_network_foundation.py'
        ]
        
        print("\n" + "="*80)
        print("AWS INFRASTRUCTURE COMPREHENSIVE TEST SUITE")
        print("="*80)
        print(f"\nStart Time: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Test Directory: {self.test_dir}")
        
        # Check AWS credentials
        print("\nChecking AWS credentials...")
        try:
            import boto3
            sts = boto3.client('sts')
            identity = sts.get_caller_identity()
            print(f"✓ AWS Account: {identity['Account']}")
            print(f"✓ AWS User ARN: {identity['Arn']}")
        except Exception as e:
            print(f"✗ AWS credentials check failed: {str(e)}")
            return
        
        # Run each test suite
        all_passed = True
        for test_file in test_suites:
            success, results = self.run_test_suite(test_file)
            self.test_results[test_file] = results
            
            if not success:
                all_passed = False
        
        # Generate summary report
        self.generate_summary_report(all_passed)
    
    def generate_summary_report(self, all_passed: bool):
        """Generate comprehensive test summary report"""
        end_time = datetime.now()
        duration = end_time - self.start_time
        
        print("\n" + "="*80)
        print("TEST EXECUTION SUMMARY")
        print("="*80)
        
        print(f"\nExecution Time: {duration.total_seconds():.2f} seconds")
        print(f"Overall Status: {'PASSED' if all_passed else 'FAILED'}")
        
        # Detailed results per suite
        print("\n" + "-"*60)
        print("Test Suite Results:")
        print("-"*60)
        
        total_tests = 0
        total_passed = 0
        total_failed = 0
        
        for test_file, results in self.test_results.items():
            status = "✓ PASSED" if results['success'] else "✗ FAILED"
            print(f"\n{test_file}: {status}")
            
            # Parse test counts from output
            if 'report' in results and results['report']:
                summary = results['report'].get('summary', {})
                passed = summary.get('passed', 0)
                failed = summary.get('failed', 0)
                total = summary.get('total', passed + failed)
                
                total_tests += total
                total_passed += passed
                total_failed += failed
                
                print(f"  Tests Run: {total}")
                print(f"  Passed: {passed}")
                print(f"  Failed: {failed}")
            
            # Show any errors
            if results.get('stderr'):
                print(f"  Errors: {results['stderr'][:200]}...")
        
        # Overall statistics
        print("\n" + "-"*60)
        print("Overall Statistics:")
        print("-"*60)
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {total_passed}")
        print(f"Failed: {total_failed}")
        if total_tests > 0:
            print(f"Success Rate: {(total_passed/total_tests)*100:.1f}%")
        
        # Write detailed report
        self.write_detailed_report()
        
        # Exit code
        sys.exit(0 if all_passed else 1)
    
    def write_detailed_report(self):
        """Write detailed test results to file"""
        report_path = self.test_dir / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        report_data = {
            'execution_time': str(datetime.now() - self.start_time),
            'start_time': self.start_time.isoformat(),
            'end_time': datetime.now().isoformat(),
            'test_results': self.test_results
        }
        
        with open(report_path, 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
        
        print(f"\nDetailed report written to: {report_path}")


class InfrastructureValidator:
    """Additional validation beyond unit tests"""
    
    @staticmethod
    def validate_terraform_state():
        """Validate Terraform state files if they exist"""
        print("\n" + "-"*60)
        print("Terraform State Validation:")
        print("-"*60)
        
        tf_dirs = [
            'infrastructure/aws-setup',
            'infrastructure/network/terraform'
        ]
        
        for tf_dir in tf_dirs:
            state_file = Path(tf_dir) / 'terraform.tfstate'
            if state_file.exists():
                print(f"✓ Found state: {state_file}")
                try:
                    with open(state_file, 'r') as f:
                        state = json.load(f)
                        resources = len(state.get('resources', []))
                        print(f"  Resources: {resources}")
                except Exception as e:
                    print(f"  ✗ Error reading state: {str(e)}")
            else:
                print(f"- No state found: {tf_dir}")
    
    @staticmethod
    def validate_configuration_files():
        """Validate configuration JSON files"""
        print("\n" + "-"*60)
        print("Configuration File Validation:")
        print("-"*60)
        
        config_files = [
            'infrastructure/network/existing-vpc-config.json',
            'infrastructure/network/database-subnets-config.json',
            'infrastructure/network/security-groups-config.json',
            'infrastructure/aws-setup/organization-config.json'
        ]
        
        for config_file in config_files:
            config_path = Path(config_file)
            if config_path.exists():
                try:
                    with open(config_path, 'r') as f:
                        data = json.load(f)
                        print(f"✓ Valid JSON: {config_file}")
                        print(f"  Keys: {', '.join(data.keys())}")
                except Exception as e:
                    print(f"✗ Invalid JSON: {config_file}")
                    print(f"  Error: {str(e)}")
            else:
                print(f"✗ Missing: {config_file}")


def main():
    """Main entry point for infrastructure testing"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║         AWS Infrastructure Comprehensive Test Suite           ║
║                                                              ║
║  Testing: TASK-001 (AWS Organizations)                       ║
║          TASK-002 (Network Foundation)                       ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Run tests
    runner = InfrastructureTestRunner()
    
    try:
        # Validate configurations first
        InfrastructureValidator.validate_configuration_files()
        InfrastructureValidator.validate_terraform_state()
        
        # Run all test suites
        runner.run_all_tests()
        
    except KeyboardInterrupt:
        print("\n\nTest execution interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
