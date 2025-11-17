"""
Language System Service - FastAPI server.
Provides unified API for localization, TTS, and timing operations.
"""
import os
import logging
from typing import Optional, Dict, List
from contextlib import asynccontextmanager
import asyncpg
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app
from pydantic import BaseModel, Field

from services.localization.service import LocalizationService
from services.localization.repository import LocalizationRepository
from .language_gateway import (
    LanguageSystemGateway, LocalizationRequest, LocalizationResult,
    LocalizationMode
)
from .tts_manager import TTSManager
from .timing_manager import TimingManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
db_pool: Optional[asyncpg.Pool] = None
gateway: Optional[LanguageSystemGateway] = None


# API Models
class ProcessRequest(BaseModel):
    """API model for localization processing request."""
    key: str
    language_code: str
    mode: str = LocalizationMode.TEXT_ONLY.value
    context: Optional[Dict] = None
    speaker_id: Optional[str] = None
    archetype_id: Optional[str] = None
    emotion: Optional[str] = None
    generate_audio: bool = True
    generate_timing: bool = True
    audio_quality: str = "high"


class ProcessBatchRequest(BaseModel):
    """API model for batch processing."""
    requests: List[ProcessRequest]
    parallel: bool = True


class DialogueEntry(BaseModel):
    """Single dialogue entry."""
    key: str
    speaker_id: Optional[str] = None
    archetype_id: Optional[str] = None
    emotion: Optional[str] = None
    context: Optional[Dict] = None


class ProcessDialogueRequest(BaseModel):
    """API model for dialogue processing."""
    entries: List[DialogueEntry]
    language_code: str
    mode: str = LocalizationMode.FULL_SYNC.value


class PregenerateRequest(BaseModel):
    """API model for asset pre-generation."""
    language_code: str
    categories: List[str]
    force_regenerate: bool = False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    global db_pool, gateway
    
    # Startup
    logger.info("Starting language system service...")
    
    try:
        # Create database connection pool
        db_pool = await asyncpg.create_pool(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', '5432')),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'postgres'),
            database=os.getenv('DB_NAME', 'body_broker'),
            min_size=10,
            max_size=20,
            command_timeout=60
        )
        logger.info("Database connection pool created")
        
        # Initialize services
        localization_repo = LocalizationRepository(db_pool)
        localization_service = LocalizationService(localization_repo)
        
        # TTS configuration
        tts_config = {
            'azure_cognitive_enabled': os.getenv('AZURE_TTS_ENABLED', 'true') == 'true',
            'azure_cognitive': {
                'subscription_key': os.getenv('AZURE_TTS_KEY'),
                'region': os.getenv('AZURE_TTS_REGION', 'eastus')
            },
            'google_cloud_enabled': os.getenv('GOOGLE_TTS_ENABLED', 'false') == 'true',
            'google_cloud': {
                'credentials_path': os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
            },
            'aws_polly_enabled': os.getenv('AWS_POLLY_ENABLED', 'false') == 'true',
            'aws_polly': {
                'region': os.getenv('AWS_REGION', 'us-east-1')
            },
            'eleven_labs_enabled': os.getenv('ELEVEN_LABS_ENABLED', 'false') == 'true',
            'eleven_labs': {
                'api_key': os.getenv('ELEVEN_LABS_API_KEY')
            }
        }
        
        tts_manager = TTSManager(tts_config)
        
        # Timing configuration
        timing_config = {
            'english_phoneme_enabled': True,
            'japanese_phoneme_enabled': True,
            'subtitle_max_chars': 40,
            'subtitle_max_duration': 7.0,
            'subtitle_min_duration': 1.0
        }
        
        timing_manager = TimingManager(timing_config)
        
        # Gateway configuration
        gateway_config = {
            'max_parallel_requests': 10,
            'cache_enabled': True
        }
        
        # Create gateway
        gateway = LanguageSystemGateway(
            localization_service,
            tts_manager,
            timing_manager,
            gateway_config
        )
        
        logger.info("Language system gateway initialized")
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down language system service...")
    
    if db_pool:
        await db_pool.close()
        logger.info("Database connection pool closed")


# Create FastAPI app
app = FastAPI(
    title="Language System Service",
    description="Unified API for localization, TTS, and timing operations",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


# API Routes

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "language_system",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Service health check."""
    return {
        "service": "language_system",
        "status": "healthy"
    }


@app.post("/api/v1/process")
async def process_localization(request: ProcessRequest):
    """
    Process a single localization request.
    
    Handles text retrieval, optional audio generation, and timing data.
    """
    if not gateway:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    try:
        # Convert API model to internal request
        internal_request = LocalizationRequest(
            key=request.key,
            language_code=request.language_code,
            mode=LocalizationMode(request.mode),
            context=request.context,
            speaker_id=request.speaker_id,
            archetype_id=request.archetype_id,
            emotion=request.emotion,
            generate_audio=request.generate_audio,
            generate_timing=request.generate_timing,
            audio_quality=request.audio_quality
        )
        
        # Process request
        result = await gateway.process_request(internal_request)
        
        # Convert result to API response
        response = {
            'key': result.key,
            'language_code': result.language_code,
            'text': result.text,
            'mode': result.mode.value,
            'cached': result.cached,
            'processing_time_ms': result.processing_time_ms,
            'warnings': result.warnings
        }
        
        # Add audio data if present
        if result.audio_data:
            # In production, would store audio and return URL
            response['audio'] = {
                'sample_rate': result.audio_sample_rate,
                'duration_seconds': result.audio_duration,
                'data_size_bytes': len(result.audio_data)
            }
        
        # Add timing data if present
        if result.timing_data:
            response['timing'] = {
                'duration': result.timing_data.audio_duration,
                'phoneme_count': len(result.timing_data.phoneme_markers),
                'viseme_count': len(result.timing_data.viseme_markers),
                'word_count': len(result.timing_data.word_markers),
                'subtitle_count': len(result.timing_data.subtitle_markers)
            }
        
        return response
        
    except Exception as e:
        logger.error(f"Processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/process/batch")
async def process_batch(request: ProcessBatchRequest):
    """Process multiple localization requests."""
    if not gateway:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    try:
        # Convert API models to internal requests
        internal_requests = []
        for req in request.requests:
            internal_request = LocalizationRequest(
                key=req.key,
                language_code=req.language_code,
                mode=LocalizationMode(req.mode),
                context=req.context,
                speaker_id=req.speaker_id,
                archetype_id=req.archetype_id,
                emotion=req.emotion,
                generate_audio=req.generate_audio,
                generate_timing=req.generate_timing,
                audio_quality=req.audio_quality
            )
            internal_requests.append(internal_request)
        
        # Process batch
        results = await gateway.process_batch(
            internal_requests,
            parallel=request.parallel
        )
        
        # Convert results to API response
        response_results = []
        for result in results:
            response = {
                'key': result.key,
                'language_code': result.language_code,
                'text': result.text,
                'mode': result.mode.value,
                'cached': result.cached,
                'processing_time_ms': result.processing_time_ms,
                'warnings': result.warnings
            }
            
            if result.audio_data:
                response['audio'] = {
                    'sample_rate': result.audio_sample_rate,
                    'duration_seconds': result.audio_duration,
                    'data_size_bytes': len(result.audio_data)
                }
            
            if result.timing_data:
                response['timing'] = {
                    'duration': result.timing_data.audio_duration,
                    'subtitle_count': len(result.timing_data.subtitle_markers)
                }
            
            response_results.append(response)
        
        return {
            'count': len(response_results),
            'results': response_results
        }
        
    except Exception as e:
        logger.error(f"Batch processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/process/dialogue")
async def process_dialogue(request: ProcessDialogueRequest):
    """Process a complete dialogue sequence."""
    if not gateway:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    try:
        # Convert entries to dicts
        dialogue_entries = []
        for entry in request.entries:
            dialogue_entries.append({
                'key': entry.key,
                'speaker_id': entry.speaker_id,
                'archetype_id': entry.archetype_id,
                'emotion': entry.emotion,
                'context': entry.context
            })
        
        # Process dialogue
        results = await gateway.process_dialogue(
            dialogue_entries,
            request.language_code,
            LocalizationMode(request.mode)
        )
        
        # Convert results (simplified for API)
        response_results = []
        for result in results:
            response = {
                'key': result.key,
                'text': result.text,
                'audio_duration': result.audio_duration if result.audio_data else None,
                'has_timing': result.timing_data is not None,
                'warnings': result.warnings
            }
            response_results.append(response)
        
        return {
            'language_code': request.language_code,
            'count': len(response_results),
            'entries': response_results
        }
        
    except Exception as e:
        logger.error(f"Dialogue processing error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/validate/{language_code}")
async def validate_localization(
    language_code: str,
    categories: Optional[List[str]] = Body(None)
):
    """Validate localization completeness and quality."""
    if not gateway:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    try:
        validation_result = await gateway.validate_localization(
            language_code, categories
        )
        return validation_result
        
    except Exception as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/pregenerate")
async def pregenerate_assets(request: PregenerateRequest):
    """Pre-generate localization assets for a language."""
    if not gateway:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    try:
        stats = await gateway.pregenerate_assets(
            request.language_code,
            request.categories,
            request.force_regenerate
        )
        return stats
        
    except Exception as e:
        logger.error(f"Pre-generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/features/{language_code}")
async def get_supported_features(language_code: str):
    """Get supported features for a language."""
    if not gateway:
        raise HTTPException(status_code=500, detail="Service not initialized")
    
    try:
        features = await gateway.get_supported_features(language_code)
        return {
            'language_code': language_code,
            'features': features
        }
        
    except Exception as e:
        logger.error(f"Feature check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def run_server():
    """Run the FastAPI server."""
    import uvicorn
    
    host = os.getenv('SERVICE_HOST', '0.0.0.0')
    port = int(os.getenv('SERVICE_PORT', '8081'))
    
    logger.info(f"Starting server on {host}:{port}")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )


if __name__ == "__main__":
    run_server()
