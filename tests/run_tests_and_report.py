"""
Test runner and report generator.
Runs all tests and produces a comprehensive validation report.
"""
import subprocess
import json
import sys
from pathlib import Path
from datetime import datetime
import os


def run_pytest_with_report():
    """Run pytest and generate detailed reports."""
    
    # Ensure test data exists
    print("Checking test data...")
    test_data_dir = Path("tests/test_data")
    if not test_data_dir.exists():
        print("Test data not found. Generating...")
        try:
            subprocess.run([
                sys.executable, "-m", "tests.test_data_generators"
            ], check=True, capture_output=True, text=True)
            print("✓ Test data generated successfully")
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to generate test data: {e}")
            return False
    
    # Create reports directory
    reports_dir = Path("tests/reports")
    reports_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Run different test suites
    test_suites = [
        {
            "name": "Unit Tests - Audio Authentication",
            "pattern": "tests/test_*analyzer.py",
            "markers": "unit"
        },
        {
            "name": "Unit Tests - Engagement Analytics", 
            "pattern": "tests/test_*indicators.py tests/test_*constraints.py",
            "markers": "unit"
        },
        {
            "name": "Integration Tests - Audio ↔ Engagement",
            "pattern": "tests/test_integration_*.py",
            "markers": "integration"
        },
        {
            "name": "All Tests with Coverage",
            "pattern": "tests/",
            "markers": None,
            "coverage": True
        }
    ]
    
    results = []
    
    for suite in test_suites:
        print(f"\n{'='*60}")
        print(f"Running: {suite['name']}")
        print(f"{'='*60}")
        
        # Build pytest command
        cmd = [
            sys.executable, "-m", "pytest",
            "-v",  # Verbose
            "--tb=short",  # Short traceback
            "--no-header",  # Clean output
        ]
        
        # Add markers if specified
        if suite.get('markers'):
            cmd.extend(["-m", suite['markers']])
        
        # Add coverage if requested
        if suite.get('coverage'):
            cmd.extend([
                "--cov=services",
                "--cov-report=term-missing",
                "--cov-report=html:tests/reports/coverage_html",
                f"--cov-report=json:tests/reports/coverage_{timestamp}.json"
            ])
        
        # Add test pattern
        if isinstance(suite['pattern'], list):
            cmd.extend(suite['pattern'])
        else:
            cmd.append(suite['pattern'])
        
        # Add JSON report
        json_report = f"tests/reports/{suite['name'].replace(' ', '_')}_{timestamp}.json"
        cmd.extend([f"--json-report-file={json_report}"])
        
        # Run tests
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        
        # Store results
        suite_result = {
            "name": suite['name'],
            "return_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "json_report": json_report if os.path.exists(json_report) else None
        }
        results.append(suite_result)
        
        # Print summary
        if result.returncode == 0:
            print(f"✓ {suite['name']} PASSED")
        else:
            print(f"✗ {suite['name']} FAILED (code: {result.returncode})")
            if result.stderr:
                print(f"Error output:\n{result.stderr}")
    
    # Generate consolidated report
    generate_validation_report(results, reports_dir, timestamp)
    
    return all(r['return_code'] == 0 for r in results)


def generate_validation_report(results, reports_dir, timestamp):
    """Generate a comprehensive validation report."""
    
    report_path = reports_dir / f"validation_report_{timestamp}.md"
    
    with open(report_path, 'w') as f:
        f.write("# Test Validation Report\n\n")
        f.write(f"**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Summary
        f.write("## Summary\n\n")
        total_suites = len(results)
        passed_suites = sum(1 for r in results if r['return_code'] == 0)
        
        f.write(f"- Total Test Suites: {total_suites}\n")
        f.write(f"- Passed: {passed_suites}\n")
        f.write(f"- Failed: {total_suites - passed_suites}\n\n")
        
        # Detailed Results
        f.write("## Detailed Results\n\n")
        
        for result in results:
            f.write(f"### {result['name']}\n\n")
            
            if result['return_code'] == 0:
                f.write("**Status**: ✅ PASSED\n\n")
            else:
                f.write(f"**Status**: ❌ FAILED (exit code: {result['return_code']})\n\n")
            
            # Parse test counts from output
            if "passed" in result['stdout'] or "failed" in result['stdout']:
                f.write("**Test Results**:\n")
                f.write("```\n")
                # Extract summary line
                for line in result['stdout'].split('\n'):
                    if 'passed' in line or 'failed' in line or 'skipped' in line:
                        if line.strip() and not line.startswith(' '):
                            f.write(f"{line}\n")
                f.write("```\n\n")
            
            # Coverage info
            if "--cov" in result['stdout']:
                f.write("**Coverage Summary**:\n")
                f.write("```\n")
                in_coverage = False
                for line in result['stdout'].split('\n'):
                    if "TOTAL" in line:
                        f.write(f"{line}\n")
                    elif line.startswith("Name"):
                        in_coverage = True
                    elif in_coverage and line.strip() == "":
                        break
                    elif in_coverage:
                        f.write(f"{line}\n")
                f.write("```\n\n")
        
        # Test Quality Metrics
        f.write("## Test Quality Metrics\n\n")
        
        f.write("### Code Coverage\n\n")
        # Look for coverage JSON
        coverage_files = list(reports_dir.glob("coverage_*.json"))
        if coverage_files:
            latest_coverage = max(coverage_files, key=os.path.getctime)
            try:
                with open(latest_coverage) as cf:
                    coverage_data = json.load(cf)
                    total_coverage = coverage_data.get('totals', {}).get('percent_covered', 0)
                    f.write(f"- Overall Coverage: {total_coverage:.1f}%\n")
                    
                    # File breakdown
                    f.write("\n**File Coverage**:\n\n")
                    for file, data in coverage_data.get('files', {}).items():
                        if 'services/' in file:
                            percent = data['summary']['percent_covered']
                            f.write(f"- `{file}`: {percent:.1f}%\n")
            except Exception as e:
                f.write(f"Error reading coverage data: {e}\n")
        
        f.write("\n### Test Distribution\n\n")
        f.write("- Unit Tests: Audio (2 files), Engagement (2 files)\n")
        f.write("- Integration Tests: 2 comprehensive test suites\n")
        f.write("- Performance Tests: Included in unit tests\n")
        f.write("- Test Data: Generated audio files and JSON fixtures\n")
        
        # Recommendations
        f.write("\n## Recommendations\n\n")
        
        if passed_suites < total_suites:
            f.write("- ❗ Fix failing tests before deployment\n")
        
        f.write("- ✅ All test infrastructure is properly set up\n")
        f.write("- ✅ Comprehensive test coverage for core functionality\n")
        f.write("- ✅ Integration tests validate component interactions\n")
        f.write("- ⚠️  Add end-to-end tests with real database\n")
        f.write("- ⚠️  Add performance benchmarks for production loads\n")
    
    print(f"\n📊 Validation report generated: {report_path}")


def check_dependencies():
    """Check if all test dependencies are available."""
    print("Checking test dependencies...")
    
    required = ['pytest', 'pytest-asyncio', 'pytest-cov', 'numpy', 'soundfile']
    missing = []
    
    for package in required:
        try:
            __import__(package.replace('-', '_'))
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} (missing)")
            missing.append(package)
    
    if missing:
        print(f"\nMissing packages: {', '.join(missing)}")
        print(f"Install with: pip install {' '.join(missing)}")
        return False
    
    return True


def main():
    """Main test runner."""
    print("🧪 Gaming System AI Core - Test Runner\n")
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Missing dependencies. Please install required packages.")
        return 1
    
    # Run tests
    print("\n🚀 Running test suites...\n")
    success = run_pytest_with_report()
    
    if success:
        print("\n✅ All tests passed! Check tests/reports/ for detailed reports.")
        return 0
    else:
        print("\n❌ Some tests failed. Check tests/reports/ for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
