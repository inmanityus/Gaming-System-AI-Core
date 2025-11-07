"""
Verify Created Assets - Load and Validate
"""

import unreal
import sys

def log(message):
    """Log message"""
    print(message)
    unreal.log(message)

def verify_reverb_assets():
    """Verify all reverb assets can be loaded"""
    log("\n" + "=" * 60)
    log("Verifying Reverb Assets Can Be Loaded")
    log("=" * 60)
    
    reverb_paths = [
        "/Game/Audio/Reverb/RE_Interior_Small",
        "/Game/Audio/Reverb/RE_Interior_Large",
        "/Game/Audio/Reverb/RE_Exterior_Open",
        "/Game/Audio/Reverb/RE_Exterior_Urban",
        "/Game/Audio/Reverb/RE_Exterior_Forest",
        "/Game/Audio/Reverb/RE_Exterior_Cave",
    ]
    
    verified_count = 0
    
    for path in reverb_paths:
        try:
            if unreal.EditorAssetLibrary.does_asset_exist(path):
                asset = unreal.EditorAssetLibrary.load_asset(path)
                if asset:
                    # Check if it's actually a ReverbEffect
                    if isinstance(asset, unreal.ReverbEffect):
                        log(f"  ✓ {path.split('/')[-1]} - Valid ReverbEffect")
                        verified_count += 1
                    else:
                        log(f"  ⚠ {path.split('/')[-1]} - Wrong type: {type(asset)}")
                else:
                    log(f"  ✗ {path.split('/')[-1]} - Failed to load")
            else:
                log(f"  ✗ {path.split('/')[-1]} - Not found")
        except Exception as e:
            log(f"  ✗ {path.split('/')[-1]} - Error: {str(e)}")
    
    log(f"\nVerification: {verified_count}/{len(reverb_paths)} assets loaded successfully")
    return verified_count == len(reverb_paths)

def main():
    """Main execution"""
    log("=" * 60)
    log("Asset Verification Script")
    log("=" * 60)
    
    all_valid = verify_reverb_assets()
    
    if all_valid:
        log("\n✅ All assets verified and can be loaded!")
        return 0
    else:
        log("\n⚠ Some assets failed verification")
        return 1

if __name__ == "__main__":
    sys.exit(main())

