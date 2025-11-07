# scripts/populate-ue5-features.py
"""
Populate Capability Registry with UE5.6.1 and UE5.7 features
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
import json

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=os.getenv("DB_PORT", "5432"),
        database=os.getenv("DB_NAME", "capabilities"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "postgres")
    )

def populate_features():
    """Populate features for UE5.6.1 and UE5.7"""
    conn = get_db_connection()
    
    try:
        with conn.cursor() as cur:
            # Get category IDs
            cur.execute("SELECT id, name FROM feature_categories")
            categories = {row[1]: row[0] for row in cur.fetchall()}
            
            # UE5.6.1 Features
            features_5_6_1 = [
                # Rendering
                ("nanite_virtualized_geometry", "rendering", 
                 "Virtualized geometry system for massive detail", 
                 "https://docs.unrealengine.com/5.6/en-US/nanite-virtualized-geometry-in-unreal-engine/",
                 "Use for rendering massive structures with millions of polygons"),
                ("lumen_global_illumination", "rendering",
                 "Dynamic global illumination system",
                 "https://docs.unrealengine.com/5.6/en-US/lumen-global-illumination-and-reflections-in-unreal-engine/",
                 "Use for realistic lighting with dynamic light bounces"),
                ("path_tracer", "rendering",
                 "Cinematic quality path tracing",
                 "https://docs.unrealengine.com/5.6/en-US/path-tracer-in-unreal-engine/",
                 "Use for offline rendering and cinematic sequences"),
                ("temporal_super_resolution", "rendering",
                 "High-quality temporal upscaling",
                 "https://docs.unrealengine.com/5.6/en-US/temporal-super-resolution-in-unreal-engine/",
                 "Use for high-quality rendering at lower resolutions"),
                
                # Audio
                ("metasound", "audio",
                 "Procedural audio system",
                 "https://docs.unrealengine.com/5.6/en-US/metasound-in-unreal-engine/",
                 "Use for dynamic, procedural audio generation"),
                ("spatial_audio", "audio",
                 "3D positional audio system",
                 "https://docs.unrealengine.com/5.6/en-US/spatial-audio-in-unreal-engine/",
                 "Use for realistic 3D sound positioning"),
                ("convolution_reverb", "audio",
                 "Realistic reverb simulation",
                 "https://docs.unrealengine.com/5.6/en-US/convolution-reverb-in-unreal-engine/",
                 "Use for realistic acoustic environments"),
                
                # Physics
                ("chaos_physics", "physics",
                 "Advanced destruction and physics",
                 "https://docs.unrealengine.com/5.6/en-US/chaos-physics-in-unreal-engine/",
                 "Use for realistic destruction and physics simulation"),
                ("cloth_simulation", "physics",
                 "Realistic fabric simulation",
                 "https://docs.unrealengine.com/5.6/en-US/cloth-simulation-in-unreal-engine/",
                 "Use for realistic clothing and fabric"),
                
                # AI
                ("mass_ai", "ai",
                 "Crowd simulation system",
                 "https://docs.unrealengine.com/5.6/en-US/mass-ai-in-unreal-engine/",
                 "Use for realistic crowd behaviors"),
                ("behavior_trees", "ai",
                 "NPC AI logic system",
                 "https://docs.unrealengine.com/5.6/en-US/behavior-trees-in-unreal-engine/",
                 "Use for complex NPC decision-making"),
                
                # World Building
                ("world_partition", "world_building",
                 "Large world streaming system",
                 "https://docs.unrealengine.com/5.6/en-US/world-partition-in-unreal-engine/",
                 "Use for massive open worlds"),
                ("data_layers", "world_building",
                 "Variant level content system",
                 "https://docs.unrealengine.com/5.6/en-US/data-layers-in-unreal-engine/",
                 "Use for dynamic level variants"),
                
                # Animation
                ("control_rig", "animation",
                 "Procedural animation system",
                 "https://docs.unrealengine.com/5.6/en-US/control-rig-in-unreal-engine/",
                 "Use for procedural character animation"),
                ("ik_retargeter", "animation",
                 "Animation retargeting system",
                 "https://docs.unrealengine.com/5.6/en-US/ik-retargeter-in-unreal-engine/",
                 "Use for retargeting animations between characters"),
            ]
            
            # Insert features
            for name, category, description, doc_url, example in features_5_6_1:
                cur.execute("""
                    INSERT INTO features (name, category_id, description, documentation_url, example_usage)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (name) DO UPDATE SET
                        description = EXCLUDED.description,
                        documentation_url = EXCLUDED.documentation_url,
                        example_usage = EXCLUDED.example_usage
                """, (name, categories[category], description, doc_url, example))
            
            # Link features to UE5.6.1
            cur.execute("SELECT id, name FROM features")
            feature_map = {row[1]: row[0] for row in cur.fetchall()}
            
            for name, _, _, _, _ in features_5_6_1:
                cur.execute("""
                    INSERT INTO version_features (version, feature_id, introduced_in)
                    VALUES ('5.6.1', %s, '5.6.1')
                    ON CONFLICT (version, feature_id) DO NOTHING
                """, (feature_map[name],))
            
            # UE5.7 Preview Features (enhanced versions)
            features_5_7 = [
                ("nanite_virtualized_geometry", "rendering", "Enhanced performance"),
                ("lumen_global_illumination", "rendering", "Improved quality and performance"),
            ]
            
            # Insert UE5.7 version
            cur.execute("""
                INSERT INTO ue_versions (version, release_date, is_preview, is_stable)
                VALUES ('5.7.0', CURRENT_DATE, TRUE, FALSE)
                ON CONFLICT (version) DO UPDATE SET is_preview = TRUE
            """)
            
            # Link enhanced features to UE5.7
            for name, category, enhancement in features_5_7:
                if name in feature_map:
                    cur.execute("""
                        INSERT INTO version_features (version, feature_id, introduced_in, config)
                        VALUES ('5.7.0', %s, '5.6.1', %s::jsonb)
                        ON CONFLICT (version, feature_id) DO UPDATE SET
                            config = EXCLUDED.config
                    """, (feature_map[name], json.dumps({"enhancement": enhancement})))
            
            conn.commit()
            print("✅ Features populated successfully")
            
    except Exception as e:
        conn.rollback()
        print(f"❌ Error populating features: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    populate_features()



