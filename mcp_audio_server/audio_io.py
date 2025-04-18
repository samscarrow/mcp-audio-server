"""Audio input/output utilities with robust FFmpeg decoding."""

import base64
import io
import json
import logging
import os
import shutil
import signal
import subprocess
import tempfile
import time
from contextlib import contextmanager
from typing import Dict, Optional, Tuple, Union

import numpy as np

from mcp_audio_server.security import SecureTempFile, validate_file_type, apply_resource_limits

logger = logging.getLogger(__name__)

# Configuration constants
MAX_AUDIO_SIZE_MB = 100  # Maximum audio file size in MB
MAX_AUDIO_DURATION_SEC = 300  # Maximum audio duration in seconds (5 minutes)
FFMPEG_TIMEOUT_SEC = 30  # Maximum time allowed for FFmpeg processing
TARGET_SAMPLE_RATE = 44100  # Standardized sample rate
TARGET_CHANNELS = 1  # Mono audio

# Error codes
class AudioDecodeError:
    DECODE_FAILED = "DECODING_ERROR"
    TIMEOUT = "TIMEOUT_ERROR"
    FILE_TOO_LARGE = "FILE_TOO_LARGE"
    DURATION_TOO_LONG = "DURATION_TOO_LONG"
    UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"
    FFMPEG_NOT_FOUND = "FFMPEG_NOT_FOUND"
    INVALID_FILE_TYPE = "INVALID_FILE_TYPE"


class AudioDecodingException(Exception):
    """Exception raised for audio decoding errors."""
    
    def __init__(self, message: str, error_code: str, details: Optional[Dict] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


def check_ffmpeg_available() -> Tuple[bool, str]:
    """Check if FFmpeg is available and return version."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            check=True
        )
        version_line = result.stdout.split('\n')[0]
        return True, version_line
    except (subprocess.SubprocessError, FileNotFoundError):
        return False, ""


@contextmanager
def time_limit(seconds: int):
    """Context manager to limit execution time of a block."""
    def signal_handler(signum, frame):
        raise AudioDecodingException(
            "FFmpeg processing timed out", 
            AudioDecodeError.TIMEOUT
        )
        
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)


def get_audio_info(file_path: str) -> Dict[str, Union[float, int, str]]:
    """Get audio file information using FFprobe."""
    # First, validate the file type
    is_valid, mime_type = validate_file_type(file_path)
    if not is_valid:
        raise AudioDecodingException(
            f"Invalid file type: {mime_type}",
            AudioDecodeError.INVALID_FILE_TYPE,
            {"detected_mime": mime_type}
        )
    
    cmd = [
        "ffprobe", 
        "-v", "error",
        "-show_entries", "format=duration,size:stream=codec_name,sample_rate,channels",
        "-of", "json",
        file_path
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        info = json.loads(result.stdout)
        
        # Extract relevant information
        duration = float(info.get("format", {}).get("duration", 0))
        size_bytes = int(info.get("format", {}).get("size", 0))
        codec = info.get("streams", [{}])[0].get("codec_name", "unknown")
        
        return {
            "duration": duration,
            "size_bytes": size_bytes,
            "size_mb": size_bytes / (1024 * 1024),
            "codec": codec
        }
    except (subprocess.SubprocessError, json.JSONDecodeError) as e:
        logger.error(f"Error getting audio info: {e}")
        raise AudioDecodingException(
            f"Failed to analyze audio file: {e}",
            AudioDecodeError.DECODE_FAILED,
            {"error": str(e)}
        )


def normalize_audio(input_path: str, output_path: str = None) -> Tuple[np.ndarray, int]:
    """Normalize audio to standard format using FFmpeg and load as numpy array."""
    # If no output path provided, use a secure temporary file
    temp_file = None
    if not output_path:
        with SecureTempFile(suffix=".wav") as secure_temp:
            temp_file = secure_temp.name
            output_path = temp_file
    
    try:
        with time_limit(FFMPEG_TIMEOUT_SEC):
            # Get audio info to validate size and duration
            info = get_audio_info(input_path)
            
            # Validate size
            if info["size_mb"] > MAX_AUDIO_SIZE_MB:
                raise AudioDecodingException(
                    f"Audio file too large ({info['size_mb']:.2f} MB). Maximum allowed: {MAX_AUDIO_SIZE_MB} MB",
                    AudioDecodeError.FILE_TOO_LARGE,
                    {"size_mb": info["size_mb"], "max_size_mb": MAX_AUDIO_SIZE_MB}
                )
            
            # Validate duration
            if info["duration"] > MAX_AUDIO_DURATION_SEC:
                raise AudioDecodingException(
                    f"Audio duration too long ({info['duration']:.2f} seconds). Maximum allowed: {MAX_AUDIO_DURATION_SEC} seconds",
                    AudioDecodeError.DURATION_TOO_LONG,
                    {"duration": info["duration"], "max_duration": MAX_AUDIO_DURATION_SEC}
                )
            
            # Normalize using FFmpeg
            cmd = [
                "ffmpeg",
                "-i", input_path,
                "-ac", str(TARGET_CHANNELS),  # Convert to mono
                "-ar", str(TARGET_SAMPLE_RATE),  # Sample rate
                "-sample_fmt", "s16",  # 16-bit depth
                "-y",  # Overwrite output file if it exists
                output_path
            ]
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            _, stderr = process.communicate()
            
            if process.returncode != 0:
                stderr_str = stderr.decode("utf-8", errors="replace")
                logger.error(f"FFmpeg error: {stderr_str}")
                raise AudioDecodingException(
                    "Failed to decode audio", 
                    AudioDecodeError.DECODE_FAILED,
                    {"ffmpeg_error": stderr_str}
                )
            
            # Load normalized audio data
            import soundfile as sf
            audio_data, sample_rate = sf.read(output_path)
            
            return audio_data, sample_rate
    
    except AudioDecodingException:
        raise  # Re-raise without modification
    except Exception as e:
        logger.error(f"Error normalizing audio: {e}")
        raise AudioDecodingException(
            f"Failed to normalize audio: {e}",
            AudioDecodeError.DECODE_FAILED,
            {"error": str(e)}
        )
    finally:
        # Clean up temporary file if created
        if temp_file and os.path.exists(output_path):
            try:
                os.unlink(output_path)
            except Exception as e:
                logger.warning(f"Failed to clean up temporary file: {e}")


def decode_audio(audio_data: str, format_type: str) -> Tuple[np.ndarray, int]:
    """Decode base64-encoded audio data into numpy array using FFmpeg.
    
    Args:
        audio_data: Base64-encoded audio data
        format_type: Format of the audio data ('wav', 'mp3', etc.)
        
    Returns:
        Tuple of (audio_samples, sample_rate)
        
    Raises:
        AudioDecodingException: For any decoding errors with structured info
    """
    # Apply resource limits
    apply_resource_limits()
    
    # Check if FFmpeg is available
    is_ffmpeg_available, version = check_ffmpeg_available()
    if not is_ffmpeg_available:
        raise AudioDecodingException(
            "FFmpeg not found. Please install FFmpeg to decode audio files.",
            AudioDecodeError.FFMPEG_NOT_FOUND
        )
    
    logger.info(f"Using FFmpeg: {version}")
    
    # Create secure temporary files for input and output
    with SecureTempFile(suffix=f".{format_type}") as input_file:
        try:
            # Decode base64 data
            try:
                binary_data = base64.b64decode(audio_data)
            except Exception as e:
                logger.error(f"Error decoding base64 data: {e}")
                raise AudioDecodingException(
                    f"Invalid base64 data: {e}",
                    AudioDecodeError.DECODE_FAILED,
                    {"error": str(e)}
                )
            
            # Write to temporary file
            input_file.write(binary_data)
            input_file.flush()
            
            # Normalize and load audio data
            return normalize_audio(input_file.name)
            
        finally:
            # Cleanup is handled by the context manager
            pass
