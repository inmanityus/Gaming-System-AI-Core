"""
Verify that all test infrastructure is properly set up.
This script checks that all components for testing are in place.
"""
import os
import sys
import subprocess
import json
import importlib
import importlib.metadata
from pathlib import Path
from typing import Dict, List, Tuple, Optional


def check_file_exists(file_path: str) -> Tuple[bool, str]:
    """Check if a file exists."""
    if Path(file_path).exists():
        return True, "[OK] Found"
    return False, "[FAIL] Missing"


def check_directory_exists(dir_path: str) -> Tuple[bool, str]:
    """Check if a directory exists."""
    path = Path(dir_path)
    if path.exists() and path.is_dir():
        file_count = len(list(path.rglob("*.py")))
        return True, f"[OK] Found ({file_count} Python files)"
    return False, "[FAIL] Missing"


def check_package_installed(
    package: str,
    import_name: Optional[str] = None,
    version_spec: Optional[str] = None
) -> Tuple[bool, str]:
    """Check if a Python package is installed and meets version requirements."""
    module_name = import_name or package
    
    try:
        importlib.import_module(module_name)
    except ImportError:
        return False, f"[FAIL] '{package}' not installed"
    
    # Version check (if needed for specific packages)
    if version_spec:
        try:
            from packaging.specifiers import SpecifierSet
            from packaging.version import Version
            installed_version_str = importlib.metadata.version(package)
            installed_version = Version(installed_version_str)
            spec = SpecifierSet(version_spec)
            if installed_version in spec:
                return True, f"[OK] '{package}' ({installed_version_str})"
            else:
                return False, f"[FAIL] '{package}' v{installed_version_str} (need {version_spec})"
        except Exception:
            return True, f"[OK] '{package}' installed"
    
    try:
        version = importlib.metadata.version(package)
        return True, f"[OK] '{package}' ({version})"
    except:
        return True, f"[OK] '{package}' installed"


def check_docker_running() -> Tuple[bool, str]:
    """Check if Docker is running."""
    try:
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            # Extract version for informative message
            docker_version = "unknown"
            for line in result.stdout.splitlines():
                if "Server Version:" in line:
                    docker_version = line.split(":")[-1].strip()
                    break
            return True, f"[OK] Running (v{docker_version})"
        else:
            # Show the actual error
            error_lines = result.stderr.strip().splitlines()
            error_msg = error_lines[-1] if error_lines else "Unknown error"
            # Truncate long error messages
            if len(error_msg) > 60:
                error_msg = error_msg[:57] + "..."
            return False, f"[FAIL] {error_msg}"
    except FileNotFoundError:
        return False, "[FAIL] Docker not found"
    except subprocess.TimeoutExpired:
        return False, "[FAIL] Docker timed out"


def check_postgres_connectivity() -> Tuple[bool, str]:
    """Check PostgreSQL connectivity."""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5443"),
            database=os.getenv("DB_NAME", "gaming_test"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "postgres"),
            connect_timeout=5
        )
        conn.close()
        return True, "[OK] Connected"
    except ImportError:
        return False, "[FAIL] psycopg2 not installed"
    except Exception as e:
        return False, f"[FAIL] Connection failed: {str(e)[:50]}"


def run_checks() -> Dict[str, List[Tuple[str, Tuple[bool, str]]]]:
    """Run all infrastructure checks."""
    checks = {
        "Core Test Files": [
            ("pytest.ini", check_file_exists("pytest.ini")),
            ("requirements-test.txt", check_file_exists("requirements-test.txt")),
            ("tests/conftest.py", check_file_exists("tests/conftest.py")),
            ("tests/conftest_full.py", check_file_exists("tests/conftest_full.py")),
        ],
        "Test Directories": [
            ("tests/unit", check_directory_exists("tests/unit")),
            ("tests/integration", check_directory_exists("tests/integration")),
            ("tests/performance", check_directory_exists("tests/performance")),
            ("tests/smoke", check_directory_exists("tests/smoke")),
        ],
        "Database Integration": [
            ("tests/integration/conftest_db.py", check_file_exists("tests/integration/conftest_db.py")),
            ("tests/integration/test_audio_metrics_db.py", check_file_exists("tests/integration/test_audio_metrics_db.py")),
            ("tests/integration/test_engagement_db.py", check_file_exists("tests/integration/test_engagement_db.py")),
            ("tests/integration/test_localization_db.py", check_file_exists("tests/integration/test_localization_db.py")),
            ("tests/integration/test_e2e_api_workflows.py", check_file_exists("tests/integration/test_e2e_api_workflows.py")),
        ],
        "Performance Testing": [
            ("tests/performance/test_audio_performance.py", check_file_exists("tests/performance/test_audio_performance.py")),
            ("tests/performance/locustfile.py", check_file_exists("tests/performance/locustfile.py")),
            ("tests/performance/run_performance_tests.py", check_file_exists("tests/performance/run_performance_tests.py")),
        ],
        "CI/CD Workflows": [
            (".github/workflows/ci.yml", check_file_exists(".github/workflows/ci.yml")),
            (".github/workflows/deploy.yml", check_file_exists(".github/workflows/deploy.yml")),
            (".github/workflows/database-migrations.yml", check_file_exists(".github/workflows/database-migrations.yml")),
            (".github/workflows/security.yml", check_file_exists(".github/workflows/security.yml")),
            (".github/workflows/release.yml", check_file_exists(".github/workflows/release.yml")),
            (".github/workflows/code-quality.yml", check_file_exists(".github/workflows/code-quality.yml")),
        ],
        "Helper Scripts": [
            ("scripts/validate_migrations.py", check_file_exists("scripts/validate_migrations.py")),
            ("scripts/generate_changelog.py", check_file_exists("scripts/generate_changelog.py")),
            ("scripts/check_license_compliance.py", check_file_exists("scripts/check_license_compliance.py")),
        ],
        "Python Packages": [
            ("pytest", check_package_installed("pytest")),
            ("pytest_asyncio", check_package_installed("pytest_asyncio")),
            ("pytest_cov", check_package_installed("pytest_cov")),
            ("pytest_benchmark", check_package_installed("pytest_benchmark")),
            ("locust", check_package_installed("locust")),
        ],
        "External Dependencies": [
            ("Docker", check_docker_running()),
            ("PostgreSQL", check_postgres_connectivity()),
        ],
    }
    
    return checks


def print_report(checks: Dict[str, List[Tuple[str, Tuple[bool, str]]]]):
    """Print the infrastructure check report."""
    print("=" * 70)
    print("TEST INFRASTRUCTURE VERIFICATION REPORT")
    print("=" * 70)
    
    total_checks = 0
    passed_checks = 0
    
    for category, items in checks.items():
        print(f"\n{category}:")
        print("-" * len(category))
        
        for name, (passed, message) in items:
            print(f"  {name:<50} {message}")
            total_checks += 1
            if passed:
                passed_checks += 1
    
    # Summary
    print("\n" + "=" * 70)
    print(f"SUMMARY: {passed_checks}/{total_checks} checks passed")
    
    success_rate = (passed_checks / total_checks * 100) if total_checks > 0 else 0
    
    if success_rate == 100:
        print("[SUCCESS] All test infrastructure is in place!")
    elif success_rate >= 80:
        print("[WARNING] Most infrastructure is ready, but some components are missing")
    else:
        print("[ERROR] Significant infrastructure components are missing")
    
    print("=" * 70)
    
    return passed_checks == total_checks


def suggest_fixes(checks: Dict[str, List[Tuple[str, Tuple[bool, str]]]]):
    """Suggest fixes for failed checks."""
    print("\nSUGGESTED FIXES:")
    print("=" * 70)
    
    has_failures = False
    
    for category, items in checks.items():
        failures = [(name, message) for name, (passed, message) in items if not passed]
        
        if failures:
            has_failures = True
            print(f"\n{category}:")
            
            for name, message in failures:
                if "not installed" in message.lower():
                    print(f"  - Install {name}: python -m pip install {name}")
                elif "missing" in message.lower():
                    if ".py" in name:
                        print(f"  - Missing file '{name}' - ensure you're in the project root")
                    else:
                        print(f"  - Create directory: mkdir -p {name}")
                elif "docker" in name.lower():
                    if "not found" in message.lower():
                        print(f"  - Install Docker: https://docs.docker.com/get-docker/")
                    elif "permission denied" in message.lower():
                        print(f"  - Fix permissions: sudo usermod -aG docker $USER && newgrp docker")
                    else:
                        print(f"  - Start Docker Desktop or: sudo systemctl start docker")
                elif "postgresql" in name.lower():
                    print(f"  - Start PostgreSQL on port 5443:")
                    print(f"    docker run -d --name postgres-test \\")
                    print(f"      -p 5443:5432 \\")
                    print(f"      -e POSTGRES_USER=postgres \\")
                    print(f"      -e POSTGRES_PASSWORD=postgres \\")
                    print(f"      -e POSTGRES_DB=gaming_test \\")
                    print(f"      postgres:15-alpine")
    
    if not has_failures:
        print("\nNo fixes needed - everything looks good!")


def main():
    """Main function."""
    print("Verifying test infrastructure...")
    
    # Run all checks
    checks = run_checks()
    
    # Print report
    all_passed = print_report(checks)
    
    # Suggest fixes if needed
    if not all_passed:
        suggest_fixes(checks)
    
    # Return appropriate exit code
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()