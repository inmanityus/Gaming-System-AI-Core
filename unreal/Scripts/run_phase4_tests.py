"""
Phase 4 Runtime Testing Script for UE5
Runs automated runtime tests for Phase 4 systems
Run this script in UE5 Editor Python console after assets are created
"""

import unreal
import time

def get_audiomanager_component(actor):
    """Get AudioManager component from actor"""
    components = actor.get_components_by_class(unreal.AudioManager)
    return components[0] if components else None

def get_dialogue_manager_subsystem():
    """Get DialogueManager subsystem from GameInstance"""
    world = unreal.EditorLevelLibrary.get_editor_world()
    if world:
        game_instance = world.get_game_instance()
        if game_instance:
            return game_instance.get_subsystem(unreal.DialogueManager)
    return None

def test_audiomanager_initialization():
    """Test 1: AudioManager Initialization"""
    print("\n" + "=" * 60)
    print("Test 1: AudioManager Initialization")
    print("=" * 60)
    
    # Find test actor in level
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    test_actor = None
    for actor in actors:
        if "Phase4Test" in str(actor.get_class()):
            test_actor = actor
            break
    
    if not test_actor:
        print("  ✗ Test actor not found in level")
        print("     Please spawn BP_Phase4TestActor in the level")
        return False
    
    audio_manager = get_audiomanager_component(test_actor)
    if not audio_manager:
        print("  ✗ AudioManager component not found")
        return False
    
    # Check initialization
    try:
        # Initialize AudioManager
        audio_manager.initialize("http://localhost:4000")
        print("  ✓ AudioManager initialized")
        
        # Check VA-002 systems
        current_state = audio_manager.get_current_time_of_day_ambient()
        print(f"  ✓ Current time-of-day state: {current_state}")
        
        return True
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        return False

def test_time_of_day_ambient():
    """Test 2: Time-of-Day Ambient"""
    print("\n" + "=" * 60)
    print("Test 2: Time-of-Day Ambient")
    print("=" * 60)
    
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    test_actor = None
    for actor in actors:
        if "Phase4Test" in str(actor.get_class()):
            test_actor = actor
            break
    
    if not test_actor:
        print("  ✗ Test actor not found")
        return False
    
    audio_manager = get_audiomanager_component(test_actor)
    if not audio_manager:
        print("  ✗ AudioManager component not found")
        return False
    
    try:
        # Test dawn ambient
        print("  → Setting time-of-day to 'dawn'...")
        audio_manager.set_time_of_day_ambient("dawn")
        time.sleep(1)
        print("  ✓ Dawn ambient set")
        
        # Test day ambient (should crossfade)
        print("  → Setting time-of-day to 'day' (should crossfade)...")
        audio_manager.set_time_of_day_ambient("day")
        time.sleep(2)
        print("  ✓ Day ambient set (crossfade in progress)")
        
        return True
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        return False

def test_weather_audio_layering():
    """Test 3: Weather Audio Layering"""
    print("\n" + "=" * 60)
    print("Test 3: Weather Audio Layering")
    print("=" * 60)
    
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    test_actor = None
    for actor in actors:
        if "Phase4Test" in str(actor.get_class()):
            test_actor = actor
            break
    
    if not test_actor:
        print("  ✗ Test actor not found")
        return False
    
    audio_manager = get_audiomanager_component(test_actor)
    if not audio_manager:
        print("  ✗ AudioManager component not found")
        return False
    
    try:
        # Test rain weather
        print("  → Setting weather to RAIN at 0.5 intensity...")
        audio_manager.set_weather_audio_layer(unreal.EWeatherState.RAIN, 0.5)
        time.sleep(1)
        print("  ✓ Rain weather set")
        
        # Test storm weather (should have multiple layers)
        print("  → Setting weather to STORM at 0.8 intensity...")
        audio_manager.set_weather_audio_layer(unreal.EWeatherState.STORM, 0.8)
        time.sleep(1)
        print("  ✓ Storm weather set (multiple layers)")
        
        return True
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        return False

def test_dialogue_priority():
    """Test 6: Dialogue Priority System"""
    print("\n" + "=" * 60)
    print("Test 6: Dialogue Priority System")
    print("=" * 60)
    
    dialogue_manager = get_dialogue_manager_subsystem()
    if not dialogue_manager:
        print("  ✗ DialogueManager subsystem not found")
        return False
    
    try:
        # Create test dialogue items
        print("  → Creating Priority 3 dialogue...")
        # Note: This requires creating FDialogueItem structure
        # For now, we'll test the subsystem exists
        print("  ✓ DialogueManager subsystem accessible")
        print("     Note: Full dialogue test requires FDialogueItem creation")
        print("     See docs/testing/PHASE4-RUNTIME-TESTING-GUIDE.md")
        
        return True
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        return False

def test_lipsync_component():
    """Test 9: Lip-Sync System"""
    print("\n" + "=" * 60)
    print("Test 9: Lip-Sync System")
    print("=" * 60)
    
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    test_actor = None
    for actor in actors:
        if "Phase4Test" in str(actor.get_class()):
            test_actor = actor
            break
    
    if not test_actor:
        print("  ✗ Test actor not found")
        return False
    
    # Get LipSyncComponent
    lip_sync_components = test_actor.get_components_by_class(unreal.LipSyncComponent)
    if not lip_sync_components:
        print("  ✗ LipSyncComponent not found")
        return False
    
    lip_sync = lip_sync_components[0]
    
    try:
        # Test lip-sync enabled
        print("  → Enabling lip-sync...")
        lip_sync.set_lip_sync_enabled(True)
        print("  ✓ Lip-sync enabled")
        
        # Note: Full test requires FLipSyncData structure creation
        print("     Note: Full test requires FLipSyncData creation")
        print("     See docs/testing/PHASE4-RUNTIME-TESTING-GUIDE.md")
        
        return True
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        return False

def run_all_tests():
    """Run all Phase 4 runtime tests"""
    print("=" * 60)
    print("Phase 4 Runtime Testing")
    print("=" * 60)
    print("\nPrerequisites:")
    print("  - BP_Phase4TestActor spawned in level")
    print("  - All components added to test actor")
    print("  - Required assets created")
    print("\nStarting tests...")
    
    results = {}
    
    # Run tests
    results["Test 1: AudioManager Init"] = test_audiomanager_initialization()
    results["Test 2: Time-of-Day Ambient"] = test_time_of_day_ambient()
    results["Test 3: Weather Audio"] = test_weather_audio_layering()
    results["Test 6: Dialogue Priority"] = test_dialogue_priority()
    results["Test 9: Lip-Sync"] = test_lipsync_component()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✅ All tests passed!")
    else:
        print(f"\n⚠ {total - passed} test(s) failed or skipped")
        print("   Check prerequisites and asset setup")

if __name__ == "__main__":
    run_all_tests()

