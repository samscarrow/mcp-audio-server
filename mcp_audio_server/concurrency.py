"""Concurrency controls and resource management."""

import asyncio
import logging
import os
import resource
import time
from concurrent.futures import ProcessPoolExecutor
from functools import wraps
from typing import Any, Callable, Dict, Optional

import structlog

logger = structlog.get_logger(__name__)

# Load configuration from environment variables
MAX_WORKERS = int(os.environ.get("MCP_MAX_WORKERS", os.cpu_count() or 4))
MAX_MEMORY_MB = int(os.environ.get("MCP_MAX_MEMORY_MB", 1024))  # 1GB default
REQUEST_TIMEOUT = int(os.environ.get("MCP_REQUEST_TIMEOUT", 30))  # 30 seconds default
MAX_CONCURRENT = int(os.environ.get("MCP_MAX_CONCURRENT", 10))
MAX_QUEUE_SIZE = int(os.environ.get("MCP_MAX_QUEUE_SIZE", 100))


class ResourceLimitExceeded(Exception):
    """Exception raised when a resource limit is exceeded."""
    
    def __init__(self, message: str, resource_type: str):
        self.message = message
        self.resource_type = resource_type
        super().__init__(self.message)


class ServerBusy(Exception):
    """Exception raised when the server is too busy."""
    
    def __init__(self, retry_after: int = 60):
        self.retry_after = retry_after
        super().__init__(f"Server busy, retry after {retry_after} seconds")


# Semaphore for limiting concurrent requests
_request_semaphore = asyncio.Semaphore(MAX_CONCURRENT)
_active_requests = 0
_request_queue = []


def apply_resource_limits():
    """Apply OS-level resource limits to the current process."""
    # Convert MB to bytes
    max_memory_bytes = MAX_MEMORY_MB * 1024 * 1024
    
    try:
        # Set memory limit
        resource.setrlimit(resource.RLIMIT_AS, (max_memory_bytes, max_memory_bytes))
        
        # Optionally, set CPU time limit
        cpu_time_limit = REQUEST_TIMEOUT * 2  # Give some extra headroom
        resource.setrlimit(resource.RLIMIT_CPU, (cpu_time_limit, cpu_time_limit))
        
        logger.info("Resource limits applied", 
                    memory_limit_mb=MAX_MEMORY_MB, 
                    cpu_time_limit=cpu_time_limit)
    except (ValueError, resource.error) as e:
        logger.warning("Failed to set resource limits", error=str(e))


async def run_in_process_pool(func: Callable, *args, **kwargs) -> Any:
    """Run a CPU-intensive function in a process pool with resource limits."""
    loop = asyncio.get_running_loop()
    
    # Initialize the process pool if it doesn't exist
    global _process_pool
    if '_process_pool' not in globals():
        _process_pool = ProcessPoolExecutor(max_workers=MAX_WORKERS, 
                                          initializer=apply_resource_limits)
    
    # Run the function in the process pool
    try:
        return await loop.run_in_executor(_process_pool, 
                                        lambda: func(*args, **kwargs))
    except Exception as e:
        logger.exception("Error in process pool", error=str(e))
        raise


async def with_concurrency_control(func: Callable, *args, **kwargs) -> Any:
    """
    Run a function with concurrency control, timeouts, and resource limits.
    
    Args:
        func: The function to run
        *args, **kwargs: Arguments to pass to the function
        
    Returns:
        The result of the function
        
    Raises:
        asyncio.TimeoutError: If the function execution exceeds the timeout
        ServerBusy: If the server is too busy to process the request
        ResourceLimitExceeded: If a resource limit is exceeded
    """
    global _active_requests, _request_queue
    
    # Check if we're over capacity
    if _active_requests >= MAX_CONCURRENT:
        # Check if the queue is full
        if len(_request_queue) >= MAX_QUEUE_SIZE:
            raise ServerBusy()
        
        # Add to queue and wait
        future = asyncio.Future()
        _request_queue.append(future)
        
        try:
            # Wait for our turn with a timeout
            await asyncio.wait_for(future, timeout=REQUEST_TIMEOUT)
        except asyncio.TimeoutError:
            # Remove from queue if we're still there
            if future in _request_queue:
                _request_queue.remove(future)
            raise ServerBusy(retry_after=30)
    
    # We've acquired the semaphore, increment active requests
    _active_requests += 1
    
    try:
        # Run the function with a timeout
        start_time = time.time()
        result = await asyncio.wait_for(
            run_in_process_pool(func, *args, **kwargs),
            timeout=REQUEST_TIMEOUT
        )
        
        # Log execution time
        execution_time = time.time() - start_time
        logger.info("Function executed successfully", 
                    func=func.__name__, 
                    execution_time=execution_time)
        
        return result
    except asyncio.TimeoutError:
        logger.error("Function execution timed out", 
                    func=func.__name__, 
                    timeout=REQUEST_TIMEOUT)
        raise
    finally:
        # Decrement active requests
        _active_requests -= 1
        
        # Signal the next request in queue if any
        if _request_queue:
            next_future = _request_queue.pop(0)
            next_future.set_result(True)
