"""
Comprehensive test runner for the Gaming System AI Core.
Runs all test suites and generates a unified report.
"""
import subprocess
import sys
import os
import time
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple


class TestRunner:
    """Orchestrates running all test suites."""
    
    def __init__(self, report_dir: str = "test-reports"):
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results = {}
    
    def run_unit_tests(self, coverage: bool = True) -> Dict:
        """Run unit tests."""
        print("\n" + "="*60)
        print("RUNNING UNIT TESTS")
        print("="*60)
        
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/unit",
            "-v",
            "-m", "not integration and not e2e and not performance",
            f"--junit-xml={self.report_dir}/unit-results-{self.timestamp}.xml"
        ]
        
        if coverage:
            cmd.extend([
                "--cov=services",
                f"--cov-report=html:{self.report_dir}/coverage-unit-{self.timestamp}",
                "--cov-report=term"
            ])
        
        result = self._run_command(cmd, "Unit Tests")
        self.results["unit"] = result
        return result
    
    def run_integration_tests(self, coverage: bool = True) -> Dict:
        """Run integration tests."""
        print("\n" + "="*60)
        print("RUNNING INTEGRATION TESTS")
        print("="*60)
        
        # Check if PostgreSQL is running
        if not self._check_postgres():
            print("WARNING: PostgreSQL not available on port 5443")
            print("Skipping database integration tests")
            return {"status": "skipped", "reason": "PostgreSQL not available"}
        
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/integration",
            "-v",
            "-m", "integration",
            f"--junit-xml={self.report_dir}/integration-results-{self.timestamp}.xml"
        ]
        
        if coverage:
            cmd.extend([
                "--cov=services",
                "--cov-append",  # Append to existing coverage
                f"--cov-report=html:{self.report_dir}/coverage-integration-{self.timestamp}",
                "--cov-report=term"
            ])
        
        result = self._run_command(cmd, "Integration Tests", env={
            "DB_HOST": "localhost",
            "DB_PORT": "5443",
            "DB_NAME": "gaming_test",
            "DB_USER": "postgres",
            "DB_PASSWORD": "postgres"
        })
        
        self.results["integration"] = result
        return result
    
    def run_e2e_tests(self) -> Dict:
        """Run end-to-end tests."""
        print("\n" + "="*60)
        print("RUNNING E2E TESTS")
        print("="*60)
        
        # Check if services are running
        if not self._check_services():
            print("WARNING: Services not running")
            print("Skipping E2E tests")
            return {"status": "skipped", "reason": "Services not running"}
        
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/integration",
            "-v",
            "-m", "e2e",
            f"--junit-xml={self.report_dir}/e2e-results-{self.timestamp}.xml"
        ]
        
        result = self._run_command(cmd, "E2E Tests")
        self.results["e2e"] = result
        return result
    
    def run_performance_tests(self) -> Dict:
        """Run performance tests."""
        print("\n" + "="*60)
        print("RUNNING PERFORMANCE TESTS")
        print("="*60)
        
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/performance",
            "-v",
            "-m", "performance",
            "--benchmark-only",
            f"--benchmark-json={self.report_dir}/benchmark-{self.timestamp}.json",
            f"--junit-xml={self.report_dir}/performance-results-{self.timestamp}.xml"
        ]
        
        result = self._run_command(cmd, "Performance Tests")
        self.results["performance"] = result
        return result
    
    def run_smoke_tests(self, endpoint: str = "http://localhost:8000") -> Dict:
        """Run smoke tests."""
        print("\n" + "="*60)
        print("RUNNING SMOKE TESTS")
        print("="*60)
        
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/smoke",
            "-v",
            "-m", "smoke",
            f"--api-endpoint={endpoint}",
            f"--junit-xml={self.report_dir}/smoke-results-{self.timestamp}.xml"
        ]
        
        result = self._run_command(cmd, "Smoke Tests")
        self.results["smoke"] = result
        return result
    
    def run_security_checks(self) -> Dict:
        """Run security checks."""
        print("\n" + "="*60)
        print("RUNNING SECURITY CHECKS")
        print("="*60)
        
        results = {}
        
        # Run bandit
        print("Running Bandit security scan...")
        cmd = [sys.executable, "-m", "bandit", "-r", "services", "-f", "json"]
        bandit_result = self._run_command(cmd, "Bandit", capture_output=True)
        
        if bandit_result["stdout"]:
            try:
                bandit_data = json.loads(bandit_result["stdout"])
                results["bandit"] = {
                    "issues": len(bandit_data.get("results", [])),
                    "severity": bandit_data.get("metrics", {})
                }
            except:
                results["bandit"] = {"error": "Failed to parse results"}
        
        # Run safety check
        print("Running Safety dependency check...")
        cmd = [sys.executable, "-m", "safety", "check", "--json"]
        safety_result = self._run_command(cmd, "Safety", capture_output=True)
        
        if safety_result["stdout"]:
            try:
                safety_data = json.loads(safety_result["stdout"])
                results["safety"] = {
                    "vulnerabilities": len(safety_data)
                }
            except:
                results["safety"] = {"error": "Failed to parse results"}
        
        self.results["security"] = results
        return results
    
    def run_code_quality_checks(self) -> Dict:
        """Run code quality checks."""
        print("\n" + "="*60)
        print("RUNNING CODE QUALITY CHECKS")
        print("="*60)
        
        results = {}
        
        # Black formatting check
        print("Checking code formatting with Black...")
        cmd = [sys.executable, "-m", "black", "--check", "services", "tests"]
        black_result = self._run_command(cmd, "Black", capture_stderr=True)
        results["black"] = {
            "passed": black_result["returncode"] == 0,
            "files_to_reformat": black_result["stderr"].count("would reformat")
        }
        
        # Flake8 linting
        print("Running Flake8 linting...")
        cmd = [
            sys.executable, "-m", "flake8",
            "services", "tests",
            "--count",
            "--statistics"
        ]
        flake8_result = self._run_command(cmd, "Flake8", capture_output=True)
        results["flake8"] = {
            "passed": flake8_result["returncode"] == 0,
            "issues": flake8_result["stdout"].count("\n") if flake8_result["stdout"] else 0
        }
        
        # MyPy type checking
        print("Running MyPy type checking...")
        cmd = [
            sys.executable, "-m", "mypy",
            "services",
            "--ignore-missing-imports"
        ]
        mypy_result = self._run_command(cmd, "MyPy", capture_output=True)
        results["mypy"] = {
            "passed": mypy_result["returncode"] == 0,
            "errors": mypy_result["stdout"].count("error:") if mypy_result["stdout"] else 0
        }
        
        self.results["quality"] = results
        return results
    
    def generate_report(self):
        """Generate comprehensive test report."""
        print("\n" + "="*60)
        print("GENERATING TEST REPORT")
        print("="*60)
        
        report = {
            "timestamp": self.timestamp,
            "summary": self._generate_summary(),
            "results": self.results
        }
        
        # Save JSON report
        report_file = self.report_dir / f"test-report-{self.timestamp}.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=2, default=str)
        
        # Generate HTML report
        self._generate_html_report(report)
        
        # Print summary
        self._print_summary(report["summary"])
        
        return report_file
    
    def _run_command(
        self,
        cmd: List[str],
        name: str,
        env: Optional[Dict] = None,
        capture_output: bool = False,
        capture_stderr: bool = False,
        timeout: int = 1800  # 30 minutes default timeout
    ) -> Dict:
        """Run a command and capture results."""
        start_time = time.time()
        
        # Set up environment
        cmd_env = os.environ.copy()
        if env:
            cmd_env.update(env)
        
        # Always capture output for diagnostics
        stdout_capture = subprocess.PIPE
        stderr_capture = subprocess.PIPE
        
        # Run command
        try:
            result = subprocess.run(
                cmd,
                env=cmd_env,
                stdout=stdout_capture,
                stderr=stderr_capture,
                text=True,
                timeout=timeout
            )
            
            # Determine status based on return code
            status = "completed" if result.returncode == 0 else "failed"
            
            return {
                "status": status,
                "returncode": result.returncode,
                "duration": time.time() - start_time,
                "stdout": result.stdout if capture_output or result.returncode != 0 else None,
                "stderr": result.stderr if capture_stderr or capture_output or result.returncode != 0 else None
            }
        except subprocess.TimeoutExpired as e:
            # Kill the process if it times out
            if e.stdout:
                stdout = e.stdout.decode('utf-8', errors='replace')
            else:
                stdout = ""
            if e.stderr:
                stderr = e.stderr.decode('utf-8', errors='replace')  
            else:
                stderr = ""
                
            return {
                "status": "timeout",
                "error": f"Command timed out after {timeout} seconds",
                "duration": timeout,
                "stdout": stdout,
                "stderr": stderr
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "duration": time.time() - start_time,
                "stdout": None,
                "stderr": None
            }
    
    def _check_postgres(self) -> bool:
        """Check if PostgreSQL is available."""
        try:
            import psycopg2
        except ImportError:
            print("WARNING: psycopg2 not installed. Cannot check PostgreSQL connectivity.")
            return False
            
        try:
            conn = psycopg2.connect(
                host="localhost",
                port="5443",
                database="gaming_test",
                user="postgres",
                password="postgres",
                connect_timeout=5
            )
            conn.close()
            return True
        except psycopg2.OperationalError as e:
            print(f"PostgreSQL connection failed: {str(e)[:100]}")
            return False
        except Exception as e:
            print(f"Unexpected error checking PostgreSQL: {type(e).__name__}: {str(e)[:100]}")
            return False
    
    def _check_services(self) -> bool:
        """Check if services are running."""
        try:
            import requests
            response = requests.get("http://localhost:8000/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def _generate_summary(self) -> Dict:
        """Generate test summary."""
        summary = {
            "total_suites": len(self.results),
            "passed_suites": 0,
            "failed_suites": 0,
            "skipped_suites": 0,
            "error_suites": 0,
            "timeout_suites": 0,
            "total_duration": 0
        }
        
        for suite, result in self.results.items():
            if isinstance(result, dict):
                status = result.get("status")
                
                if status == "skipped":
                    summary["skipped_suites"] += 1
                elif status == "completed" and result.get("returncode") == 0:
                    summary["passed_suites"] += 1
                elif status == "failed" or (status == "completed" and result.get("returncode") != 0):
                    summary["failed_suites"] += 1
                elif status == "timeout":
                    summary["timeout_suites"] += 1
                elif status == "error":
                    summary["error_suites"] += 1
                
                if "duration" in result:
                    summary["total_duration"] += result["duration"]
        
        summary["success_rate"] = (
            summary["passed_suites"] / summary["total_suites"] * 100
            if summary["total_suites"] > 0 else 0
        )
        
        return summary
    
    def _generate_html_report(self, report: Dict):
        """Generate HTML test report."""
        html_file = self.report_dir / f"test-report-{self.timestamp}.html"
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Test Report - {self.timestamp}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1, h2, h3 {{ color: #333; }}
        .summary {{ background: #f0f0f0; padding: 20px; border-radius: 5px; margin: 20px 0; }}
        .passed {{ color: #4CAF50; font-weight: bold; }}
        .failed {{ color: #f44336; font-weight: bold; }}
        .skipped {{ color: #ff9800; font-weight: bold; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        .metric {{ background: #e3f2fd; padding: 10px; margin: 10px 0; border-radius: 3px; }}
    </style>
</head>
<body>
    <h1>Test Report</h1>
    <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    
    <div class="summary">
        <h2>Summary</h2>
        <p>Total Suites: {report['summary']['total_suites']}</p>
        <p class="passed">Passed: {report['summary']['passed_suites']}</p>
        <p class="failed">Failed: {report['summary']['failed_suites']}</p>
        <p class="skipped">Skipped: {report['summary']['skipped_suites']}</p>
        <p>Success Rate: {report['summary']['success_rate']:.1f}%</p>
        <p>Total Duration: {report['summary']['total_duration']:.2f} seconds</p>
    </div>
    
    <h2>Test Results</h2>
    {self._generate_results_html(report['results'])}
    
    <h2>Artifacts</h2>
    <p>Test reports and coverage data saved to: {self.report_dir}</p>
</body>
</html>
        """
        
        with open(html_file, 'w') as f:
            f.write(html_content)
    
    def _generate_results_html(self, results: Dict) -> str:
        """Generate HTML for test results."""
        html = "<table>"
        html += "<tr><th>Test Suite</th><th>Status</th><th>Details</th></tr>"
        
        for suite, result in results.items():
            if isinstance(result, dict):
                status = "Passed" if result.get("returncode") == 0 else "Failed"
                if result.get("status") == "skipped":
                    status = "Skipped"
                
                status_class = status.lower()
                details = ""
                
                if "duration" in result:
                    details += f"Duration: {result['duration']:.2f}s"
                if "reason" in result:
                    details += f", Reason: {result['reason']}"
                
                html += f"<tr><td>{suite.title()}</td><td class='{status_class}'>{status}</td><td>{details}</td></tr>"
        
        html += "</table>"
        return html
    
    def _print_summary(self, summary: Dict):
        """Print test summary to console."""
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"Total Suites: {summary['total_suites']}")
        print(f"Passed: {summary['passed_suites']}")
        print(f"Failed: {summary['failed_suites']}")
        print(f"Skipped: {summary['skipped_suites']}")
        print(f"Success Rate: {summary['success_rate']:.1f}%")
        print(f"Total Duration: {summary['total_duration']:.2f} seconds")
        print("="*60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Run all test suites")
    parser.add_argument(
        "--suites",
        nargs="+",
        choices=["unit", "integration", "e2e", "performance", "smoke", "security", "quality", "all"],
        default=["all"],
        help="Which test suites to run"
    )
    parser.add_argument(
        "--no-coverage",
        action="store_true",
        help="Skip coverage reporting"
    )
    parser.add_argument(
        "--report-dir",
        default="test-reports",
        help="Directory for test reports"
    )
    parser.add_argument(
        "--api-endpoint",
        default="http://localhost:8000",
        help="API endpoint for smoke tests"
    )
    
    args = parser.parse_args()
    
    # Create test runner
    runner = TestRunner(report_dir=args.report_dir)
    
    # Determine which suites to run
    if "all" in args.suites:
        suites = ["unit", "integration", "e2e", "performance", "smoke", "security", "quality"]
    else:
        suites = args.suites
    
    # Run selected suites
    try:
        if "unit" in suites:
            runner.run_unit_tests(coverage=not args.no_coverage)
        
        if "integration" in suites:
            runner.run_integration_tests(coverage=not args.no_coverage)
        
        if "e2e" in suites:
            runner.run_e2e_tests()
        
        if "performance" in suites:
            runner.run_performance_tests()
        
        if "smoke" in suites:
            runner.run_smoke_tests(endpoint=args.api_endpoint)
        
        if "security" in suites:
            runner.run_security_checks()
        
        if "quality" in suites:
            runner.run_code_quality_checks()
        
        # Generate report
        report_file = runner.generate_report()
        print(f"\nFull report saved to: {report_file}")
        
        # Exit with appropriate code
        if runner.results:
            failed_suites = sum(
                1 for r in runner.results.values()
                if isinstance(r, dict) and r.get("returncode", 0) != 0
            )
            sys.exit(1 if failed_suites > 0 else 0)
        
    except KeyboardInterrupt:
        print("\n\nTest run interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError running tests: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
