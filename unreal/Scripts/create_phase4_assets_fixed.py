"""
Phase 4 Asset Creation Script - FIXED VERSION
Properly creates assets and verifies they exist
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
    """Create UReverbEffect assets - FIXED VERSION"""
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
    
    for asset_name, preset_name, send_level in reverb_configs:
        path = f"/Game/Audio/Reverb/{asset_name}"
        
        try:
            # Check if asset exists - FIXED: Properly check, don't assume
            asset_data = None
            try:
                asset_data = unreal.EditorAssetLibrary.find_asset_data(path)
            except:
                pass  # Asset doesn't exist, which is fine
            
            if asset_data:
                # Verify it's actually loadable
                try:
                    asset = unreal.EditorAssetLibrary.load_asset(path)
                    if asset:
                        log(f"  ✓ {asset_name} already exists and is valid")
                        created_assets.append((path, preset_name, send_level))
                        continue
                except:
                    pass  # Asset data exists but can't load, recreate
            
            # Asset doesn't exist or is invalid - CREATE IT
            log(f"  → Creating {asset_name}...")
            
            # Method: Use EditorAssetLibrary to create asset directly
            # Create package path
            package_path = f"/Game/Audio/Reverb/{asset_name}"
            
            # Try creating via new_object in a package
            try:
                # Load or create package
                package = unreal.EditorAssetLibrary.load_package("/Game/Audio/Reverb")
                if not package:
                    # Package doesn't exist, create directory first
                    unreal.EditorAssetLibrary.make_directory("/Game/Audio/Reverb")
                    package = unreal.EditorAssetLibrary.load_package("/Game/Audio/Reverb")
                
                # Create ReverbEffect object
                reverb_effect = unreal.new_object(
                    unreal.ReverbEffect,
                    package,
                    asset_name
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
                    
                    # Save the asset
                    unreal.EditorAssetLibrary.save_asset(path, only_if_is_dirty=False)
                    
                    # Verify it was created
                    verify_data = unreal.EditorAssetLibrary.find_asset_data(path)
                    if verify_data:
                        log(f"  ✓ Created {asset_name}")
                        created_assets.append((path, preset_name, send_level))
                    else:
                        log(f"  ✗ Created but verification failed: {asset_name}")
                else:
                    log(f"  ✗ Failed to create object: {asset_name}")
                    
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
    """Create BP_Phase4TestActor Blueprint - FIXED VERSION"""
    log("\nCreating Test Blueprint...")
    
    blueprint_path = "/Game/Blueprints/BP_Phase4TestActor"
    
    try:
        # Check if exists - FIXED: Properly check
        asset_data = None
        try:
            asset_data = unreal.EditorAssetLibrary.find_asset_data(blueprint_path)
        except:
            pass
        
        if asset_data:
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
        
        blueprint = asset_tools.create_asset(
            asset_name="BP_Phase4TestActor",
            package_path="/Game/Blueprints",
            asset_class=unreal.Blueprint,
            factory=factory
        )
        
        if blueprint:
            # Save the asset
            unreal.EditorAssetLibrary.save_asset(blueprint_path, only_if_is_dirty=False)
            
            # Verify
            verify_data = unreal.EditorAssetLibrary.find_asset_data(blueprint_path)
            if verify_data:
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
    """Create test level - FIXED VERSION"""
    log("\nCreating Test Level...")
    
    level_path = "/Game/Maps/Phase4TestLevel"
    
    try:
        # Check if exists - FIXED: Properly check
        asset_data = None
        try:
            asset_data = unreal.EditorAssetLibrary.find_asset_data(level_path)
        except:
            pass
        
        if asset_data:
            try:
                level = unreal.EditorAssetLibrary.load_asset(level_path)
                if level:
                    log("  ✓ Phase4TestLevel already exists and is valid")
                    return level_path
            except:
                pass
        
        # Create level
        log("  → Creating Phase4TestLevel...")
        level = unreal.EditorLevelLibrary.new_level(level_path)
        
        if level:
            # Save the level
            unreal.EditorLevelLibrary.save_current_level()
            
            # Verify
            verify_data = unreal.EditorAssetLibrary.find_asset_data(level_path)
            if verify_data:
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
            asset_data = unreal.EditorAssetLibrary.find_asset_data(path)
            if asset_data:
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
            asset_data = unreal.EditorAssetLibrary.find_asset_data(blueprint_path)
            if asset_data:
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
            asset_data = unreal.EditorAssetLibrary.find_asset_data(level_path)
            if asset_data:
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
    log("Phase 4 Asset Creation Script - FIXED VERSION")
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

