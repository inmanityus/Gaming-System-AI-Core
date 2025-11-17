"""
Media storage handler for audio segments
"""
import os
import asyncio
import aiofiles
import logging
from pathlib import Path
from typing import Optional, Tuple
import numpy as np
import wave
import struct
from datetime import datetime


logger = logging.getLogger(__name__)


class MediaStorageHandler:
    """Handles storage of audio segments to media storage."""
    
    def __init__(self, base_path: str = "/media/audio", use_s3: bool = False):
        self.base_path = Path(base_path)
        self.use_s3 = use_s3
        
        # Create base directory if local storage
        if not use_s3:
            self.base_path.mkdir(parents=True, exist_ok=True)
    
    def _generate_file_path(self, segment_id: str, build_id: str, format: str = 'wav') -> Tuple[Path, str]:
        """Generate file path and URI for a segment."""
        # Organize by build and date
        date_str = datetime.utcnow().strftime('%Y-%m-%d')
        relative_path = Path(build_id) / date_str / f"{segment_id}.{format}"
        full_path = self.base_path / relative_path
        
        # Generate URI
        if self.use_s3:
            uri = f"s3://ethelred-audio/{relative_path}"
        else:
            uri = f"redalert://media/audio/{relative_path}"
        
        return full_path, uri
    
    async def store_segment(self, 
                          audio_data: np.ndarray,
                          sample_rate: int,
                          segment_id: str,
                          build_id: str,
                          format: str = 'wav') -> str:
        """Store audio segment and return media URI."""
        file_path, uri = self._generate_file_path(segment_id, build_id, format)
        
        # Ensure directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == 'wav':
            await self._write_wav(file_path, audio_data, sample_rate)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        logger.info(f"Stored audio segment {segment_id} to {uri}")
        return uri
    
    async def _write_wav(self, file_path: Path, audio_data: np.ndarray, sample_rate: int):
        """Write audio data to WAV file."""
        # Normalize audio data to 16-bit range if needed
        if audio_data.dtype == np.float32 or audio_data.dtype == np.float64:
            # Convert float [-1, 1] to int16
            audio_data = np.clip(audio_data * 32767, -32768, 32767).astype(np.int16)
        elif audio_data.dtype != np.int16:
            # Convert to int16
            audio_data = audio_data.astype(np.int16)
        
        # Determine number of channels
        if len(audio_data.shape) == 1:
            channels = 1
            frames = audio_data
        else:
            channels = audio_data.shape[1]
            # Interleave channels for WAV format
            frames = audio_data.flatten('C')
        
        # Write WAV file
        with wave.open(str(file_path), 'wb') as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(frames.tobytes())
    
    async def retrieve_segment(self, uri: str) -> Optional[Tuple[np.ndarray, int]]:
        """Retrieve audio segment from storage. Returns (audio_data, sample_rate)."""
        if uri.startswith('redalert://media/audio/'):
            # Extract relative path from URI
            relative_path = uri.replace('redalert://media/audio/', '')
            file_path = self.base_path / relative_path
            
            if not file_path.exists():
                logger.error(f"Audio file not found: {file_path}")
                return None
            
            # Read WAV file
            with wave.open(str(file_path), 'rb') as wav_file:
                channels = wav_file.getnchannels()
                sample_width = wav_file.getsampwidth()
                sample_rate = wav_file.getframerate()
                frames = wav_file.readframes(wav_file.getnframes())
            
            # Convert bytes to numpy array
            if sample_width == 2:
                audio_data = np.frombuffer(frames, dtype=np.int16)
            else:
                raise ValueError(f"Unsupported sample width: {sample_width}")
            
            # Reshape for multiple channels
            if channels > 1:
                audio_data = audio_data.reshape(-1, channels)
            
            return audio_data, sample_rate
        
        elif uri.startswith('s3://'):
            # S3 retrieval would go here
            raise NotImplementedError("S3 storage not yet implemented")
        
        else:
            logger.error(f"Unknown URI scheme: {uri}")
            return None
    
    async def delete_segment(self, uri: str) -> bool:
        """Delete a segment from storage."""
        if uri.startswith('redalert://media/audio/'):
            relative_path = uri.replace('redalert://media/audio/', '')
            file_path = self.base_path / relative_path
            
            try:
                if file_path.exists():
                    file_path.unlink()
                    logger.info(f"Deleted audio segment: {uri}")
                    return True
            except Exception as e:
                logger.error(f"Failed to delete segment {uri}: {e}")
                return False
        
        return False
    
    async def cleanup_old_segments(self, days: int = 30) -> int:
        """Clean up segments older than specified days."""
        if self.use_s3:
            # S3 lifecycle policies would handle this
            return 0
        
        count = 0
        cutoff_time = datetime.utcnow().timestamp() - (days * 86400)
        
        for build_dir in self.base_path.iterdir():
            if not build_dir.is_dir():
                continue
            
            for date_dir in build_dir.iterdir():
                if not date_dir.is_dir():
                    continue
                
                for audio_file in date_dir.glob("*.wav"):
                    if audio_file.stat().st_mtime < cutoff_time:
                        try:
                            audio_file.unlink()
                            count += 1
                        except Exception as e:
                            logger.error(f"Failed to delete old file {audio_file}: {e}")
        
        logger.info(f"Cleaned up {count} old audio segments")
        return count


class MediaCache:
    """Simple LRU cache for recently accessed audio segments."""
    
    def __init__(self, max_size_mb: int = 100):
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.cache = {}
        self.access_times = {}
        self.sizes = {}
        self.total_size = 0
    
    def get(self, uri: str) -> Optional[Tuple[np.ndarray, int]]:
        """Get segment from cache."""
        if uri in self.cache:
            self.access_times[uri] = datetime.utcnow()
            return self.cache[uri]
        return None
    
    def put(self, uri: str, audio_data: np.ndarray, sample_rate: int):
        """Add segment to cache."""
        size = audio_data.nbytes
        
        # Evict old entries if needed
        while self.total_size + size > self.max_size_bytes and self.cache:
            # Find oldest entry
            oldest_uri = min(self.access_times.keys(), 
                           key=lambda k: self.access_times[k])
            self._evict(oldest_uri)
        
        # Add to cache
        self.cache[uri] = (audio_data, sample_rate)
        self.access_times[uri] = datetime.utcnow()
        self.sizes[uri] = size
        self.total_size += size
    
    def _evict(self, uri: str):
        """Evict entry from cache."""
        if uri in self.cache:
            del self.cache[uri]
            del self.access_times[uri]
            self.total_size -= self.sizes[uri]
            del self.sizes[uri]
    
    def clear(self):
        """Clear entire cache."""
        self.cache.clear()
        self.access_times.clear()
        self.sizes.clear()
        self.total_size = 0

