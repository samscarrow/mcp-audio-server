"""Caching utilities for audio analysis results."""

import asyncio
import hashlib
import json
import os
import time
from pathlib import Path
from typing import Any, Dict, Optional, Union

import structlog

logger = structlog.get_logger(__name__)

# Default cache settings
CACHE_DIR = os.environ.get("MCP_CACHE_DIR", "/var/lib/mcp/cache")
DEFAULT_CACHE_TTL = int(os.environ.get("MCP_CACHE_TTL", 24 * 60 * 60))  # 24 hours in seconds
MAX_CACHE_SIZE = int(os.environ.get("MCP_CACHE_SIZE_MB", 1024)) * 1024 * 1024  # MB to bytes

# Lock for cache operations
_cache_lock = asyncio.Lock()

# Optional Redis support
try:
    import redis
    REDIS_URL = os.environ.get("MCP_REDIS_URL")
    if REDIS_URL:
        redis_client = redis.from_url(REDIS_URL)
        REDIS_AVAILABLE = True
    else:
        REDIS_AVAILABLE = False
except ImportError:
    REDIS_AVAILABLE = False


def compute_file_hash(file_bytes: bytes) -> str:
    """
    Compute a unique hash for a file.
    
    Args:
        file_bytes: Raw file bytes
        
    Returns:
        SHA-256 hash hex digest
    """
    return hashlib.sha256(file_bytes).hexdigest()


def get_cache_path(cache_key: str) -> Path:
    """
    Get the filesystem path for a cache key.
    
    Args:
        cache_key: Cache key (hash)
        
    Returns:
        Path object for the cached file
    """
    # Use a two-level directory structure to avoid too many files in one directory
    prefix = cache_key[:2]
    cache_dir = Path(CACHE_DIR) / prefix
    
    # Create directory if it doesn't exist
    if not cache_dir.exists():
        try:
            cache_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error("Failed to create cache directory", error=str(e), path=str(cache_dir))
            # Fall back to the root cache directory
            cache_dir = Path(CACHE_DIR)
    
    return cache_dir / f"{cache_key}.json"


async def get_from_cache(cache_key: str) -> Optional[Dict[str, Any]]:
    """
    Get analysis results from cache.
    
    Args:
        cache_key: Cache key (hash)
        
    Returns:
        Cached result or None if not found or expired
    """
    # Try Redis first if available
    if REDIS_AVAILABLE:
        try:
            cached_data = redis_client.get(f"mcp:analysis:{cache_key}")
            if cached_data:
                return json.loads(cached_data)
        except Exception as e:
            logger.warning("Redis cache retrieval failed", error=str(e))
    
    # Fall back to file system cache
    cache_path = get_cache_path(cache_key)
    
    if not cache_path.exists():
        return None
    
    try:
        async with _cache_lock:
            # Check if the file is expired
            stat = cache_path.stat()
            current_time = time.time()
            
            if current_time - stat.st_mtime > DEFAULT_CACHE_TTL:
                logger.debug("Cache entry expired", key=cache_key)
                # Delete expired entry
                cache_path.unlink()
                return None
            
            # Load the cache entry
            with open(cache_path, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error("Error reading from cache", error=str(e), key=cache_key)
        return None


async def save_to_cache(cache_key: str, data: Dict[str, Any]) -> bool:
    """
    Save analysis results to cache.
    
    Args:
        cache_key: Cache key (hash)
        data: Analysis results to cache
        
    Returns:
        True if successful, False otherwise
    """
    # Try Redis first if available
    if REDIS_AVAILABLE:
        try:
            redis_client.setex(
                f"mcp:analysis:{cache_key}",
                DEFAULT_CACHE_TTL,
                json.dumps(data)
            )
            logger.debug("Saved to Redis cache", key=cache_key)
            # Still save to file cache as backup
        except Exception as e:
            logger.warning("Redis cache save failed", error=str(e))
    
    # Save to file system cache
    cache_path = get_cache_path(cache_key)
    
    try:
        async with _cache_lock:
            with open(cache_path, 'w') as f:
                json.dump(data, f)
            logger.debug("Saved to file cache", key=cache_key, path=str(cache_path))
            return True
    except Exception as e:
        logger.error("Error saving to cache", error=str(e), key=cache_key)
        return False


async def clean_cache() -> None:
    """
    Clean up expired and excess cache entries.
    """
    cache_dir = Path(CACHE_DIR)
    if not cache_dir.exists():
        return
    
    try:
        async with _cache_lock:
            # Get all cache files
            files = []
            for path in cache_dir.glob('**/*.json'):
                if path.is_file():
                    stat = path.stat()
                    files.append((path, stat.st_mtime, stat.st_size))
            
            # Remove expired files
            current_time = time.time()
            for path, mtime, _ in files:
                if current_time - mtime > DEFAULT_CACHE_TTL:
                    try:
                        path.unlink()
                        logger.debug("Removed expired cache entry", path=str(path))
                    except Exception as e:
                        logger.warning("Failed to remove expired cache entry", error=str(e), path=str(path))
            
            # Check cache size and remove oldest files if over limit
            files = [(path, mtime, size) for path, mtime, size in files if path.exists()]
            files.sort(key=lambda x: x[1])  # Sort by modification time
            
            total_size = sum(size for _, _, size in files)
            while total_size > MAX_CACHE_SIZE and files:
                path, _, size = files.pop(0)  # Remove oldest file
                try:
                    path.unlink()
                    total_size -= size
                    logger.debug("Removed oldest cache entry to reduce cache size", path=str(path))
                except Exception as e:
                    logger.warning("Failed to remove cache entry", error=str(e), path=str(path))
    except Exception as e:
        logger.error("Error cleaning cache", error=str(e))


class PerformanceStats:
    """Utility for measuring and reporting performance statistics."""
    
    def __init__(self, operation_name: str):
        self.operation_name = operation_name
        self.start_time = time.perf_counter()
        self.checkpoints = {}
    
    def checkpoint(self, name: str) -> float:
        """Record a checkpoint and return the time since the last checkpoint."""
        now = time.perf_counter()
        elapsed = now - self.start_time
        self.checkpoints[name] = elapsed
        return elapsed
    
    def finish(self) -> Dict[str, float]:
        """Finish timing and return all checkpoint times."""
        self.checkpoint("total")
        
        # Calculate time between checkpoints
        checkpoint_names = sorted(self.checkpoints.keys(), key=lambda k: self.checkpoints[k])
        intervals = {}
        
        for i in range(1, len(checkpoint_names)):
            prev = checkpoint_names[i-1]
            curr = checkpoint_names[i]
            intervals[f"{prev}_to_{curr}"] = self.checkpoints[curr] - self.checkpoints[prev]
        
        result = {
            "operation": self.operation_name,
            "total_time": self.checkpoints["total"],
            "checkpoints": self.checkpoints,
            "intervals": intervals
        }
        
        logger.info(
            "Performance stats",
            operation=self.operation_name,
            total_time=self.checkpoints["total"],
            **{f"time_{k}": v for k, v in self.checkpoints.items() if k != "total"}
        )
        
        return result
