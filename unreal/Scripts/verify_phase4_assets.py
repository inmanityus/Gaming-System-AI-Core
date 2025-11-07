"""
Phase 4 Comprehensive Verification Script
Verifies all created assets and tests functionality
"""

import unreal
import sys

def verify_reverb_assets():
    """Verify reverb effect assets exist and are valid"""
    print("\n" + "=" * 60)
    print("Verifying Reverb Assets")
    print("=" * 60)
    
    reverb_configs = [
        "RE_Interior_Small",
        "RE_Interior_Large",
        "RE_Exterior_Open",
        "RE_Exterior_Urban",
        "RE_Exterior_Forest",
        "RE_Exterior_Cave",
    ]
    
    found = 0
    missing = []
    
    for asset_name in reverb_configs:
        path = f"/Game/Audio/Reverb/{asset_name}"
        try:
            asset_data = unreal.EditorAssetLibrary.find_asset_data(path)
            if asset_data:
                asset = unreal.EditorAssetLibrary.load_asset(path)
                if asset:
                    print(f"  ✓ {asset_name} - Valid asset")
                    found += 1
                else:
                    print(f"  ✗ {asset_name} - Found but failed to load")
                    missing.append(asset_name)
            else:
                print(f"  ✗ {asset_name} - Not found")
                missing.append(asset_name)
        except Exception as e:
            print(f"  ✗ {asset_name} - Error: {str(e)}")
            missing.append(asset_name)
    
    print(f"\nSummary: {found}/{len(reverb_configs)} reverb assets verified")
    return found == len(reverb_configs), missing

def verify_test_blueprint():
    """Verify test Blueprint exists and is valid"""
    print("\n" + "=" * 60)
    print("Verifying Test Blueprint")
    print("=" * 60)
    
    blueprint_path = "/Game/Blueprints/BP_Phase4TestActor"
    
    try:
        asset_data = unreal.EditorAssetLibrary.find_asset_data(blueprint_path)
        if asset_data:
            blueprint = unreal.EditorAssetLibrary.load_asset(blueprint_path)
            if blueprint:
                print(f"  ✓ BP_Phase4TestActor - Valid Blueprint")
                
                # Try to get Blueprint class info
                try:
                    bp_class = blueprint.get_editor_property("generated_class")
                    if bp_class:
                        print(f"  ✓ Blueprint class: {bp_class.get_name()}")
                    else:
                        print(f"  ⚠ Blueprint class not available")
                except:
                    print(f"  ⚠ Could not get Blueprint class info")
                
                return True
            else:
                print(f"  ✗ BP_Phase4TestActor - Found but failed to load")
                return False
        else:
            print(f"  ✗ BP_Phase4TestActor - Not found")
            return False
    except Exception as e:
        print(f"  ✗ Error verifying Blueprint: {str(e)}")
        return False

def verify_test_level():
    """Verify test level exists"""
    print("\n" + "=" * 60)
    print("Verifying Test Level")
    print("=" * 60)
    
    level_path = "/Game/Maps/Phase4TestLevel"
    
    try:
        asset_data = unreal.EditorAssetLibrary.find_asset_data(level_path)
        if asset_data:
            level = unreal.EditorAssetLibrary.load_asset(level_path)
            if level:
                print(f"  ✓ Phase4TestLevel - Valid level")
                return True
            else:
                print(f"  ✗ Phase4TestLevel - Found but failed to load")
                return False
        else:
            print(f"  ✗ Phase4TestLevel - Not found")
            return False
    except Exception as e:
        print(f"  ✗ Error verifying level: {str(e)}")
        return False

def verify_directory_structure():
    """Verify all required directories exist"""
    print("\n" + "=" * 60)
    print("Verifying Directory Structure")
    print("=" * 60)
    
    directories = [
        "/Game/Audio/MetaSounds",
        "/Game/Audio/Reverb",
        "/Game/Data/Expressions",
        "/Game/Data/Gestures",
        "/Game/Blueprints",
        "/Game/Maps",
    ]
    
    all_exist = True
    for dir_path in directories:
        try:
            # Check if directory exists by trying to list assets
            assets = unreal.EditorAssetLibrary.list_assets(dir_path, recursive=False)
            print(f"  ✓ {dir_path} exists ({len(assets)} assets)")
        except:
            print(f"  ✗ {dir_path} does not exist or is inaccessible")
            all_exist = False
    
    return all_exist

def test_audiomanager_class():
    """Test if AudioManager class is accessible"""
    print("\n" + "=" * 60)
    print("Testing AudioManager Class")
    print("=" * 60)
    
    try:
        # Try to get AudioManager class
        audio_manager_class = unreal.AudioManager
        if audio_manager_class:
            print(f"  ✓ AudioManager class accessible")
            print(f"    Class name: {audio_manager_class.get_name()}")
            return True
        else:
            print(f"  ✗ AudioManager class not found")
            return False
    except Exception as e:
        print(f"  ✗ Error accessing AudioManager: {str(e)}")
        return False

def test_dialogue_manager_subsystem():
    """Test if DialogueManager subsystem is accessible"""
    print("\n" + "=" * 60)
    print("Testing DialogueManager Subsystem")
    print("=" * 60)
    
    try:
        world = unreal.EditorLevelLibrary.get_editor_world()
        if world:
            game_instance = world.get_game_instance()
            if game_instance:
                try:
                    dialogue_manager = game_instance.get_subsystem(unreal.DialogueManager)
                    if dialogue_manager:
                        print(f"  ✓ DialogueManager subsystem accessible")
                        return True
                    else:
                        print(f"  ⚠ DialogueManager subsystem not initialized")
                        return False
                except AttributeError:
                    print(f"  ⚠ DialogueManager class not found (may need compilation)")
                    return False
            else:
                print(f"  ⚠ GameInstance not available")
                return False
        else:
            print(f"  ⚠ Editor world not available")
            return False
    except Exception as e:
        print(f"  ✗ Error: {str(e)}")
        return False

def main():
    """Main verification"""
    print("=" * 60)
    print("Phase 4 Comprehensive Verification")
    print("=" * 60)
    
    results = {}
    
    # Run verifications
    results["Directory Structure"] = verify_directory_structure()
    results["Reverb Assets"], missing_reverb = verify_reverb_assets()
    results["Test Blueprint"] = verify_test_blueprint()
    results["Test Level"] = verify_test_level()
    results["AudioManager Class"] = test_audiomanager_class()
    results["DialogueManager Subsystem"] = test_dialogue_manager_subsystem()
    
    # Summary
    print("\n" + "=" * 60)
    print("Verification Summary")
    print("=" * 60)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name}: {status}")
    
    if missing_reverb:
        print(f"\nMissing Reverb Assets: {', '.join(missing_reverb)}")
    
    print(f"\nTotal: {passed}/{total} verifications passed")
    
    if passed == total:
        print("\n✅ All verifications passed!")
        return 0
    else:
        print(f"\n⚠ {total - passed} verification(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())

