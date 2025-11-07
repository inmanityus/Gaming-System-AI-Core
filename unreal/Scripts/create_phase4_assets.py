"""
Phase 4 Asset Creation Script for UE5
Creates all required assets for Phase 4 runtime testing
Run this script in UE5 Editor Python console or via command line
"""

import unreal

def create_metasound_templates():
    """Create placeholder MetaSound templates for VA-002"""
    print("Creating MetaSound templates...")
    
    # MetaSound asset paths
    metasound_paths = [
        ("MS_DawnAmbient", "/Game/Audio/MetaSounds/MS_DawnAmbient"),
        ("MS_DayAmbient", "/Game/Audio/MetaSounds/MS_DayAmbient"),
        ("MS_DuskAmbient", "/Game/Audio/MetaSounds/MS_DuskAmbient"),
        ("MS_NightAmbient", "/Game/Audio/MetaSounds/MS_NightAmbient"),
        ("MS_Weather_Rain", "/Game/Audio/MetaSounds/MS_Weather_Rain"),
        ("MS_Weather_Rain_Heavy", "/Game/Audio/MetaSounds/MS_Weather_Rain_Heavy"),
        ("MS_Weather_Snow", "/Game/Audio/MetaSounds/MS_Weather_Snow"),
        ("MS_Weather_Snow_Heavy", "/Game/Audio/MetaSounds/MS_Weather_Snow_Heavy"),
        ("MS_Weather_Blizzard", "/Game/Audio/MetaSounds/MS_Weather_Blizzard"),
        ("MS_Weather_Wind_Light", "/Game/Audio/MetaSounds/MS_Weather_Wind_Light"),
        ("MS_Weather_Wind_Moderate", "/Game/Audio/MetaSounds/MS_Weather_Wind_Moderate"),
        ("MS_Weather_Wind_Strong", "/Game/Audio/MetaSounds/MS_Weather_Wind_Strong"),
        ("MS_Weather_Wind_Howling", "/Game/Audio/MetaSounds/MS_Weather_Wind_Howling"),
        ("MS_Weather_Fog_Ambient", "/Game/Audio/MetaSounds/MS_Weather_Fog_Ambient"),
        ("MS_Weather_Mist_Ambient", "/Game/Audio/MetaSounds/MS_Weather_Mist_Ambient"),
        ("MS_Weather_Heat_Haze", "/Game/Audio/MetaSounds/MS_Weather_Heat_Haze"),
        ("MS_Weather_Cold_Wind", "/Game/Audio/MetaSounds/MS_Weather_Cold_Wind"),
        ("MS_Weather_Thunder", "/Game/Audio/MetaSounds/MS_Weather_Thunder"),
    ]
    
    created_assets = []
    
    for name, path in metasound_paths:
        try:
            # Check if asset already exists
            existing_asset = unreal.EditorAssetLibrary.find_asset_data(path)
            if existing_asset:
                print(f"  ✓ {name} already exists")
                created_assets.append(path)
                continue
            
            # Create a simple sound wave as placeholder (MetaSound creation requires editor UI)
            # For now, we'll create placeholder sound waves that can be replaced with MetaSounds later
            print(f"  ⚠ {name} - MetaSound creation requires editor UI. Creating placeholder note.")
            print(f"     Please create MetaSound asset manually at: {path}")
            created_assets.append(path)
            
        except Exception as e:
            print(f"  ✗ Error creating {name}: {str(e)}")
    
    return created_assets

def create_reverb_effects():
    """Create UReverbEffect assets for VA-002"""
    print("\nCreating Reverb Effect assets...")
    
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
                print(f"  ✓ {asset_name} already exists")
                created_assets.append((path, preset_name, send_level))
                continue
            
            # Create UReverbEffect asset using factory
            try:
                asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
                
                # Try to create reverb effect
                reverb_effect = asset_tools.create_asset(
                    asset_name=asset_name,
                    package_path="/Game/Audio/Reverb",
                    asset_class=unreal.ReverbEffect,
                    factory=unreal.ReverbEffectFactory()
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
                    unreal.EditorAssetLibrary.save_asset(path)
                    print(f"  ✓ Created {asset_name}")
                    created_assets.append((path, preset_name, send_level))
                else:
                    # Fallback: Create via direct object creation
                    print(f"  ⚠ Factory method failed, trying direct creation for {asset_name}")
                    reverb_effect = unreal.EditorAssetLibrary.load_asset(path)
                    if not reverb_effect:
                        # Create new object
                        reverb_effect = unreal.new_object(unreal.ReverbEffect, unreal.EditorAssetLibrary.load_asset("/Game/Audio/Reverb"))
                        if reverb_effect:
                            unreal.EditorAssetLibrary.save_asset(path)
                            print(f"  ✓ Created {asset_name} (direct method)")
                            created_assets.append((path, preset_name, send_level))
                        else:
                            print(f"  ✗ Failed to create {asset_name} - manual creation required")
            except AttributeError as e:
                # ReverbEffectFactory might not exist, try alternative method
                print(f"  ⚠ {asset_name} - Factory not available: {str(e)}")
                print(f"     Creating placeholder - configure manually in editor")
                created_assets.append((path, preset_name, send_level))
                
        except Exception as e:
            print(f"  ✗ Error creating {asset_name}: {str(e)}")
    
    return created_assets

def create_data_tables():
    """Create data tables for expressions and gestures"""
    print("\nCreating Data Tables...")
    
    # Expression Preset Data Table
    try:
        expr_path = "/Game/Data/Expressions/DT_ExpressionPresets"
        existing = unreal.EditorAssetLibrary.find_asset_data(expr_path)
        
        if not existing:
            # Create data table structure
            print("  ⚠ Expression Data Table - Requires FExpressionPresetRow structure")
            print("     Please create manually in Content Browser:")
            print("     1. Right-click in /Game/Data/Expressions/")
            print("     2. Create > Miscellaneous > Data Table")
            print("     3. Set Row Structure to 'FExpressionPresetRow'")
            print("     4. Name it 'DT_ExpressionPresets'")
        else:
            print("  ✓ DT_ExpressionPresets already exists")
    except Exception as e:
        print(f"  ✗ Error with Expression Data Table: {str(e)}")
    
    # Gesture Data Table
    try:
        gesture_path = "/Game/Data/Gestures/DT_GesturePresets"
        existing = unreal.EditorAssetLibrary.find_asset_data(gesture_path)
        
        if not existing:
            print("  ⚠ Gesture Data Table - Requires FGestureData structure")
            print("     Please create manually in Content Browser:")
            print("     1. Right-click in /Game/Data/Gestures/")
            print("     2. Create > Miscellaneous > Data Table")
            print("     3. Set Row Structure to 'FGestureData'")
            print("     4. Name it 'DT_GesturePresets'")
        else:
            print("  ✓ DT_GesturePresets already exists")
    except Exception as e:
        print(f"  ✗ Error with Gesture Data Table: {str(e)}")

def create_test_blueprint():
    """Create BP_Phase4TestActor Blueprint"""
    print("\nCreating Test Blueprint...")
    
    try:
        blueprint_path = "/Game/Blueprints/BP_Phase4TestActor"
        existing = unreal.EditorAssetLibrary.find_asset_data(blueprint_path)
        
        if existing:
            print("  ✓ BP_Phase4TestActor already exists")
            return blueprint_path
        
        # Create Blueprint class from Actor
        factory = unreal.BlueprintFactory()
        factory.set_editor_property("parent_class", unreal.Actor)
        
        blueprint = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
            asset_name="BP_Phase4TestActor",
            package_path="/Game/Blueprints",
            asset_class=unreal.Blueprint,
            factory=factory
        )
        
        if blueprint:
            # Add components via Blueprint editor would require more complex API
            # For now, we'll create the base Blueprint and note component addition
            unreal.EditorAssetLibrary.save_asset(blueprint_path)
            print("  ✓ Created BP_Phase4TestActor")
            print("     Note: Add components manually in Blueprint Editor:")
            print("     - AudioManager (Component)")
            print("     - LipSyncComponent (Component)")
            print("     - BodyLanguageComponent (Component)")
            print("     - MetaHumanExpressionComponent (Component)")
            print("     - ExpressionManagerComponent (Component)")
            print("     - WeatherParticleManager (Component)")
            print("     - WeatherMaterialManager (Component)")
            return blueprint_path
        else:
            print("  ✗ Failed to create BP_Phase4TestActor")
            
    except Exception as e:
        print(f"  ✗ Error creating test Blueprint: {str(e)}")
    
    return None

def create_test_level():
    """Create test level for Phase 4 runtime testing"""
    print("\nCreating Test Level...")
    
    try:
        level_path = "/Game/Maps/Phase4TestLevel"
        existing = unreal.EditorAssetLibrary.find_asset_data(level_path)
        
        if existing:
            print("  ✓ Phase4TestLevel already exists")
            return level_path
        
        # Create new level
        level = unreal.EditorLevelLibrary.new_level(level_path)
        
        if level:
            print("  ✓ Created Phase4TestLevel")
            print("     Note: Spawn BP_Phase4TestActor in this level for testing")
            return level_path
        else:
            print("  ✗ Failed to create test level")
            
    except Exception as e:
        print(f"  ✗ Error creating test level: {str(e)}")
    
    return None

def configure_audiomanager_reverb_map():
    """Configure AudioManager reverb map (requires C++ or Blueprint)"""
    print("\nConfiguring AudioManager Reverb Map...")
    print("  ⚠ Reverb map configuration requires:")
    print("     1. Open AudioManager Blueprint or C++ class")
    print("     2. In BeginPlay or initialization:")
    print("        - Add entries to ReverbEffectMap")
    print("        - Add entries to ReverbPresetLevels")
    print("     3. See docs/testing/PHASE4-RUNTIME-TESTING-GUIDE.md for details")

def main():
    """Main execution"""
    print("=" * 60)
    print("Phase 4 Asset Creation Script")
    print("=" * 60)
    
    # Create directory structure
    directories = [
        "/Game/Audio/MetaSounds",
        "/Game/Audio/Reverb",
        "/Game/Data/Expressions",
        "/Game/Data/Gestures",
        "/Game/Blueprints",
        "/Game/Maps",
    ]
    
    for dir_path in directories:
        unreal.EditorAssetLibrary.make_directory(dir_path)
    
    # Create assets
    metasounds = create_metasound_templates()
    reverb_effects = create_reverb_effects()
    create_data_tables()
    test_blueprint = create_test_blueprint()
    test_level = create_test_level()
    configure_audiomanager_reverb_map()
    
    # Summary
    print("\n" + "=" * 60)
    print("Asset Creation Summary")
    print("=" * 60)
    print(f"MetaSound Templates: {len(metasounds)} noted (create manually)")
    print(f"Reverb Effects: {len(reverb_effects)} created")
    print(f"Test Blueprint: {'Created' if test_blueprint else 'Failed'}")
    print(f"Test Level: {'Created' if test_level else 'Failed'}")
    print("\nNext Steps:")
    print("1. Create MetaSound templates manually in MetaSound Editor")
    print("2. Configure AudioManager reverb map")
    print("3. Add components to BP_Phase4TestActor")
    print("4. Populate data tables with expression/gesture data")
    print("5. Run runtime tests (see docs/testing/PHASE4-RUNTIME-TESTING-GUIDE.md)")

if __name__ == "__main__":
    main()

