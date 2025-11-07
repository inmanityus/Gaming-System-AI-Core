"""
UE5 Asset Generation - C++ Helper Wrapper
Calls C++ helper function from Python
"""

import unreal
import sys

def log(message):
    """Log message"""
    print(message)
    unreal.log(message)

def create_reverb_effects_via_cpp():
    """Create reverb effects using C++ helper function"""
    log("\nCreating Reverb Effect assets via C++ Helper...")
    
    reverb_configs = [
        ("RE_Interior_Small", "interior_small", 0.6, {
            "density": 1.0, "diffusion": 1.0, "gain": 0.32, "gain_hf": 0.89,
            "decay_time": 0.5, "decay_hf_ratio": 0.83, "reflections_gain": 0.05,
            "reflections_delay": 0.007, "late_gain": 1.26, "late_delay": 0.011,
            "air_absorption_gain_hf": 0.994, "room_rolloff_factor": 0.0, "volume": 0.6
        }),
        ("RE_Interior_Large", "interior_large", 0.7, {
            "density": 1.0, "diffusion": 1.0, "gain": 0.32, "gain_hf": 0.89,
            "decay_time": 2.0, "decay_hf_ratio": 0.83, "reflections_gain": 0.05,
            "reflections_delay": 0.007, "late_gain": 1.26, "late_delay": 0.011,
            "air_absorption_gain_hf": 0.994, "room_rolloff_factor": 0.0, "volume": 0.7
        }),
        ("RE_Exterior_Open", "exterior_open", 0.3, {
            "density": 0.5, "diffusion": 0.5, "gain": 0.15, "gain_hf": 0.5,
            "decay_time": 0.2, "decay_hf_ratio": 0.5, "reflections_gain": 0.02,
            "reflections_delay": 0.003, "late_gain": 0.5, "late_delay": 0.005,
            "air_absorption_gain_hf": 0.994, "room_rolloff_factor": 0.0, "volume": 0.3
        }),
        ("RE_Exterior_Urban", "exterior_urban", 0.4, {
            "density": 0.7, "diffusion": 0.7, "gain": 0.2, "gain_hf": 0.6,
            "decay_time": 0.3, "decay_hf_ratio": 0.6, "reflections_gain": 0.03,
            "reflections_delay": 0.005, "late_gain": 0.7, "late_delay": 0.008,
            "air_absorption_gain_hf": 0.994, "room_rolloff_factor": 0.0, "volume": 0.4
        }),
        ("RE_Exterior_Forest", "exterior_forest", 0.2, {
            "density": 0.3, "diffusion": 0.3, "gain": 0.1, "gain_hf": 0.3,
            "decay_time": 0.1, "decay_hf_ratio": 0.3, "reflections_gain": 0.01,
            "reflections_delay": 0.002, "late_gain": 0.3, "late_delay": 0.003,
            "air_absorption_gain_hf": 0.994, "room_rolloff_factor": 0.0, "volume": 0.2
        }),
        ("RE_Exterior_Cave", "exterior_cave", 0.8, {
            "density": 1.0, "diffusion": 1.0, "gain": 0.4, "gain_hf": 0.95,
            "decay_time": 3.0, "decay_hf_ratio": 0.9, "reflections_gain": 0.1,
            "reflections_delay": 0.01, "late_gain": 1.5, "late_delay": 0.015,
            "air_absorption_gain_hf": 0.994, "room_rolloff_factor": 0.0, "volume": 0.8
        }),
    ]
    
    created_assets = []
    directory = "/Game/Audio/Reverb"
    
    # Ensure directory exists
    if not unreal.EditorAssetLibrary.does_directory_exist(directory):
        unreal.EditorAssetLibrary.make_directory(directory)
    
    # Try to use C++ helper function
    try:
        audio_manager_helpers = unreal.AudioManagerAssetHelpers
        if hasattr(audio_manager_helpers, 'create_reverb_effect_asset'):
            log("  → Using C++ helper function...")
            
            for asset_name, preset_name, send_level, settings in reverb_configs:
                path = f"{directory}/{asset_name}"
                
                if unreal.EditorAssetLibrary.does_asset_exist(path):
                    log(f"  ✓ {asset_name} already exists")
                    created_assets.append((path, preset_name, send_level))
                    continue
                
                log(f"  → Creating {asset_name}...")
                
                # Call C++ helper with individual parameters (no Volume or RoomRolloffFactor)
                reverb_effect = audio_manager_helpers.create_reverb_effect_asset(
                    asset_name,
                    directory,
                    settings.get("density", 1.0),
                    settings.get("diffusion", 1.0),
                    settings.get("gain", 0.32),
                    settings.get("gain_hf", 0.89),
                    settings.get("decay_time", 1.49),
                    settings.get("decay_hf_ratio", 0.83),
                    settings.get("reflections_gain", 0.05),
                    settings.get("reflections_delay", 0.007),
                    settings.get("late_gain", 1.26),
                    settings.get("late_delay", 0.011),
                    settings.get("air_absorption_gain_hf", 0.994)
                )
                
                if reverb_effect:
                    if unreal.EditorAssetLibrary.does_asset_exist(path):
                        log(f"  ✓ Created via C++: {asset_name}")
                        created_assets.append((path, preset_name, send_level))
                    else:
                        log(f"  ⚠ C++ created but not found in registry: {asset_name}")
                        # Wait a moment for registry update
                        import time
                        time.sleep(0.5)
                        if unreal.EditorAssetLibrary.does_asset_exist(path):
                            log(f"  ✓ Verified after wait: {asset_name}")
                            created_assets.append((path, preset_name, send_level))
                        else:
                            log(f"  ✗ Still not found: {asset_name}")
                else:
                    log(f"  ✗ C++ helper returned None: {asset_name}")
            
            return created_assets
        else:
            log("  ⚠ C++ helper function not available")
    except AttributeError as e:
        log(f"  ⚠ C++ helper not accessible: {str(e)}")
    except Exception as e:
        log(f"  ⚠ C++ helper error: {str(e)}")
        import traceback
        log(f"  Traceback: {traceback.format_exc()}")
    
    log("  ⚠ C++ helper not available, assets not created")
    return []

def create_directories():
    """Create required directory structure"""
    log("Creating directory structure...")
    directories = [
        "/Game/Audio/MetaSounds",
        "/Game/Audio/Reverb",
        "/Game/Data/Expressions",
        "/Game/Data/Gestures",
        "/Game/Blueprints",
        "/Game/Maps",
    ]
    
    for dir_path in directories:
        try:
            unreal.EditorAssetLibrary.make_directory(dir_path)
            log(f"  ✓ Created directory: {dir_path}")
        except Exception as e:
            log(f"  ⚠ Directory warning: {dir_path} - {str(e)}")

def create_test_blueprint():
    """Create BP_Phase4TestActor Blueprint"""
    log("\nCreating Test Blueprint...")
    
    blueprint_path = "/Game/Blueprints/BP_Phase4TestActor"
    
    try:
        if unreal.EditorAssetLibrary.does_asset_exist(blueprint_path):
            blueprint = unreal.EditorAssetLibrary.load_asset(blueprint_path)
            if blueprint:
                log("  ✓ BP_Phase4TestActor already exists")
                return blueprint_path
        
        log("  → Creating BP_Phase4TestActor...")
        
        asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
        factory = unreal.BlueprintFactory()
        factory.set_editor_property("parent_class", unreal.Actor)
        factory.set_editor_property("suppress_dialog", True)
        
        blueprint = asset_tools.create_asset(
            asset_name="BP_Phase4TestActor",
            package_path="/Game/Blueprints",
            asset_class=unreal.Blueprint,
            factory=factory
        )
        
        if blueprint:
            blueprint.get_outer().mark_package_dirty()
            unreal.EditorAssetLibrary.save_loaded_asset(blueprint)
            
            if unreal.EditorAssetLibrary.does_asset_exist(blueprint_path):
                log("  ✓ Created BP_Phase4TestActor")
                return blueprint_path
            else:
                log("  ✗ Created but verification failed")
        else:
            log("  ✗ Failed to create Blueprint")
            
    except Exception as e:
        log(f"  ✗ Error: {str(e)}")
        import traceback
        log(f"  Traceback: {traceback.format_exc()}")
    
    return None

def create_test_level():
    """Create test level"""
    log("\nCreating Test Level...")
    
    level_path = "/Game/Maps/Phase4TestLevel"
    
    try:
        if unreal.EditorAssetLibrary.does_asset_exist(level_path):
            log("  ✓ Phase4TestLevel already exists")
            return level_path
        
        log("  → Creating Phase4TestLevel...")
        level = unreal.EditorLevelLibrary.new_level(level_path)
        
        if level:
            unreal.EditorLevelLibrary.save_current_level()
            
            if unreal.EditorAssetLibrary.does_asset_exist(level_path):
                log("  ✓ Created Phase4TestLevel")
                return level_path
            else:
                log("  ✗ Created but verification failed")
        else:
            log("  ✗ Failed to create level")
            
    except Exception as e:
        log(f"  ✗ Error: {str(e)}")
        import traceback
        log(f"  Traceback: {traceback.format_exc()}")
    
    return None

def verify_created_assets(reverb_assets, blueprint_path, level_path):
    """Verify all created assets"""
    log("\n" + "=" * 60)
    log("Verifying Created Assets")
    log("=" * 60)
    
    verified_count = 0
    total_count = len(reverb_assets) + (1 if blueprint_path else 0) + (1 if level_path else 0)
    
    for path, preset_name, send_level in reverb_assets:
        if unreal.EditorAssetLibrary.does_asset_exist(path):
            try:
                asset = unreal.EditorAssetLibrary.load_asset(path)
                if asset:
                    log(f"  ✓ Verified: {path.split('/')[-1]}")
                    verified_count += 1
                else:
                    log(f"  ✗ Failed to load: {path.split('/')[-1]}")
            except:
                log(f"  ✗ Error loading: {path.split('/')[-1]}")
        else:
            log(f"  ✗ Not found: {path.split('/')[-1]}")
    
    if blueprint_path:
        if unreal.EditorAssetLibrary.does_asset_exist(blueprint_path):
            try:
                asset = unreal.EditorAssetLibrary.load_asset(blueprint_path)
                if asset:
                    log(f"  ✓ Verified: BP_Phase4TestActor")
                    verified_count += 1
                else:
                    log(f"  ✗ Failed to load: BP_Phase4TestActor")
            except:
                log(f"  ✗ Error loading: BP_Phase4TestActor")
        else:
            log(f"  ✗ Not found: BP_Phase4TestActor")
    
    if level_path:
        if unreal.EditorAssetLibrary.does_asset_exist(level_path):
            log(f"  ✓ Verified: Phase4TestLevel")
            verified_count += 1
        else:
            log(f"  ✗ Not found: Phase4TestLevel")
    
    log(f"\nVerification: {verified_count}/{total_count} assets verified")
    return verified_count == total_count

def main():
    """Main execution"""
    log("=" * 60)
    log("Phase 4 Asset Creation Script - C++ Helper Version")
    log("Uses C++ helper function for reliable asset creation")
    log("=" * 60)
    
    try:
        create_directories()
        reverb_effects = create_reverb_effects_via_cpp()
        test_blueprint = create_test_blueprint()
        test_level = create_test_level()
        all_verified = verify_created_assets(reverb_effects, test_blueprint, test_level)
        
        log("\n" + "=" * 60)
        log("Asset Creation Summary")
        log("=" * 60)
        log(f"Reverb Effects: {len(reverb_effects)} created")
        log(f"Test Blueprint: {'Created' if test_blueprint else 'Failed'}")
        log(f"Test Level: {'Created' if test_level else 'Failed'}")
        log(f"All Assets Verified: {'YES' if all_verified else 'NO'}")
        
        if all_verified:
            log("\n✅ All assets created and verified!")
            return 0
        else:
            log("\n⚠ Some assets failed - check logs for details")
            return 1
        
    except Exception as e:
        log(f"\n✗ Fatal error: {str(e)}")
        import traceback
        log(f"Traceback: {traceback.format_exc()}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

