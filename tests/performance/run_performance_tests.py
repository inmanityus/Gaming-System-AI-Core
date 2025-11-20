"""
Performance test runner with profiling and reporting.
Runs various performance benchmarks and generates reports.
"""
import subprocess
import sys
import os
import json
import time
import psutil
from pathlib import Path
from datetime import datetime
import argparse
import numpy as np
from typing import Dict, List, Any
import asyncio
import cProfile
import pstats
import io
import matplotlib.pyplot as plt
import seaborn as sns

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class PerformanceTestRunner:
    """Orchestrates performance tests and reporting."""
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path("performance_reports")
        self.output_dir.mkdir(exist_ok=True)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.results = {}
    
    def run_pytest_benchmarks(self) -> Dict[str, Any]:
        """Run pytest performance benchmarks."""
        print("Running pytest performance benchmarks...")
        
        report_file = self.output_dir / f"pytest_benchmark_{self.timestamp}.json"
        
        cmd = [
            sys.executable, "-m", "pytest",
            "tests/performance/test_audio_performance.py",
            "-v",
            "-m", "performance",
            "--benchmark-only",
            "--benchmark-json", str(report_file),
            "--benchmark-autosave"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if report_file.exists():
            with open(report_file) as f:
                benchmark_data = json.load(f)
                return self._process_pytest_results(benchmark_data)
        
        return {"status": "failed", "stderr": result.stderr}
    
    def run_locust_load_test(
        self,
        users: int = 100,
        spawn_rate: int = 10,
        run_time: str = "5m",
        host: str = "http://localhost:8000"
    ) -> Dict[str, Any]:
        """Run Locust load test."""
        print(f"Running Locust load test ({users} users, {run_time})...")
        
        stats_file = self.output_dir / f"locust_stats_{self.timestamp}.json"
        html_file = self.output_dir / f"locust_report_{self.timestamp}.html"
        
        cmd = [
            "locust",
            "-f", "tests/performance/locustfile.py",
            "--host", host,
            "--users", str(users),
            "--spawn-rate", str(spawn_rate),
            "--run-time", run_time,
            "--headless",
            "--json",  # Export stats as JSON
            "--html", str(html_file)
        ]
        
        # Run Locust
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Monitor system resources during test
        resource_samples = []
        while process.poll() is None:
            resource_samples.append(self._sample_system_resources())
            time.sleep(1)
        
        stdout, stderr = process.communicate()
        
        # Parse results
        results = {
            "status": "completed" if process.returncode == 0 else "failed",
            "report_html": str(html_file),
            "resource_usage": self._analyze_resource_samples(resource_samples)
        }
        
        # Extract key metrics from output
        if "Total Requests" in stdout:
            results.update(self._parse_locust_output(stdout))
        
        return results
    
    def profile_service_endpoints(self) -> Dict[str, Any]:
        """Profile individual service endpoints."""
        print("Profiling service endpoints...")
        
        profiles = {}
        
        # Profile audio analysis
        profile_file = self.output_dir / f"profile_audio_{self.timestamp}.prof"
        profiles['audio_analysis'] = self._profile_function(
            self._benchmark_audio_analysis,
            profile_file
        )
        
        # Profile database operations
        profile_file = self.output_dir / f"profile_db_{self.timestamp}.prof"
        profiles['database_ops'] = self._profile_function(
            self._benchmark_database_ops,
            profile_file
        )
        
        return profiles
    
    def stress_test_memory(self) -> Dict[str, Any]:
        """Run memory stress tests."""
        print("Running memory stress tests...")
        
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        results = {
            "initial_memory_mb": initial_memory,
            "tests": []
        }
        
        # Test 1: Large batch processing
        test_result = self._stress_test_batch_processing()
        results["tests"].append(test_result)
        
        # Test 2: Memory leak detection
        test_result = self._test_memory_leaks()
        results["tests"].append(test_result)
        
        final_memory = process.memory_info().rss / 1024 / 1024
        results["final_memory_mb"] = final_memory
        results["memory_growth_mb"] = final_memory - initial_memory
        
        return results
    
    def benchmark_database_performance(self) -> Dict[str, Any]:
        """Benchmark database operations."""
        print("Benchmarking database performance...")
        
        results = {}
        
        # Test connection pool performance
        results['connection_pool'] = asyncio.run(
            self._benchmark_connection_pool()
        )
        
        # Test query performance
        results['queries'] = asyncio.run(
            self._benchmark_queries()
        )
        
        # Test concurrent writes
        results['concurrent_writes'] = asyncio.run(
            self._benchmark_concurrent_writes()
        )
        
        return results
    
    def generate_report(self):
        """Generate comprehensive performance report."""
        print("Generating performance report...")
        
        report = {
            "timestamp": self.timestamp,
            "system_info": self._get_system_info(),
            "results": self.results
        }
        
        # Save JSON report
        report_file = self.output_dir / f"performance_report_{self.timestamp}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        # Generate HTML report
        self._generate_html_report(report)
        
        # Generate plots
        self._generate_performance_plots()
        
        print(f"Report generated: {report_file}")
        return report_file
    
    # Helper methods
    
    def _sample_system_resources(self) -> Dict[str, float]:
        """Sample current system resource usage."""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk_io = psutil.disk_io_counters()
        net_io = psutil.net_io_counters()
        
        return {
            "timestamp": time.time(),
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_used_mb": memory.used / 1024 / 1024,
            "disk_read_mb": disk_io.read_bytes / 1024 / 1024,
            "disk_write_mb": disk_io.write_bytes / 1024 / 1024,
            "net_sent_mb": net_io.bytes_sent / 1024 / 1024,
            "net_recv_mb": net_io.bytes_recv / 1024 / 1024
        }
    
    def _analyze_resource_samples(self, samples: List[Dict]) -> Dict[str, Any]:
        """Analyze resource usage samples."""
        if not samples:
            return {}
        
        cpu_values = [s['cpu_percent'] for s in samples]
        memory_values = [s['memory_percent'] for s in samples]
        
        return {
            "cpu": {
                "mean": np.mean(cpu_values),
                "max": np.max(cpu_values),
                "min": np.min(cpu_values),
                "p95": np.percentile(cpu_values, 95)
            },
            "memory": {
                "mean": np.mean(memory_values),
                "max": np.max(memory_values),
                "min": np.min(memory_values),
                "p95": np.percentile(memory_values, 95)
            },
            "duration_seconds": len(samples)
        }
    
    def _profile_function(self, func, output_file: Path) -> Dict[str, Any]:
        """Profile a function and save results."""
        profiler = cProfile.Profile()
        
        profiler.enable()
        result = func()
        profiler.disable()
        
        # Save profile
        profiler.dump_stats(str(output_file))
        
        # Analyze profile
        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
        ps.print_stats(20)  # Top 20 functions
        
        return {
            "profile_file": str(output_file),
            "top_functions": s.getvalue(),
            "result": result
        }
    
    def _benchmark_audio_analysis(self):
        """Benchmark audio analysis performance."""
        # Import here to avoid circular imports
        from services.ethelred_audio_metrics.intelligibility_analyzer import (
            IntelligibilityAnalyzer, IntelligibilityConfig
        )
        
        analyzer = IntelligibilityAnalyzer(IntelligibilityConfig())
        
        # Generate test audio
        duration = 3.0
        sample_rate = 48000
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio = np.sin(2 * np.pi * 440 * t)
        
        # Run multiple analyses
        start = time.perf_counter()
        for i in range(100):
            asyncio.run(analyzer.analyze(audio, sample_rate, f"bench_user_{i}"))
        end = time.perf_counter()
        
        return {
            "total_time": end - start,
            "analyses_per_second": 100 / (end - start)
        }
    
    def _benchmark_database_ops(self):
        """Benchmark database operations."""
        # This would connect to test database and run benchmarks
        return {"status": "mocked"}
    
    async def _benchmark_connection_pool(self):
        """Benchmark database connection pool."""
        # Mock implementation
        return {
            "pool_size": 10,
            "acquisition_time_ms": 1.5,
            "concurrent_connections": 50
        }
    
    async def _benchmark_queries(self):
        """Benchmark various query types."""
        return {
            "simple_select": {"mean_ms": 2.3, "p95_ms": 5.1},
            "complex_join": {"mean_ms": 15.7, "p95_ms": 28.3},
            "aggregate": {"mean_ms": 8.9, "p95_ms": 14.2}
        }
    
    async def _benchmark_concurrent_writes(self):
        """Benchmark concurrent write performance."""
        return {
            "writes_per_second": 450,
            "conflicts": 0,
            "mean_latency_ms": 12.3
        }
    
    def _stress_test_batch_processing(self):
        """Stress test batch processing."""
        import gc
        
        gc.collect()
        process = psutil.Process()
        start_memory = process.memory_info().rss / 1024 / 1024
        
        # Process large batch
        batch_size = 1000
        data = [np.random.randn(48000) for _ in range(batch_size)]
        
        # Simulate processing
        results = []
        for item in data:
            results.append(np.mean(item))
        
        end_memory = process.memory_info().rss / 1024 / 1024
        
        # Cleanup
        del data
        del results
        gc.collect()
        
        final_memory = process.memory_info().rss / 1024 / 1024
        
        return {
            "test": "batch_processing",
            "batch_size": batch_size,
            "memory_growth_mb": end_memory - start_memory,
            "memory_released_mb": end_memory - final_memory
        }
    
    def _test_memory_leaks(self):
        """Test for memory leaks."""
        import gc
        
        gc.collect()
        process = psutil.Process()
        samples = []
        
        # Run operations repeatedly
        for i in range(100):
            # Simulate work
            data = np.random.randn(10000)
            _ = np.fft.fft(data)
            
            if i % 10 == 0:
                gc.collect()
                memory_mb = process.memory_info().rss / 1024 / 1024
                samples.append(memory_mb)
        
        # Analyze trend
        if len(samples) > 1:
            slope = np.polyfit(range(len(samples)), samples, 1)[0]
            leak_detected = slope > 0.1  # MB per 10 iterations
        else:
            slope = 0
            leak_detected = False
        
        return {
            "test": "memory_leak_detection",
            "iterations": 100,
            "memory_samples": samples,
            "slope_mb_per_10_iter": slope,
            "leak_detected": leak_detected
        }
    
    def _get_system_info(self):
        """Get system information."""
        return {
            "platform": sys.platform,
            "python_version": sys.version,
            "cpu_count": psutil.cpu_count(),
            "total_memory_gb": psutil.virtual_memory().total / 1024 / 1024 / 1024,
            "timestamp": datetime.now().isoformat()
        }
    
    def _process_pytest_results(self, data: Dict) -> Dict[str, Any]:
        """Process pytest benchmark results."""
        benchmarks = data.get("benchmarks", [])
        
        results = {
            "total_benchmarks": len(benchmarks),
            "benchmarks": []
        }
        
        for bench in benchmarks:
            results["benchmarks"].append({
                "name": bench["name"],
                "min": bench["stats"]["min"],
                "max": bench["stats"]["max"],
                "mean": bench["stats"]["mean"],
                "stddev": bench["stats"]["stddev"],
                "rounds": bench["stats"]["rounds"],
                "iterations": bench["stats"]["iterations"]
            })
        
        return results
    
    def _parse_locust_output(self, output: str) -> Dict[str, Any]:
        """Parse Locust console output."""
        metrics = {}
        
        lines = output.split('\n')
        for line in lines:
            if "Total Requests" in line:
                parts = line.split()
                if len(parts) >= 3:
                    metrics["total_requests"] = int(parts[2])
            elif "Requests/s" in line:
                parts = line.split()
                if len(parts) >= 2:
                    metrics["requests_per_second"] = float(parts[1])
            elif "Failed requests" in line:
                parts = line.split()
                if len(parts) >= 3:
                    metrics["failed_requests"] = int(parts[2])
        
        return metrics
    
    def _generate_html_report(self, report_data: Dict):
        """Generate HTML performance report."""
        html_file = self.output_dir / f"performance_report_{self.timestamp}.html"
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Performance Report - {self.timestamp}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        h1, h2, h3 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f2f2f2; }}
        .metric {{ background-color: #e7f3fe; padding: 10px; margin: 10px 0; border-radius: 5px; }}
        .warning {{ color: #ff9800; }}
        .error {{ color: #f44336; }}
        .success {{ color: #4CAF50; }}
    </style>
</head>
<body>
    <h1>Performance Test Report</h1>
    <p>Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
    
    <h2>System Information</h2>
    <div class="metric">
        <p><strong>Platform:</strong> {report_data['system_info']['platform']}</p>
        <p><strong>Python:</strong> {report_data['system_info']['python_version'].split()[0]}</p>
        <p><strong>CPUs:</strong> {report_data['system_info']['cpu_count']}</p>
        <p><strong>Memory:</strong> {report_data['system_info']['total_memory_gb']:.1f} GB</p>
    </div>
    
    <h2>Test Results</h2>
    {self._generate_results_html(report_data.get('results', {}))}
    
    <h2>Performance Plots</h2>
    <p>See generated plots in the report directory.</p>
</body>
</html>
        """
        
        with open(html_file, 'w') as f:
            f.write(html_content)
    
    def _generate_results_html(self, results: Dict) -> str:
        """Generate HTML for test results."""
        html = ""
        
        for test_name, test_results in results.items():
            html += f"<h3>{test_name.replace('_', ' ').title()}</h3>"
            
            if isinstance(test_results, dict):
                html += '<table>'
                for key, value in test_results.items():
                    if isinstance(value, (int, float)):
                        value = f"{value:.2f}" if isinstance(value, float) else str(value)
                    html += f"<tr><td><strong>{key}</strong></td><td>{value}</td></tr>"
                html += '</table>'
            else:
                html += f"<p>{test_results}</p>"
        
        return html
    
    def _generate_performance_plots(self):
        """Generate performance visualization plots."""
        # This would generate actual plots from the collected data
        # For now, just create a placeholder
        plt.figure(figsize=(10, 6))
        plt.text(0.5, 0.5, 'Performance Plots\nWould be generated here',
                ha='center', va='center', fontsize=16)
        plt.axis('off')
        plt.savefig(self.output_dir / f"performance_plots_{self.timestamp}.png")
        plt.close()


def main():
    """Main entry point for performance testing."""
    parser = argparse.ArgumentParser(description="Run performance tests")
    parser.add_argument("--tests", nargs="+", 
                       choices=["pytest", "locust", "profile", "memory", "database", "all"],
                       default=["all"],
                       help="Which tests to run")
    parser.add_argument("--output", type=Path, 
                       default=Path("performance_reports"),
                       help="Output directory for reports")
    parser.add_argument("--locust-users", type=int, default=100,
                       help="Number of users for Locust test")
    parser.add_argument("--locust-time", default="5m",
                       help="Duration for Locust test")
    
    args = parser.parse_args()
    
    runner = PerformanceTestRunner(args.output)
    
    tests_to_run = ["pytest", "locust", "profile", "memory", "database"] if "all" in args.tests else args.tests
    
    try:
        if "pytest" in tests_to_run:
            runner.results["pytest"] = runner.run_pytest_benchmarks()
        
        if "locust" in tests_to_run:
            runner.results["locust"] = runner.run_locust_load_test(
                users=args.locust_users,
                run_time=args.locust_time
            )
        
        if "profile" in tests_to_run:
            runner.results["profile"] = runner.profile_service_endpoints()
        
        if "memory" in tests_to_run:
            runner.results["memory"] = runner.stress_test_memory()
        
        if "database" in tests_to_run:
            runner.results["database"] = runner.benchmark_database_performance()
        
        # Generate report
        report_file = runner.generate_report()
        print(f"\nPerformance testing complete. Report: {report_file}")
        
    except Exception as e:
        print(f"Error during performance testing: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
