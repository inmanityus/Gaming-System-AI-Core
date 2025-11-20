"""
Performance benchmarks for audio processing services.
Tests throughput, latency, and resource usage.
"""
import pytest
import asyncio
import time
import numpy as np
import psutil
import os
import sys
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import multiprocessing as mp
from typing import List, Dict, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from services.ethelred_audio_metrics.intelligibility_analyzer import (
    IntelligibilityAnalyzer, IntelligibilityConfig
)
from services.ethelred_audio_metrics.archetype_analyzer import (
    ArchetypeAnalyzer, ArchetypeAnalyzerConfig
)


@pytest.mark.performance
class TestAudioAnalysisPerformance:
    """Performance benchmarks for audio analysis."""
    
    @pytest.fixture
    def large_audio_dataset(self):
        """Generate large dataset for performance testing."""
        # Generate various audio samples
        samples = []
        sample_rate = 48000
        
        # Different durations
        durations = [1, 3, 5, 10, 30]  # seconds
        
        for duration in durations:
            # Generate 10 samples of each duration
            for i in range(10):
                t = np.linspace(0, duration, int(sample_rate * duration))
                
                # Vary complexity
                if i < 3:  # Simple sine wave
                    signal = np.sin(2 * np.pi * 440 * t)
                elif i < 6:  # Complex harmonic
                    signal = np.zeros_like(t)
                    for harmonic in range(1, 10):
                        signal += (1.0 / harmonic) * np.sin(2 * np.pi * 440 * harmonic * t)
                else:  # Speech-like with noise
                    f0 = 150 + 50 * np.sin(2 * np.pi * 0.5 * t)
                    signal = np.sin(2 * np.pi * f0 * t)
                    signal += 0.1 * np.random.randn(len(t))
                
                samples.append((signal, sample_rate, duration))
        
        return samples
    
    async def test_single_analysis_latency(self, large_audio_dataset, intelligibility_config):
        """Test latency for single audio analysis."""
        analyzer = IntelligibilityAnalyzer(config=intelligibility_config)
        
        # Get multiple different audio samples to avoid caching
        test_samples = [s for s in large_audio_dataset if s[2] == 3][:10]  # 10 different 3s samples
        
        # Warm up with different samples
        for audio, sr, _ in test_samples[:3]:
            await analyzer.analyze(audio, sr, user_id="warmup")
        
        # Measure latency over multiple runs
        latencies = []
        num_iterations = 500  # More iterations for stable statistics
        
        for i in range(num_iterations):
            # Cycle through different samples
            audio, sample_rate, _ = test_samples[i % len(test_samples)]
            
            start = time.perf_counter()
            await analyzer.analyze(audio, sample_rate, user_id=f"perf_test_{i}")
            end = time.perf_counter()
            latencies.append((end - start) * 1000)  # Convert to ms
        
        # Calculate statistics
        latencies = np.array(latencies)
        
        print(f"\nSingle Analysis Latency (3s audio):")
        print(f"  Mean: {np.mean(latencies):.2f} ms")
        print(f"  Median: {np.median(latencies):.2f} ms")
        print(f"  95th percentile: {np.percentile(latencies, 95):.2f} ms")
        print(f"  99th percentile: {np.percentile(latencies, 99):.2f} ms")
        print(f"  Min: {np.min(latencies):.2f} ms")
        print(f"  Max: {np.max(latencies):.2f} ms")
        
        # Assert performance requirements
        assert np.median(latencies) < 100  # Median under 100ms
        assert np.percentile(latencies, 95) < 200  # 95th percentile under 200ms
    
    async def test_concurrent_analysis_throughput(self, large_audio_dataset, intelligibility_config):
        """Test throughput with concurrent analyses."""
        # Instantiate analyzer ONCE outside the loop
        analyzer = IntelligibilityAnalyzer(config=intelligibility_config)
        
        # Select medium duration samples (3 seconds)
        test_samples = [s for s in large_audio_dataset if s[2] == 3][:50]  # More samples for variety
        
        # Proper warm-up phase
        print("Warming up analyzer...")
        for i in range(10):
            audio, sr, _ = test_samples[i % len(test_samples)]
            await analyzer.analyze(audio, sr, user_id=f"warmup_{i}")
        
        # Test different concurrency levels
        concurrency_levels = [1, 5, 10, 20, 50]
        results = []
        
        print("\nConcurrent Analysis Throughput:")
        
        for concurrency in concurrency_levels:
            # Prepare all tasks BEFORE measuring
            tasks = []
            for i in range(concurrency):
                # Cycle through different samples
                audio, sr, _ = test_samples[i % len(test_samples)]
                task = analyzer.analyze(audio, sr, user_id=f"concurrent_{concurrency}_{i}")
                tasks.append(task)
            
            # Start timer only for actual execution
            start = time.perf_counter()
            await asyncio.gather(*tasks)
            end = time.perf_counter()
            
            duration = end - start
            throughput = concurrency / duration if duration > 0 else float('inf')
            
            results.append({
                'concurrency': concurrency,
                'duration': duration,
                'throughput': throughput
            })
            
            print(f"\nConcurrency {concurrency}:")
            print(f"  Duration: {duration:.2f}s")
            print(f"  Throughput: {throughput:.2f} analyses/second")
        
        # Verify scaling
        # Throughput should increase with concurrency (up to a point)
        base_throughput = results[0]['throughput']
        best_throughput = max(r['throughput'] for r in results)
        
        assert best_throughput > base_throughput * 3  # At least 3x improvement
    
    async def test_memory_usage(self, large_audio_dataset, intelligibility_config):
        """Test memory usage during analysis."""
        analyzer = IntelligibilityAnalyzer(config=intelligibility_config)
        
        # Get baseline memory
        process = psutil.Process()
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        memory_readings = []
        
        # Process multiple samples
        for i, (audio, sr, duration) in enumerate(large_audio_dataset[:20]):
            await analyzer.analyze(audio, sr, user_id=f"memory_test_{i}")
            
            # Record memory every 5 analyses
            if i % 5 == 0:
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_readings.append(current_memory - baseline_memory)
        
        print(f"\nMemory Usage:")
        print(f"  Baseline: {baseline_memory:.2f} MB")
        print(f"  Peak increase: {max(memory_readings):.2f} MB")
        print(f"  Average increase: {np.mean(memory_readings):.2f} MB")
        
        # Assert no memory leaks
        assert max(memory_readings) < 500  # Less than 500MB increase
        # Memory should stabilize (not continuously growing)
        assert memory_readings[-1] < memory_readings[len(memory_readings)//2] * 1.5
    
    def test_cpu_bound_performance(self, sample_audio_48khz):
        """Test CPU-bound performance with multiprocessing."""
        audio, sample_rate = sample_audio_48khz
        
        def process_audio_cpu(args):
            """CPU-intensive audio processing."""
            audio, sr, idx = args
            
            # Simulate CPU-intensive operations
            # FFT
            fft = np.fft.rfft(audio)
            
            # Spectral features
            magnitude = np.abs(fft)
            phase = np.angle(fft)
            
            # Statistical features
            features = {
                'mean': np.mean(audio),
                'std': np.std(audio),
                'max': np.max(audio),
                'spectral_centroid': np.sum(magnitude * np.arange(len(magnitude))) / np.sum(magnitude),
                'zero_crossings': np.sum(np.diff(np.sign(audio)) != 0)
            }
            
            return idx, features
        
        # Test with different worker counts
        worker_counts = [1, 2, 4, mp.cpu_count()]
        num_tasks = 100
        
        results = []
        
        for num_workers in worker_counts:
            start = time.perf_counter()
            
            with ProcessPoolExecutor(max_workers=num_workers) as executor:
                tasks = [(audio, sample_rate, i) for i in range(num_tasks)]
                list(executor.map(process_audio_cpu, tasks))
            
            end = time.perf_counter()
            duration = end - start
            
            results.append({
                'workers': num_workers,
                'duration': duration,
                'tasks_per_second': num_tasks / duration
            })
            
            print(f"\nCPU Performance ({num_workers} workers):")
            print(f"  Duration: {duration:.2f}s")
            print(f"  Tasks/second: {num_tasks / duration:.2f}")
        
        # Verify scaling
        single_worker_rate = results[0]['tasks_per_second']
        best_rate = max(r['tasks_per_second'] for r in results)
        
        # Should scale somewhat with CPU cores
        assert best_rate > single_worker_rate * 1.5
    
    async def test_database_write_performance(self, postgres_pool, large_audio_dataset, intelligibility_config):
        """Test database write performance."""
        analyzer = IntelligibilityAnalyzer(
            config=intelligibility_config,
            db_pool=postgres_pool
        )
        
        # Prepare batch of analyses
        num_writes = 100
        test_samples = large_audio_dataset[:10]  # Use 10 different samples
        
        start = time.perf_counter()
        
        # Concurrent database writes
        tasks = []
        for i in range(num_writes):
            audio, sr, _ = test_samples[i % len(test_samples)]
            task = analyzer.analyze(
                audio, sr,
                user_id=f"db_perf_user_{i}",
                audio_file_path=f"/perf/audio_{i}.ogg"
            )
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        
        end = time.perf_counter()
        duration = end - start
        writes_per_second = num_writes / duration
        
        print(f"\nDatabase Write Performance:")
        print(f"  Total writes: {num_writes}")
        print(f"  Duration: {duration:.2f}s")
        print(f"  Writes/second: {writes_per_second:.2f}")
        
        # Verify all written
        async with postgres_pool.acquire() as conn:
            count = await conn.fetchval("""
                SELECT COUNT(*) FROM ethelred.audio_metrics
                WHERE user_id LIKE 'db_perf_user_%'
            """)
        
        assert count == num_writes
        assert writes_per_second > 20  # At least 20 writes/second


@pytest.mark.performance
class TestArchetypeAnalysisPerformance:
    """Performance benchmarks for archetype analysis."""
    
    async def test_archetype_matching_performance(
        self,
        sample_audio_48khz,
        archetype_config,
        archetype_profiles
    ):
        """Test performance of archetype matching algorithm."""
        analyzer = ArchetypeAnalyzer(config=archetype_config)
        
        # Load profiles into analyzer
        analyzer.profiles = archetype_profiles
        
        audio, sample_rate = sample_audio_48khz
        
        # Test matching against different numbers of archetypes
        profile_counts = [5, 10, 25, 50, 100]
        
        for count in profile_counts:
            # Create extended profiles
            extended_profiles = {}
            for i in range(count):
                base_profile = archetype_profiles['vampire_alpha']
                # Slightly modify each profile
                extended_profiles[f'archetype_{i}'] = {
                    'pitch_range': (
                        base_profile['pitch_range'][0] + i,
                        base_profile['pitch_range'][1] + i
                    ),
                    'formant_ratios': [r + 0.01 * i for r in base_profile['formant_ratios']],
                    'voice_texture': base_profile['voice_texture'].copy()
                }
            
            analyzer.profiles = extended_profiles
            
            # Measure matching time
            start = time.perf_counter()
            
            for _ in range(10):
                result = await analyzer.analyze(
                    audio,
                    sample_rate,
                    expected_archetype=f'archetype_{count//2}'
                )
            
            end = time.perf_counter()
            avg_time = (end - start) / 10 * 1000  # ms per analysis
            
            print(f"\nArchetype Matching ({count} profiles):")
            print(f"  Average time: {avg_time:.2f} ms")
            
            # Should scale reasonably with profile count
            assert avg_time < 50 * (count / 10)  # Linear scaling factor


@pytest.mark.performance
class TestSystemLoadPerformance:
    """Test system behavior under load."""
    
    async def test_sustained_load(
        self,
        sample_audio_48khz,
        intelligibility_config,
        performance_timer
    ):
        """Test sustained load over extended period."""
        analyzer = IntelligibilityAnalyzer(config=intelligibility_config)
        audio, sample_rate = sample_audio_48khz
        
        # Run for 60 seconds
        duration_seconds = 60
        analyses_completed = 0
        errors = 0
        
        timer = performance_timer()
        
        async def continuous_analysis():
            nonlocal analyses_completed, errors
            
            while timer.elapsed is None or timer.elapsed < duration_seconds:
                try:
                    await analyzer.analyze(
                        audio,
                        sample_rate,
                        user_id=f"load_test_{analyses_completed}"
                    )
                    analyses_completed += 1
                except Exception as e:
                    errors += 1
                    print(f"Error during analysis: {e}")
                
                # Small delay to prevent overwhelming
                await asyncio.sleep(0.01)
        
        # Run multiple concurrent workers
        num_workers = 10
        
        with timer:
            tasks = [continuous_analysis() for _ in range(num_workers)]
            await asyncio.gather(*tasks)
        
        throughput = analyses_completed / timer.elapsed
        error_rate = errors / max(analyses_completed, 1)
        
        print(f"\nSustained Load Test ({duration_seconds}s, {num_workers} workers):")
        print(f"  Total analyses: {analyses_completed}")
        print(f"  Throughput: {throughput:.2f} analyses/second")
        print(f"  Errors: {errors}")
        print(f"  Error rate: {error_rate:.2%}")
        
        # Assert acceptable performance
        assert throughput > 50  # At least 50 analyses/second sustained
        assert error_rate < 0.01  # Less than 1% error rate
    
    async def test_spike_recovery(
        self,
        sample_audio_48khz,
        intelligibility_config
    ):
        """Test system recovery from load spikes."""
        analyzer = IntelligibilityAnalyzer(config=intelligibility_config)
        audio, sample_rate = sample_audio_48khz
        
        # Baseline performance
        baseline_latencies = []
        for i in range(20):
            start = time.perf_counter()
            await analyzer.analyze(audio, sample_rate, user_id=f"baseline_{i}")
            baseline_latencies.append(time.perf_counter() - start)
        
        baseline_median = np.median(baseline_latencies)
        
        # Create spike load
        spike_tasks = []
        for i in range(200):  # 200 concurrent requests
            task = analyzer.analyze(audio, sample_rate, user_id=f"spike_{i}")
            spike_tasks.append(task)
        
        await asyncio.gather(*spike_tasks, return_exceptions=True)
        
        # Wait brief recovery period
        await asyncio.sleep(2)
        
        # Measure post-spike performance
        recovery_latencies = []
        for i in range(20):
            start = time.perf_counter()
            await analyzer.analyze(audio, sample_rate, user_id=f"recovery_{i}")
            recovery_latencies.append(time.perf_counter() - start)
        
        recovery_median = np.median(recovery_latencies)
        
        print(f"\nSpike Recovery Test:")
        print(f"  Baseline median latency: {baseline_median*1000:.2f} ms")
        print(f"  Post-spike median latency: {recovery_median*1000:.2f} ms")
        print(f"  Recovery ratio: {recovery_median/baseline_median:.2f}x")
        
        # Should recover to within 2x of baseline
        assert recovery_median < baseline_median * 2
