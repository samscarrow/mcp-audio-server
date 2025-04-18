"""Main MCP server module with defensive error handling."""

import asyncio
import base64
import json
import logging
import os
import shutil
import subprocess
import time
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import structlog
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ValidationError

from mcp_audio_server.analysis import registry
from mcp_audio_server.analysis.chord_detection import BasicChordDetector, AdvancedChordDetector
from mcp_audio_server.analysis.key_detection import BasicKeyDetector, AdvancedKeyDetector
from mcp_audio_server.analysis.models import AudioAnalysisResult, Chord
from mcp_audio_server.analysis.tempo_tracking import BasicTempoDetector, AdvancedTempoDetector
from mcp_audio_server.audio_io import AudioDecodingException, decode_audio
from mcp_audio_server.cache import compute_file_hash, get_from_cache, save_to_cache, clean_cache, PerformanceStats
from mcp_audio_server.concurrency import with_concurrency_control, ServerBusy
from mcp_audio_server.metrics import instrument, setup_metrics_server, start_memory_tracking
from mcp_audio_server.utils.validation import validate_payload

# Constants
APP_START_TIME = time.time()
SCHEMA_VERSION = "1.0.0"

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
)

logger = structlog.get_logger("mcp_audio_server")

# Initialize FastAPI app
app = FastAPI(
    title="MCP Audio Server",
    description="MCP server for audio processing and chord analysis",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Models
class ErrorResponse(BaseModel):
    """Standardized error response model."""
    
    error_code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    correlation_id: str = Field(..., description="Request correlation ID for tracking")


class ProcessingInfo(BaseModel):
    """Information about the processing of the audio."""
    
    sample_rate: int = Field(..., description="Sample rate used for analysis")
    channels: int = Field(1, description="Number of audio channels used")
    processing_time: float = Field(..., description="Time taken to analyze the audio in seconds")
    model_used: str = Field(..., description="Chord detection model used for analysis")


class ChordEntry(BaseModel):
    """A single chord detection entry."""
    
    time: float = Field(..., description="Time position in seconds")
    label: str = Field(..., description="Chord label (e.g., 'C', 'G7', 'Dm')")
    confidence: Optional[float] = Field(None, description="Confidence score (0-1)")


class ChordAnalysisRequest(BaseModel):
    """Request model for chord analysis."""
    
    audio_data: str = Field(..., description="Base64-encoded audio data")
    format: str = Field(..., description="Format of the audio data")
    options: Dict[str, Any] = Field(default_factory=dict, description="Analysis options")


class ChordAnalysisResponse(BaseModel):
    """Response model for chord analysis."""
    
    schema_version: str = Field(SCHEMA_VERSION, description="Version of the response schema")
    key: Optional[str] = Field(None, description="Musical key of the audio")
    tempo: Optional[float] = Field(None, description="Tempo in beats per minute")
    chords: List[ChordEntry] = Field(..., description="Detected chords with timestamps")
    duration: float = Field(..., description="Duration of the audio in seconds")
    processing_info: Optional[ProcessingInfo] = Field(None, description="Processing information")
    correlation_id: str = Field(..., description="Request correlation ID for tracking")


# Initialize plugin registry
registry.register("basic_chords", BasicChordDetector())
registry.register("advanced_chords", AdvancedChordDetector())
registry.register("basic_tempo", BasicTempoDetector())
registry.register("advanced_tempo", AdvancedTempoDetector())
registry.register("basic_key", BasicKeyDetector())
registry.register("advanced_key", AdvancedKeyDetector())


# Middleware for correlation IDs and timing
@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    # Generate correlation ID
    correlation_id = str(uuid.uuid4())
    request.state.correlation_id = correlation_id
    
    # Timing
    start_time = time.time()
    
    # Set up structured logging context
    log_context = structlog.contextvars.bind_contextvars(
        correlation_id=correlation_id,
        path=request.url.path,
        method=request.method,
    )
    
    # Call the next middleware or endpoint
    try:
        response = await call_next(request)
        
        # Add correlation ID to response headers
        response.headers["X-Correlation-ID"] = correlation_id
        
        # Log request completion
        duration = time.time() - start_time
        logger.info(
            "request_processed",
            duration_ms=round(duration * 1000, 2),
            status_code=response.status_code,
        )
        
        return response
    except Exception as e:
        # Log exception
        logger.exception(
            "unhandled_exception",
            error=str(e),
            error_type=type(e).__name__,
        )
        
        # Return error response
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error_code="INTERNAL_ERROR",
                message="An unexpected error occurred",
                correlation_id=correlation_id,
            ).dict(),
        )


# Exception handlers
@app.exception_handler(AudioDecodingException)
async def audio_decoding_exception_handler(request: Request, exc: AudioDecodingException):
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details,
            correlation_id=request.state.correlation_id,
        ).dict(),
    )


@app.exception_handler(ValidationError)
async def validation_exception_handler(request: Request, exc: ValidationError):
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(
            error_code="VALIDATION_ERROR",
            message="Request validation failed",
            details={"errors": exc.errors()},
            correlation_id=request.state.correlation_id,
        ).dict(),
    )


@app.exception_handler(ServerBusy)
async def server_busy_exception_handler(request: Request, exc: ServerBusy):
    return JSONResponse(
        status_code=503,  # Service Unavailable
        headers={"Retry-After": str(exc.retry_after)},
        content=ErrorResponse(
            error_code="SERVER_BUSY",
            message=f"Server is currently busy. Please retry after {exc.retry_after} seconds.",
            details={"retry_after": exc.retry_after},
            correlation_id=request.state.correlation_id,
        ).dict(),
    )


@app.exception_handler(asyncio.TimeoutError)
async def timeout_exception_handler(request: Request, exc: asyncio.TimeoutError):
    return JSONResponse(
        status_code=408,  # Request Timeout
        content=ErrorResponse(
            error_code="TIMEOUT",
            message="The request processing has timed out",
            correlation_id=request.state.correlation_id,
        ).dict(),
    )


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    # Start metrics server
    setup_metrics_server(port=8001)
    
    # Start memory tracking
    asyncio.create_task(start_memory_tracking())
    
    # Start periodic cache cleaning
    asyncio.create_task(periodic_cache_cleaning())
    
    # Check FFmpeg availability
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            text=True,
            check=True
        )
        ffmpeg_version = result.stdout.split('\n')[0]
        logger.info(f"FFmpeg available: {ffmpeg_version}")
    except Exception as e:
        logger.error(f"FFmpeg not available: {e}")


async def periodic_cache_cleaning():
    """Periodically clean the cache to remove expired entries."""
    while True:
        try:
            await clean_cache()
            logger.debug("Completed periodic cache cleaning")
        except Exception as e:
            logger.error("Error during cache cleaning", error=str(e))
        
        # Wait for next cleaning cycle (every hour)
        await asyncio.sleep(60 * 60)


# Health check endpoints
@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    uptime_seconds = time.time() - APP_START_TIME
    
    return {
        "status": "ok",
        "uptime": uptime_seconds,
        "timestamp": datetime.utcnow().isoformat(),
        "version": app.version,
    }


@app.get("/ready")
async def readiness_check():
    """Readiness check that verifies external dependencies."""
    checks = {
        "ffmpeg": False,
        "models": False,
    }
    
    # Check FFmpeg
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        checks["ffmpeg"] = True
    
    # Check if models/detectors are available
    if len(registry.list_detectors()) > 0:
        checks["models"] = True
    
    # Determine overall status
    status = "ok" if all(checks.values()) else "degraded"
    
    response = {
        "status": status,
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    # Set appropriate status code
    if status != "ok":
        return JSONResponse(status_code=503, content=response)
    
    return response


# MCP tool endpoint
@app.post("/analyze_chords", response_model=ChordAnalysisResponse)
@instrument(tool_name="analyze_chords")
async def analyze_chords(request: ChordAnalysisRequest, req: Request) -> ChordAnalysisResponse:
    """Analyze chords in the provided audio data."""
    correlation_id = req.state.correlation_id
    perf_stats = PerformanceStats("analyze_chords")
    
    # Log request (without the actual audio data which could be large)
    logger.info(
        "chord_analysis_request",
        format=request.format,
        options=request.options,
    )
    
    # Validate request against schema
    try:
        validate_payload(request.dict(), "chord_analysis.schema.json")
        perf_stats.checkpoint("schema_validation")
    except ValueError as e:
        logger.error("schema_validation_error", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))

    # Generate a hash for the audio data to use as cache key
    try:
        binary_data = base64.b64decode(request.audio_data)
        cache_key = compute_file_hash(binary_data)
        perf_stats.checkpoint("hash_computation")
        
        # Check if we have cached results
        cached_result = await get_from_cache(cache_key)
        if cached_result:
            # Add cache hit metrics
            logger.info("cache_hit", cache_key=cache_key)
            perf_stats.checkpoint("cache_hit")
            
            # Convert cached result to response model
            response = ChordAnalysisResponse(
                schema_version=cached_result.get("schema_version", SCHEMA_VERSION),
                key=cached_result.get("key", ""),
                tempo=cached_result.get("tempo", 0),
                chords=[ChordEntry(**chord) for chord in cached_result.get("chords", [])],
                duration=cached_result.get("duration", 0),
                processing_info=cached_result.get("processing_info"),
                correlation_id=correlation_id
            )
            
            # Log response from cache
            logger.info(
                "chord_analysis_from_cache",
                cache_key=cache_key,
                num_chords=len(response.chords),
            )
            
            perf_stats.finish()
            return response
        
        # Log cache miss
        logger.info("cache_miss", cache_key=cache_key)
        perf_stats.checkpoint("cache_check")
        
    except Exception as e:
        # Non-fatal error, continue without caching
        logger.warning("Cache check failed", error=str(e))

    # Decode audio data
    try:
        audio_data, sample_rate = await with_concurrency_control(
            decode_audio, request.audio_data, request.format
        )
        perf_stats.checkpoint("audio_decode")
    except Exception as e:
        # AudioDecodingException will be caught by the exception handler
        # Other exceptions will be re-raised as HTTPException
        if not isinstance(e, (AudioDecodingException, asyncio.TimeoutError, ServerBusy)):
            logger.error("audio_decoding_error", error=str(e), error_type=type(e).__name__)
            raise HTTPException(status_code=400, detail=f"Error decoding audio: {e}")
        raise

    # Determine which detector to use based on options
    model = request.options.get("model", "basic")
    chord_detector_name = "advanced_chords" if model == "advanced" else "basic_chords"
    tempo_detector_name = "advanced_tempo" if model == "advanced" else "basic_tempo"
    key_detector_name = "advanced_key" if model == "advanced" else "basic_key"
    
    try:
        # Get the detector instances
        chord_detector = registry.get(chord_detector_name)
        tempo_detector = registry.get(tempo_detector_name)
        key_detector = registry.get(key_detector_name)
        
        # Perform analyses asynchronously with resource controls
        chord_results = await with_concurrency_control(
            chord_detector.detect_chords, audio_data, sample_rate
        )
        perf_stats.checkpoint("chord_detection")
        
        tempo_results = await with_concurrency_control(
            tempo_detector.detect_tempo, audio_data, sample_rate
        )
        perf_stats.checkpoint("tempo_detection")
        
        key_results = await with_concurrency_control(
            key_detector.detect_key, audio_data, sample_rate
        )
        perf_stats.checkpoint("key_detection")
        
        # Create chord entry objects
        chord_entries = [
            ChordEntry(
                time=chord.time,
                label=chord.label,
                confidence=chord.confidence
            )
            for chord in chord_results
        ]
        
        # Calculate processing time and duration
        processing_time = perf_stats.checkpoint("processing") - perf_stats.checkpoints.get("audio_decode", 0)
        duration = len(audio_data) / sample_rate
        
        # Create processing info
        processing_info = ProcessingInfo(
            sample_rate=sample_rate,
            channels=1,
            processing_time=processing_time,
            model_used=model
        )
        
        # Log response summary
        logger.info(
            "chord_analysis_complete",
            processing_time=processing_time,
            num_chords=len(chord_entries),
            key=key_results.get("key", ""),
            tempo=tempo_results.get("tempo", 0),
        )
        
        # Prepare and validate response
        response = ChordAnalysisResponse(
            schema_version=SCHEMA_VERSION,
            key=key_results.get("key", ""),
            tempo=tempo_results.get("tempo", 0),
            chords=chord_entries,
            duration=duration,
            processing_info=processing_info,
            correlation_id=correlation_id
        )
        
        # Validate response against schema
        try:
            validate_payload(response.dict(), "audio_analysis_response.schema.json")
            perf_stats.checkpoint("response_validation")
        except ValueError as e:
            logger.error("response_validation_error", error=str(e))
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to generate valid response: {e}"
            )
        
        # Cache the results
        if 'cache_key' in locals():
            try:
                # Cache the response as a dictionary
                cache_data = response.dict()
                await save_to_cache(cache_key, cache_data)
                logger.debug("Saved results to cache", cache_key=cache_key)
            except Exception as e:
                # Non-fatal error, continue without caching
                logger.warning("Failed to cache results", error=str(e), cache_key=cache_key)
        
        perf_stats.finish()
        return response
        
    except KeyError as e:
        # Handle missing detector
        logger.error("detector_not_found", error=str(e))
        raise HTTPException(status_code=400, detail=f"Detector not found: {e}")


@app.get("/metrics")
async def metrics_dashboard():
    """Redirect to the metrics dashboard."""
    return JSONResponse(
        status_code=307,  # Temporary redirect
        headers={"Location": "http://localhost:8001"},
        content={"message": "Redirecting to metrics dashboard"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

