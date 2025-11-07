"""
Phase 4 Asset Creation Script - Enhanced Version
Creates assets programmatically and handles errors
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
    """Create UReverbEffect assets"""
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
        try:
            path = f"/Game/Audio/Reverb/{asset_name}"
            
            # Check if asset already exists
            existing_asset = unreal.EditorAssetLibrary.find_asset_data(path)
            if existing_asset:
                log(f"  ✓ {asset_name} already exists")
                created_assets.append((path, preset_name, send_level))
                continue
            
            # Try to create reverb effect using various methods
            reverb_effect = None
            
            # Method 1: Try factory
            try:
                asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
                factory = unreal.ReverbEffectFactory()
                factory.set_editor_property("supported_class", unreal.ReverbEffect)
                
                reverb_effect = asset_tools.create_asset(
                    asset_name=asset_name,
                    package_path="/Game/Audio/Reverb",
                    asset_class=unreal.ReverbEffect,
                    factory=factory
                )
            except Exception as e:
                log(f"  ⚠ Factory method failed for {asset_name}: {str(e)}")
            
            # Method 2: Try direct object creation
            if not reverb_effect:
                try:
                    # Create new object in package
                    package = unreal.EditorAssetLibrary.load_package("/Game/Audio/Reverb")
                    if package:
                        reverb_effect = unreal.new_object(unreal.ReverbEffect, package, asset_name)
                except Exception as e:
                    log(f"  ⚠ Direct creation failed for {asset_name}: {str(e)}")
            
            if reverb_effect:
                # Configure reverb settings
                try:
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
                    unreal.EditorAssetLibrary.save_asset(path)
                    log(f"  ✓ Created {asset_name}")
                    created_assets.append((path, preset_name, send_level))
                except Exception as e:
                    log(f"  ⚠ Settings configuration failed for {asset_name}: {str(e)}")
                    # Save anyway
                    unreal.EditorAssetLibrary.save_asset(path)
                    log(f"  ✓ Created {asset_name} (without settings)")
                    created_assets.append((path, preset_name, send_level))
            else:
                log(f"  ✗ Failed to create {asset_name} - manual creation required")
                
        except Exception as e:
            log(f"  ✗ Error creating {asset_name}: {str(e)}")
            import traceback
            log(f"  Traceback: {traceback.format_exc()}")
    
    return created_assets

def create_test_blueprint():
    """Create BP_Phase4TestActor Blueprint"""
    log("\nCreating Test Blueprint...")
    
    try:
        blueprint_path = "/Game/Blueprints/BP_Phase4TestActor"
        existing = unreal.EditorAssetLibrary.find_asset_data(blueprint_path)
        
        if existing:
            log("  ✓ BP_Phase4TestActor already exists")
            return blueprint_path
        
        # Create Blueprint class from Actor
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
            unreal.EditorAssetLibrary.save_asset(blueprint_path)
            log("  ✓ Created BP_Phase4TestActor")
            log("     Note: Add components manually in Blueprint Editor")
            return blueprint_path
        else:
            log("  ✗ Failed to create BP_Phase4TestActor")
            
    except Exception as e:
        log(f"  ✗ Error creating test Blueprint: {str(e)}")
        import traceback
        log(f"  Traceback: {traceback.format_exc()}")
    
    return None

def create_test_level():
    """Create test level"""
    log("\nCreating Test Level...")
    
    try:
        level_path = "/Game/Maps/Phase4TestLevel"
        existing = unreal.EditorAssetLibrary.find_asset_data(level_path)
        
        if existing:
            log("  ✓ Phase4TestLevel already exists")
            return level_path
        
        # Create new level
        level = unreal.EditorLevelLibrary.new_level(level_path)
        
        if level:
            log("  ✓ Created Phase4TestLevel")
            return level_path
        else:
            log("  ✗ Failed to create test level")
            
    except Exception as e:
        log(f"  ✗ Error creating test level: {str(e)}")
        import traceback
        log(f"  Traceback: {traceback.format_exc()}")
    
    return None

def main():
    """Main execution"""
    log("=" * 60)
    log("Phase 4 Asset Creation Script - Enhanced")
    log("=" * 60)
    
    try:
        # Create directories
        create_directories()
        
        # Create assets
        reverb_effects = create_reverb_effects()
        test_blueprint = create_test_blueprint()
        test_level = create_test_level()
        
        # Summary
        log("\n" + "=" * 60)
        log("Asset Creation Summary")
        log("=" * 60)
        log(f"Reverb Effects: {len(reverb_effects)} created")
        log(f"Test Blueprint: {'Created' if test_blueprint else 'Failed'}")
        log(f"Test Level: {'Created' if test_level else 'Failed'}")
        log("\nScript execution complete!")
        
    except Exception as e:
        log(f"\n✗ Fatal error: {str(e)}")
        import traceback
        log(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main()

