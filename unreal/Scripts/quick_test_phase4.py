"""
Phase 4 Quick Test Script - Run in UE5 Editor Python Console
Quick verification of Phase 4 systems without full test suite
"""

import unreal

def quick_test():
    """Quick test of Phase 4 systems"""
    print("=" * 60)
    print("Phase 4 Quick Test")
    print("=" * 60)
    
    # Test 1: Check if AudioManager class exists
    print("\n1. Checking AudioManager class...")
    try:
        audio_manager_class = unreal.AudioManager
        print("   ✓ AudioManager class found")
    except:
        print("   ✗ AudioManager class not found")
    
    # Test 2: Check if DialogueManager subsystem exists
    print("\n2. Checking DialogueManager subsystem...")
    try:
        world = unreal.EditorLevelLibrary.get_editor_world()
        if world:
            game_instance = world.get_game_instance()
            if game_instance:
                dialogue_manager = game_instance.get_subsystem(unreal.DialogueManager)
                if dialogue_manager:
                    print("   ✓ DialogueManager subsystem accessible")
                else:
                    print("   ⚠ DialogueManager subsystem not initialized")
            else:
                print("   ⚠ GameInstance not found")
        else:
            print("   ⚠ Editor world not found")
    except Exception as e:
        print(f"   ✗ Error: {str(e)}")
    
    # Test 3: Check for test actor in level
    print("\n3. Checking for test actors...")
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    test_actors = [a for a in actors if "Phase4Test" in str(a.get_class())]
    if test_actors:
        print(f"   ✓ Found {len(test_actors)} test actor(s)")
        for actor in test_actors:
            print(f"     - {actor.get_name()}")
    else:
        print("   ⚠ No test actors found in level")
        print("     Spawn BP_Phase4TestActor to run full tests")
    
    # Test 4: Check asset paths
    print("\n4. Checking asset paths...")
    asset_paths = [
        "/Game/Audio/MetaSounds/MS_DayAmbient",
        "/Game/Audio/Reverb/RE_Interior_Small",
        "/Game/Blueprints/BP_Phase4TestActor",
    ]
    
    for path in asset_paths:
        asset = unreal.EditorAssetLibrary.find_asset_data(path)
        if asset:
            print(f"   ✓ {path.split('/')[-1]} exists")
        else:
            print(f"   ⚠ {path.split('/')[-1]} not found")
    
    print("\n" + "=" * 60)
    print("Quick Test Complete")
    print("=" * 60)
    print("\nTo run full tests:")
    print("  exec(open(r'E:\\Vibe Code\\Gaming System\\AI Core\\unreal\\Scripts\\run_phase4_tests.py').read())")

if __name__ == "__main__":
    quick_test()

