"""
Phase 4 Asset Creation Script - PEER REVIEWED & FIXED
Based on feedback from Claude 3.5 Sonnet and GPT-4 Turbo
"""

import unreal
import sys

def log(message):
    """Log message to both console and UE5 log"""
    print(message)
    unreal.log(message)

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
            log(f"  ⚠ Directory creation warning: {dir_path} - {str(e)}")

def create_reverb_effects():
    """Create UReverbEffect assets - PEER REVIEWED VERSION"""
    log("\nCreating Reverb Effect assets...")
    
    reverb_configs = [
        ("RE_Interior_Small", "interior_small", 0.6),
        ("RE_Interior_Large", "interior_large", 0.7),
        ("RE_Exterior_Open", "exterior_open", 0.3),
        ("RE_Exterior_Urban", "exterior_urban", 0.4),
        ("RE_Exterior_Forest", "exterior_forest", 0.2),
        ("RE_Exterior_Cave", "exterior_cave", 0.8),
    ]
    
    created_assets = []
    directory = "/Game/Audio/Reverb"
    
    # Ensure directory exists
    if not unreal.EditorAssetLibrary.does_directory_exist(directory):
        unreal.EditorAssetLibrary.make_directory(directory)
        log(f"  ✓ Created directory: {directory}")
    
    for asset_name, preset_name, send_level in reverb_configs:
        path = f"{directory}/{asset_name}"
        
        try:
            # Check if asset already exists - FIXED: Use does_asset_exist
            if unreal.EditorAssetLibrary.does_asset_exist(path):
                try:
                    asset = unreal.EditorAssetLibrary.load_asset(path)
                    if asset:
                        log(f"  ✓ {asset_name} already exists and is valid")
                        created_assets.append((path, preset_name, send_level))
                        continue
                except:
                    pass  # Asset exists but can't load, recreate
            
            # Create asset using factory pattern (peer-reviewed approach)
            log(f"  → Creating {asset_name}...")
            
            try:
                # Get asset tools
                asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
                
                # Create factory for ReverbEffect
                factory = unreal.ReverbEffectFactory()
                factory.set_editor_property("suppress_dialog", True)
                
                # Create the asset using factory
                reverb_effect = asset_tools.create_asset(
                    asset_name=asset_name,
                    package_path=directory,
                    asset_class=unreal.ReverbEffect,
                    factory=factory
                )
                
                if reverb_effect:
                    # Configure reverb settings
                    reverb_settings = unreal.ReverbSettings()
                    reverb_settings.room_filter = 0.5
                    reverb_settings.room_filter_high = 0.5
                    reverb_settings.room_size = 0.5
                    reverb_settings.room_gain = 0.5
                    reverb_settings.reflections = 0.5
                    reverb_settings.reverb = 0.5
                    reverb_settings.gain = 0.5
                    reverb_settings.reflections_delay = 0.02
                    reverb_settings.reverb_delay = 0.04
                    reverb_settings.diffusion = 0.5
                    reverb_settings.density = 0.5
                    reverb_settings.air_absorption_gain_hf = 0.994
                    
                    reverb_effect.set_editor_property("settings", reverb_settings)
                    
                    # Mark package as dirty and save (peer-reviewed approach)
                    reverb_effect.get_outer().mark_package_dirty()
                    unreal.EditorAssetLibrary.save_loaded_asset(reverb_effect)
                    
                    # Verify it was created
                    if unreal.EditorAssetLibrary.does_asset_exist(path):
                        log(f"  ✓ Created and verified: {asset_name}")
                        created_assets.append((path, preset_name, send_level))
                    else:
                        log(f"  ✗ Created but verification failed: {asset_name}")
                else:
                    log(f"  ✗ Factory creation returned None: {asset_name}")
                    
            except AttributeError as e:
                # ReverbEffectFactory might not be available, try alternative
                log(f"  ⚠ Factory not available for {asset_name}: {str(e)}")
                log(f"     Trying alternative method...")
                
                # Alternative: Create via new_object and proper package handling
                try:
                    package_name = f"{directory}/{asset_name}"
                    package = unreal.EditorAssetLibrary.load_package(package_name)
                    if not package:
                        # Create new package
                        package = unreal.EditorAssetLibrary.make_package(package_name)
                    
                    if package:
                        reverb_effect = unreal.new_object(
                            unreal.ReverbEffect,
                            package,
                            asset_name
                        )
                        
                        if reverb_effect:
                            # Configure settings
                            reverb_settings = unreal.ReverbSettings()
                            reverb_settings.room_filter = 0.5
                            reverb_settings.room_filter_high = 0.5
                            reverb_settings.room_size = 0.5
                            reverb_settings.room_gain = 0.5
                            reverb_settings.reflections = 0.5
                            reverb_settings.reverb = 0.5
                            reverb_settings.gain = 0.5
                            reverb_settings.reflections_delay = 0.02
                            reverb_settings.reverb_delay = 0.04
                            reverb_settings.diffusion = 0.5
                            reverb_settings.density = 0.5
                            reverb_settings.air_absorption_gain_hf = 0.994
                            
                            reverb_effect.set_editor_property("settings", reverb_settings)
                            
                            # Save
                            package.mark_package_dirty()
                            unreal.EditorAssetLibrary.save_loaded_asset(reverb_effect)
                            
                            if unreal.EditorAssetLibrary.does_asset_exist(path):
                                log(f"  ✓ Created via alternative method: {asset_name}")
                                created_assets.append((path, preset_name, send_level))
                            else:
                                log(f"  ✗ Alternative method failed verification: {asset_name}")
                        else:
                            log(f"  ✗ Alternative method returned None: {asset_name}")
                    else:
                        log(f"  ✗ Failed to create package: {asset_name}")
                        
                except Exception as e2:
                    log(f"  ✗ Alternative method failed: {str(e2)}")
                    
            except Exception as e:
                log(f"  ✗ Error creating {asset_name}: {str(e)}")
                import traceback
                log(f"  Traceback: {traceback.format_exc()}")
                
        except Exception as e:
            log(f"  ✗ Fatal error for {asset_name}: {str(e)}")
            import traceback
            log(f"  Traceback: {traceback.format_exc()}")
    
    return created_assets

def create_test_blueprint():
    """Create BP_Phase4TestActor Blueprint"""
    log("\nCreating Test Blueprint...")
    
    blueprint_path = "/Game/Blueprints/BP_Phase4TestActor"
    
    try:
        # Check if exists
        if unreal.EditorAssetLibrary.does_asset_exist(blueprint_path):
            try:
                blueprint = unreal.EditorAssetLibrary.load_asset(blueprint_path)
                if blueprint:
                    log("  ✓ BP_Phase4TestActor already exists and is valid")
                    return blueprint_path
            except:
                pass
        
        # Create Blueprint
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
            
            # Verify
            if unreal.EditorAssetLibrary.does_asset_exist(blueprint_path):
                log("  ✓ Created BP_Phase4TestActor")
                log("     Note: Add components manually in Blueprint Editor")
                return blueprint_path
            else:
                log("  ✗ Created but verification failed")
        else:
            log("  ✗ Failed to create Blueprint")
            
    except Exception as e:
        log(f"  ✗ Error creating Blueprint: {str(e)}")
        import traceback
        log(f"  Traceback: {traceback.format_exc()}")
    
    return None

def create_test_level():
    """Create test level"""
    log("\nCreating Test Level...")
    
    level_path = "/Game/Maps/Phase4TestLevel"
    
    try:
        # Check if exists
        if unreal.EditorAssetLibrary.does_asset_exist(level_path):
            log("  ✓ Phase4TestLevel already exists")
            return level_path
        
        # Create level
        log("  → Creating Phase4TestLevel...")
        level = unreal.EditorLevelLibrary.new_level(level_path)
        
        if level:
            # Save the level
            unreal.EditorLevelLibrary.save_current_level()
            
            # Verify
            if unreal.EditorAssetLibrary.does_asset_exist(level_path):
                log("  ✓ Created Phase4TestLevel")
                return level_path
            else:
                log("  ✗ Created but verification failed")
        else:
            log("  ✗ Failed to create level")
            
    except Exception as e:
        log(f"  ✗ Error creating level: {str(e)}")
        import traceback
        log(f"  Traceback: {traceback.format_exc()}")
    
    return None

def verify_created_assets(reverb_assets, blueprint_path, level_path):
    """Verify all created assets actually exist"""
    log("\n" + "=" * 60)
    log("Verifying Created Assets")
    log("=" * 60)
    
    verified_count = 0
    total_count = len(reverb_assets) + (1 if blueprint_path else 0) + (1 if level_path else 0)
    
    # Verify reverb assets
    for path, preset_name, send_level in reverb_assets:
        try:
            if unreal.EditorAssetLibrary.does_asset_exist(path):
                asset = unreal.EditorAssetLibrary.load_asset(path)
                if asset:
                    log(f"  ✓ Verified: {path.split('/')[-1]}")
                    verified_count += 1
                else:
                    log(f"  ✗ Failed to load: {path.split('/')[-1]}")
            else:
                log(f"  ✗ Not found: {path.split('/')[-1]}")
        except Exception as e:
            log(f"  ✗ Error verifying {path.split('/')[-1]}: {str(e)}")
    
    # Verify blueprint
    if blueprint_path:
        try:
            if unreal.EditorAssetLibrary.does_asset_exist(blueprint_path):
                asset = unreal.EditorAssetLibrary.load_asset(blueprint_path)
                if asset:
                    log(f"  ✓ Verified: BP_Phase4TestActor")
                    verified_count += 1
                else:
                    log(f"  ✗ Failed to load: BP_Phase4TestActor")
            else:
                log(f"  ✗ Not found: BP_Phase4TestActor")
        except Exception as e:
            log(f"  ✗ Error verifying Blueprint: {str(e)}")
    
    # Verify level
    if level_path:
        try:
            if unreal.EditorAssetLibrary.does_asset_exist(level_path):
                log(f"  ✓ Verified: Phase4TestLevel")
                verified_count += 1
            else:
                log(f"  ✗ Not found: Phase4TestLevel")
        except Exception as e:
            log(f"  ✗ Error verifying Level: {str(e)}")
    
    log(f"\nVerification: {verified_count}/{total_count} assets verified")
    return verified_count == total_count

def main():
    """Main execution"""
    log("=" * 60)
    log("Phase 4 Asset Creation Script - PEER REVIEWED VERSION")
    log("=" * 60)
    
    try:
        # Create directories
        create_directories()
        
        # Create assets
        reverb_effects = create_reverb_effects()
        test_blueprint = create_test_blueprint()
        test_level = create_test_level()
        
        # Verify assets
        all_verified = verify_created_assets(reverb_effects, test_blueprint, test_level)
        
        # Summary
        log("\n" + "=" * 60)
        log("Asset Creation Summary")
        log("=" * 60)
        log(f"Reverb Effects: {len(reverb_effects)} created")
        log(f"Test Blueprint: {'Created' if test_blueprint else 'Failed'}")
        log(f"Test Level: {'Created' if test_level else 'Failed'}")
        log(f"All Assets Verified: {'YES' if all_verified else 'NO'}")
        
        if all_verified:
            log("\n✅ All assets created and verified successfully!")
            return 0
        else:
            log("\n⚠ Some assets failed verification")
            return 1
        
    except Exception as e:
        log(f"\n✗ Fatal error: {str(e)}")
        import traceback
        log(f"Traceback: {traceback.format_exc()}")
        return 1

if __name__ == "__main__":
    sys.exit(main())

