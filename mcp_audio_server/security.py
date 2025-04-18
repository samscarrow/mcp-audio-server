"""Security and file-handling utilities."""

import os
import re
import magic
import resource
import tempfile
from pathlib import Path
from typing import Optional, Set, Tuple

import structlog

logger = structlog.get_logger(__name__)

# Constants
ALLOWED_AUDIO_MIME_TYPES = {
    'audio/wav', 'audio/x-wav',
    'audio/mpeg', 'audio/mp3',
    'audio/ogg', 'audio/vorbis',
    'audio/flac',
    'audio/aac',
}

# Memory limit in bytes (1GB)
MEMORY_LIMIT_BYTES = 1024 * 1024 * 1024

# CPU time limit in seconds
CPU_TIME_LIMIT = 60

# File descriptor limit
FD_LIMIT = 1024

# Temporary directory
TEMP_DIR = os.environ.get('MCP_TEMP_DIR', '/tmp/mcp-audio-server')


def apply_resource_limits() -> None:
    """Apply OS-level resource limits to the current process."""
    try:
        # Set memory limit
        resource.setrlimit(resource.RLIMIT_AS, (MEMORY_LIMIT_BYTES, MEMORY_LIMIT_BYTES))
        
        # Set CPU time limit
        resource.setrlimit(resource.RLIMIT_CPU, (CPU_TIME_LIMIT, CPU_TIME_LIMIT))
        
        # Set file descriptor limit
        resource.setrlimit(resource.RLIMIT_NOFILE, (FD_LIMIT, FD_LIMIT))
        
        logger.info("Resource limits applied", 
                   memory_limit_mb=MEMORY_LIMIT_BYTES / (1024 * 1024),
                   cpu_time_limit=CPU_TIME_LIMIT,
                   fd_limit=FD_LIMIT)
    except (ValueError, resource.error) as e:
        logger.warning("Failed to set resource limits", error=str(e))


def validate_filename(filename: str) -> bool:
    """
    Validate a filename for security.
    
    Args:
        filename: The filename to validate
        
    Returns:
        True if the filename is safe, False otherwise
    """
    # Check for path traversal
    if '..' in filename or filename.startswith('/'):
        logger.warning("Path traversal attempt detected", filename=filename)
        return False
    
    # Check for unusual characters
    allowed_pattern = re.compile(r'^[a-zA-Z0-9_\-\.]+$')
    if not allowed_pattern.match(filename):
        logger.warning("Filename contains unusual characters", filename=filename)
        return False
    
    return True


def validate_file_type(file_path: str, allowed_mime_types: Optional[Set[str]] = None) -> Tuple[bool, str]:
    """
    Validate a file's MIME type.
    
    Args:
        file_path: Path to the file
        allowed_mime_types: Set of allowed MIME types (defaults to ALLOWED_AUDIO_MIME_TYPES)
        
    Returns:
        Tuple of (is_valid, mime_type)
    """
    if allowed_mime_types is None:
        allowed_mime_types = ALLOWED_AUDIO_MIME_TYPES
    
    try:
        mime = magic.Magic(mime=True)
        detected_mime = mime.from_file(file_path)
        
        is_valid = detected_mime in allowed_mime_types
        
        if not is_valid:
            logger.warning("File type validation failed", 
                         file_path=file_path, 
                         detected_mime=detected_mime,
                         allowed_types=allowed_mime_types)
        
        return is_valid, detected_mime
    except Exception as e:
        logger.error("Error validating file type", error=str(e), file_path=file_path)
        return False, "unknown"


def get_secure_temp_dir() -> str:
    """
    Get or create a secure temporary directory.
    
    Returns:
        Path to the temporary directory
    """
    temp_dir = Path(TEMP_DIR)
    
    try:
        # Create the directory if it doesn't exist
        if not temp_dir.exists():
            temp_dir.mkdir(parents=True, mode=0o700)  # Restricted permissions
            logger.info("Created secure temporary directory", path=str(temp_dir))
        
        return str(temp_dir)
    except Exception as e:
        logger.warning("Failed to create secure temp directory, falling back to system default", 
                      error=str(e))
        return tempfile.gettempdir()


class SecureTempFile:
    """Context manager for secure temporary file handling."""
    
    def __init__(self, suffix: Optional[str] = None, prefix: Optional[str] = "mcp_"):
        self.temp_dir = get_secure_temp_dir()
        self.suffix = suffix
        self.prefix = prefix
        self.file = None
        self.path = None
    
    def __enter__(self):
        """Create a temporary file with restricted permissions."""
        try:
            self.file = tempfile.NamedTemporaryFile(
                dir=self.temp_dir,
                suffix=self.suffix,
                prefix=self.prefix,
                delete=False,
                mode='wb'
            )
            self.path = self.file.name
            
            # Set permissions to owner-only
            os.chmod(self.path, 0o600)
            
            return self.file
        except Exception as e:
            logger.error("Error creating secure temporary file", error=str(e))
            raise
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up the temporary file."""
        if self.file:
            self.file.close()
        
        if self.path and os.path.exists(self.path):
            try:
                os.unlink(self.path)
                logger.debug("Removed temporary file", path=self.path)
            except Exception as e:
                logger.warning("Failed to remove temporary file", 
                             path=self.path, error=str(e))
