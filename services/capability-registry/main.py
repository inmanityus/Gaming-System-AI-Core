# services/capability-registry/main.py
"""
Capability Registry Service
Stores and serves UE5 version capabilities to Storyteller
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional as Opt
import psycopg2
from psycopg2.extras import RealDictCursor
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

app = FastAPI(title="UE5 Capability Registry API")

# Pydantic models
class VersionCreate(BaseModel):
    version: str
    release_date: Opt[str] = None
    is_preview: Opt[bool] = False
    is_stable: Opt[bool] = True
    release_notes_url: Opt[str] = None

class VersionUpdate(BaseModel):
    release_date: Opt[str] = None
    is_preview: Opt[bool] = None
    is_stable: Opt[bool] = None
    release_notes_url: Opt[str] = None

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection pool
_db_pool = None

def get_db_connection():
    """Get database connection with connection pooling"""
    global _db_pool
    
    if _db_pool is None:
        from psycopg2 import pool
        _db_pool = pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=10,
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432"),
            database=os.getenv("DB_NAME", "capabilities"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "postgres")
        )
    
    return _db_pool.getconn()

def return_db_connection(conn):
    """Return connection to pool"""
    global _db_pool
    if _db_pool:
        _db_pool.putconn(conn)

@app.get("/api/v1/capabilities")
async def get_capabilities(
    version: Optional[str] = Query(None, description="UE5 version"),
    category: Optional[str] = Query(None, description="Feature category")
):
    """Get available capabilities for UE5 version"""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if version:
                # Get capabilities for specific version
                query = """
                    SELECT 
                        fc.name as category,
                        f.name,
                        f.description,
                        vf.introduced_in,
                        vf.deprecated_in,
                        vf.config
                    FROM version_features vf
                    JOIN features f ON vf.feature_id = f.id
                    JOIN feature_categories fc ON f.category_id = fc.id
                    WHERE vf.version = %s
                """
                params = [version]
                
                if category:
                    query += " AND fc.name = %s"
                    params.append(category)
                
                query += " ORDER BY fc.name, f.name"
                
                cur.execute(query, params)
                rows = cur.fetchall()
                
                # Group by category
                capabilities = {}
                for row in rows:
                    cat = row['category']
                    if cat not in capabilities:
                        capabilities[cat] = []
                    
                    capabilities[cat].append({
                        'name': row['name'],
                        'description': row['description'],
                        'introduced_in': row['introduced_in'],
                        'deprecated_in': row['deprecated_in'],
                        'config': row['config'] if row['config'] else {}
                    })
                
                return {
                    'version': version,
                    'capabilities': capabilities
                }
            else:
                # Get latest version capabilities
                cur.execute("""
                    SELECT version FROM ue_versions 
                    WHERE is_stable = TRUE 
                    ORDER BY release_date DESC 
                    LIMIT 1
                """)
                latest = cur.fetchone()
                if latest:
                    return await get_capabilities(version=latest['version'], category=category)
                else:
                    return {'version': None, 'capabilities': {}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if conn:
            return_db_connection(conn)

@app.get("/api/v1/versions")
async def get_versions():
    """Get all available UE5 versions"""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT version, release_date, is_preview, is_stable, release_notes_url
                FROM ue_versions
                ORDER BY release_date DESC
            """)
            rows = cur.fetchall()
            return [dict(row) for row in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if conn:
            return_db_connection(conn)

@app.get("/api/v1/versions/{version}")
async def get_version(version: str):
    """Get specific UE5 version details with capabilities"""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Get version info
            cur.execute("""
                SELECT version, release_date, is_preview, is_stable, release_notes_url
                FROM ue_versions
                WHERE version = %s
            """, [version])
            version_info = cur.fetchone()
            if not version_info:
                raise HTTPException(status_code=404, detail=f"Version {version} not found")
            
            # Get capabilities for this version - call the internal function directly
            conn_caps = get_db_connection()
            try:
                with conn_caps.cursor(cursor_factory=RealDictCursor) as cur_caps:
                    query = """
                        SELECT 
                            fc.name as category,
                            f.name,
                            f.description,
                            vf.introduced_in,
                            vf.deprecated_in,
                            vf.config
                        FROM version_features vf
                        JOIN features f ON vf.feature_id = f.id
                        JOIN feature_categories fc ON f.category_id = fc.id
                        WHERE vf.version = %s
                        ORDER BY fc.name, f.name
                    """
                    cur_caps.execute(query, [version])
                    rows = cur_caps.fetchall()
                    
                    # Group by category
                    capabilities = {}
                    for row in rows:
                        cat = row['category']
                        if cat not in capabilities:
                            capabilities[cat] = []
                        
                        capabilities[cat].append({
                            'name': row['name'],
                            'description': row['description'],
                            'introduced_in': row['introduced_in'],
                            'deprecated_in': row['deprecated_in'],
                            'config': row['config'] if row['config'] else {}
                        })
            finally:
                return_db_connection(conn_caps)
            
            return {
                **dict(version_info),
                'capabilities': capabilities
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if conn:
            return_db_connection(conn)

@app.post("/api/v1/versions")
async def create_version(version_data: VersionCreate):
    """Create a new UE5 version entry"""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO ue_versions (version, release_date, is_preview, is_stable, release_notes_url)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (version) DO UPDATE SET
                    release_date = EXCLUDED.release_date,
                    is_preview = EXCLUDED.is_preview,
                    is_stable = EXCLUDED.is_stable,
                    release_notes_url = EXCLUDED.release_notes_url
                RETURNING version
            """, (
                version_data.version,
                version_data.release_date,
                version_data.is_preview,
                version_data.is_stable,
                version_data.release_notes_url
            ))
            conn.commit()
            return {"version": cur.fetchone()[0], "status": "created"}
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=400, detail=f"Error creating version: {str(e)}")
    finally:
        if conn:
            return_db_connection(conn)

@app.put("/api/v1/versions/{version}")
async def update_version_endpoint(version: str, version_data: VersionUpdate):
    """Update an existing UE5 version"""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            # Check if version exists
            cur.execute("SELECT version FROM ue_versions WHERE version = %s", [version])
            if not cur.fetchone():
                raise HTTPException(status_code=404, detail=f"Version {version} not found")
            
            # Update version
            cur.execute("""
                UPDATE ue_versions
                SET release_date = COALESCE(%s, release_date),
                    is_preview = COALESCE(%s, is_preview),
                    is_stable = COALESCE(%s, is_stable),
                    release_notes_url = COALESCE(%s, release_notes_url)
                WHERE version = %s
                RETURNING version
            """, (
                version_data.release_date,
                version_data.is_preview,
                version_data.is_stable,
                version_data.release_notes_url,
                version
            ))
            conn.commit()
            return {"version": cur.fetchone()[0], "status": "updated"}
    except HTTPException:
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=400, detail=f"Error updating version: {str(e)}")
    finally:
        if conn:
            return_db_connection(conn)

@app.delete("/api/v1/versions/{version}")
async def delete_version(version: str):
    """Delete a UE5 version (requires authentication in production)"""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("DELETE FROM ue_versions WHERE version = %s RETURNING version", [version])
            deleted = cur.fetchone()
            if not deleted:
                raise HTTPException(status_code=404, detail=f"Version {version} not found")
            conn.commit()
            return {"status": "deleted", "version": deleted[0]}
    except HTTPException:
        raise
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting version: {str(e)}")
    finally:
        if conn:
            return_db_connection(conn)

@app.get("/api/v1/features/{feature_name}")
async def get_feature_details(feature_name: str):
    """Get detailed information about a specific feature"""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT 
                    f.id,
                    f.name,
                    f.description,
                    f.documentation_url,
                    f.example_usage,
                    fc.name as category
                FROM features f
                JOIN feature_categories fc ON f.category_id = fc.id
                WHERE f.name = %s
            """, [feature_name])
            
            feature = cur.fetchone()
            if not feature:
                raise HTTPException(status_code=404, detail="Feature not found")
            
            # Get parameters
            cur.execute("""
                SELECT parameter_name, parameter_type, default_value, description
                FROM feature_parameters
                WHERE feature_id = %s
            """, [feature['id']])
            
            parameters = [dict(row) for row in cur.fetchall()]
            
            return {
                **dict(feature),
                'parameters': parameters
            }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        if conn:
            return_db_connection(conn)

@app.get("/api/v1/suggestions")
async def get_suggestions(
    context: str = Query(..., description="Story context"),
    version: Optional[str] = Query(None, description="UE5 version")
):
    """Get feature suggestions based on story context"""
    capabilities = await get_capabilities(version=version)
    
    suggestions = []
    context_lower = context.lower()
    
    # Simple keyword-based suggestions (can be enhanced with NLP)
    if "underground" in context_lower or "cavern" in context_lower:
        if "lumen" in str(capabilities.get('capabilities', {}).get('rendering', [])):
            suggestions.append(
                "Use Lumen global illumination for realistic underground lighting"
            )
    
    if "crowd" in context_lower or "city" in context_lower:
        if "mass_ai" in str(capabilities.get('capabilities', {}).get('ai', [])):
            suggestions.append(
                "Use Mass AI to create realistic crowd behaviors"
            )
    
    if "weather" in context_lower:
        if "niagara" in str(capabilities.get('capabilities', {}).get('rendering', [])):
            suggestions.append(
                "Use Niagara particle systems for dynamic weather effects"
            )
    
    return {
        'context': context,
        'version': capabilities.get('version'),
        'suggestions': suggestions
    }

@app.post("/api/v1/versions/{version}/update")
async def update_version(version: str):
    """Update capability registry for a new UE5 version"""
    # This would be called by the update automation system
    # Implementation would parse release notes and extract features
    return {"status": "update_initiated", "version": version}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)

