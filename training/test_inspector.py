"""
Inspector Validation Tests
Coder: Claude Sonnet 4.5
Reviewer: GPT-Codex-2 (Pending)

Meta-validation: Tests that validate the validator!

Tests the AdapterInspector to ensure it:
- Correctly identifies valid adapters
- Correctly flags invalid adapters
- Handles edge cases gracefully
- Produces accurate reports
"""

import json
import tempfile
import shutil
from pathlib import Path
from train_lora_adapter import AdapterInspector

def create_mock_adapter(directory: Path, valid: bool = True) -> None:
    """Create a mock adapter for testing."""
    directory.mkdir(parents=True, exist_ok=True)
    
    if valid:
        # Valid adapter structure
        (directory / "adapter_config.json").write_text(json.dumps({
            "base_model": "Qwen/Qwen2.5-7B-Instruct",
            "peft_type": "LORA"
        }))
        (directory / "adapter_model.safetensors").write_bytes(b"x" * 50_000_000)  # 50MB mock
        (directory / "training_config.json").write_text(json.dumps({
            "archetype": "vampire",
            "adapter_task": "personality",
            "lora_rank": 32
        }))
    else:
        # Invalid adapter (missing files)
        (directory / "training_config.json").write_text(json.dumps({
            "archetype": "vampire",
            "adapter_task": "personality"
        }))


def test_valid_adapter_detection():
    """Test: Inspector correctly validates a good adapter."""
    print("\n=== TEST 1: Valid Adapter Detection ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        adapter_path = Path(tmpdir) / "adapters" / "vampire" / "personality"
        create_mock_adapter(adapter_path, valid=True)
        
        # Copy inspector config to temp dir
        inspector_config = Path(__file__).parent / "inspector_config.json"
        temp_inspector_config = Path(tmpdir) / "inspector_config.json"
        shutil.copy(inspector_config, temp_inspector_config)
        
        # Test
        inspector = AdapterInspector(str(temp_inspector_config))
        report = inspector.validate_adapter("vampire", "personality", str(adapter_path))
        
        assert report['overall_status'] in ['passed', 'passed_with_warnings'], \
            f"Expected 'passed', got {report['overall_status']}"
        assert report['tests_passed'] > 0, "Should have passing tests"
        
        print(f"✅ PASSED: Valid adapter correctly identified")
        print(f"   Status: {report['overall_status']}")
        print(f"   Tests passed: {report['tests_passed']}/{report['tests_passed'] + report['tests_failed']}")
        return True


def test_invalid_adapter_detection():
    """Test: Inspector correctly flags a bad adapter."""
    print("\n=== TEST 2: Invalid Adapter Detection ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        adapter_path = Path(tmpdir) / "adapters" / "vampire" / "personality"
        create_mock_adapter(adapter_path, valid=False)
        
        # Copy inspector config
        inspector_config = Path(__file__).parent / "inspector_config.json"
        temp_inspector_config = Path(tmpdir) / "inspector_config.json"
        shutil.copy(inspector_config, temp_inspector_config)
        
        # Test
        inspector = AdapterInspector(str(temp_inspector_config))
        report = inspector.validate_adapter("vampire", "personality", str(adapter_path))
        
        assert report['tests_failed'] > 0, "Should have failing tests for invalid adapter"
        
        print(f"✅ PASSED: Invalid adapter correctly flagged")
        print(f"   Status: {report['overall_status']}")
        print(f"   Tests failed: {report['tests_failed']}/{report['tests_passed'] + report['tests_failed']}")
        return True


def test_missing_adapter_handling():
    """Test: Inspector handles missing adapter gracefully."""
    print("\n=== TEST 3: Missing Adapter Handling ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        adapter_path = Path(tmpdir) / "adapters" / "vampire" / "nonexistent"
        
        # Copy inspector config
        inspector_config = Path(__file__).parent / "inspector_config.json"
        temp_inspector_config = Path(tmpdir) / "inspector_config.json"
        shutil.copy(inspector_config, temp_inspector_config)
        
        # Test
        inspector = AdapterInspector(str(temp_inspector_config))
        
        try:
            report = inspector.validate_adapter("vampire", "personality", str(adapter_path))
            # Should not crash, should fail gracefully
            assert report['overall_status'] == 'failed', "Should fail for missing adapter"
            print(f"✅ PASSED: Missing adapter handled gracefully")
            return True
        except Exception as e:
            print(f"❌ FAILED: Inspector crashed on missing adapter: {e}")
            return False


def test_report_generation():
    """Test: Inspector generates proper report structure."""
    print("\n=== TEST 4: Report Generation ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        adapter_path = Path(tmpdir) / "adapters" / "vampire" / "personality"
        create_mock_adapter(adapter_path, valid=True)
        
        # Copy inspector config
        inspector_config = Path(__file__).parent / "inspector_config.json"
        temp_inspector_config = Path(tmpdir) / "inspector_config.json"
        shutil.copy(inspector_config, temp_inspector_config)
        
        # Test
        inspector = AdapterInspector(str(temp_inspector_config))
        report = inspector.validate_adapter("vampire", "personality", str(adapter_path))
        
        # Check report structure
        required_fields = ['archetype', 'adapter_task', 'timestamp', 'tests_passed', 
                          'tests_failed', 'tests', 'overall_status']
        
        for field in required_fields:
            assert field in report, f"Missing required field: {field}"
        
        # Check report saved
        report_file = adapter_path / "validation_report.json"
        assert report_file.exists(), "Report file should be saved"
        
        # Validate JSON structure
        with open(report_file, 'r') as f:
            saved_report = json.load(f)
        
        assert saved_report == report, "Saved report should match returned report"
        
        print(f"✅ PASSED: Report generated correctly")
        print(f"   Required fields: {len(required_fields)}/{len(required_fields)}")
        print(f"   Report saved: {report_file.exists()}")
        return True


def test_validation_checkpoint_logic():
    """Test: Inspector correctly identifies validation checkpoints."""
    print("\n=== TEST 5: Validation Checkpoint Logic ===")
    
    from train_lora_adapter import TrainingQueueManager
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create mock queue
        queue_file = Path(tmpdir) / "training_queue.json"
        queue_data = {
            "queue_name": "test_queue",
            "config": {
                "validation_checkpoints": [7, 14],
                "auto_start_next": True
            },
            "tasks": [],
            "summary": {
                "total_tasks": 14,
                "pending": 14,
                "completed": 0,
                "failed": 0
            }
        }
        
        with open(queue_file, 'w') as f:
            json.dump(queue_data, f)
        
        # Copy inspector config
        inspector_config = Path(__file__).parent / "inspector_config.json"
        temp_inspector_config = Path(tmpdir) / "inspector_config.json"
        shutil.copy(inspector_config, temp_inspector_config)
        
        # Test
        manager = TrainingQueueManager(str(queue_file))
        
        # Test checkpoint detection
        assert not manager.is_validation_checkpoint(), "Should not be at checkpoint with 0 completed"
        
        manager.queue['summary']['completed'] = 7
        assert manager.is_validation_checkpoint(), "Should be at checkpoint with 7 completed"
        
        manager.queue['summary']['completed'] = 8
        assert not manager.is_validation_checkpoint(), "Should not be at checkpoint with 8 completed"
        
        manager.queue['summary']['completed'] = 14
        assert manager.is_validation_checkpoint(), "Should be at checkpoint with 14 completed"
        
        print(f"✅ PASSED: Checkpoint logic works correctly")
        return True


def run_all_tests():
    """Run all Inspector validation tests."""
    print("\n" + "="*60)
    print("INSPECTOR VALIDATION TEST SUITE")
    print("Meta-validation: Testing the validator!")
    print("="*60)
    
    tests = [
        test_valid_adapter_detection,
        test_invalid_adapter_detection,
        test_missing_adapter_handling,
        test_report_generation,
        test_validation_checkpoint_logic
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ EXCEPTION in {test.__name__}: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"Tests passed: {passed}/{total}")
    print(f"Pass rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("\n✅ ALL TESTS PASSED - Inspector validated!")
        return True
    else:
        print(f"\n❌ {total - passed} TESTS FAILED - Inspector needs fixes")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)

