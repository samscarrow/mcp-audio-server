"""Metrics and observability utilities."""

import os
import time
from typing import Callable, Optional, TypeVar

import structlog
from prometheus_client import (Counter, Gauge, Histogram, start_http_server,
                               Summary)

logger = structlog.get_logger(__name__)

# Initialize Prometheus metrics
JOBS_TOTAL = Counter(
    "audio_jobs_total", 
    "Total audio analysis jobs processed",
    ["tool", "status"]
)

JOB_DURATION = Histogram(
    "audio_job_duration_seconds", 
    "Duration of audio analysis jobs in seconds",
    ["tool"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0]
)

QUEUE_SIZE = Gauge(
    "audio_queue_size", 
    "Current size of the request queue"
)

ACTIVE_REQUESTS = Gauge(
    "audio_active_requests", 
    "Number of currently active requests"
)

MEMORY_USAGE = Gauge(
    "audio_memory_usage_bytes", 
    "Current memory usage in bytes"
)

REQUEST_ERRORS = Counter(
    "audio_request_errors_total", 
    "Total number of request errors",
    ["error_type"]
)

# Type for functions to be instrumented
F = TypeVar('F', bound=Callable)


def instrument(tool_name: str) -> Callable[[F], F]:
    """
    Decorator to instrument functions with metrics.
    
    Args:
        tool_name: Name of the tool being instrumented
        
    Returns:
        Decorated function
    """
    def decorator(func: F) -> F:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                # Update active requests gauge
                ACTIVE_REQUESTS.inc()
                
                # Execute the function
                result = await func(*args, **kwargs)
                
                # Record successful job
                JOBS_TOTAL.labels(tool=tool_name, status="success").inc()
                
                return result
            except Exception as e:
                # Record error
                JOBS_TOTAL.labels(tool=tool_name, status="error").inc()
                REQUEST_ERRORS.labels(error_type=type(e).__name__).inc()
                raise
            finally:
                # Record duration
                duration = time.time() - start_time
                JOB_DURATION.labels(tool=tool_name).observe(duration)
                
                # Update active requests gauge
                ACTIVE_REQUESTS.dec()
                
                # Update memory usage
                try:
                    import psutil
                    process = psutil.Process(os.getpid())
                    memory_info = process.memory_info()
                    MEMORY_USAGE.set(memory_info.rss)
                except ImportError:
                    pass
        
        return wrapper
    
    return decorator


def update_queue_size(size: int) -> None:
    """Update the queue size metric."""
    QUEUE_SIZE.set(size)


def setup_metrics_server(port: int = 8001) -> None:
    """Start the Prometheus metrics server."""
    try:
        start_http_server(port)
        logger.info(f"Metrics server started on port {port}")
    except Exception as e:
        logger.error(f"Failed to start metrics server: {e}")


def record_memory_usage() -> None:
    """Record current memory usage."""
    try:
        import psutil
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        MEMORY_USAGE.set(memory_info.rss)
    except ImportError:
        logger.warning("psutil not installed, memory usage not tracked")


# Periodic memory usage tracking
async def start_memory_tracking(interval: int = 60) -> None:
    """
    Start periodic memory usage tracking.
    
    Args:
        interval: Tracking interval in seconds
    """
    import asyncio
    
    while True:
        record_memory_usage()
        await asyncio.sleep(interval)
