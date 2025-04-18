# Multi-stage build for MCP Audio Server

# Builder stage
FROM python:3.11-slim AS builder

# Install system dependencies for builder
RUN apt-get update && apt-get install -y \
    build-essential \
    libsndfile1-dev \
    ffmpeg \
    pkg-config \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry==1.7.1

# Copy configuration files
WORKDIR /app
COPY pyproject.toml poetry.lock* ./

# Export dependencies to requirements.txt
RUN poetry export -f requirements.txt --without-hashes --without-urls > requirements.txt

# Runtime stage
FROM python:3.11-slim AS runtime

# Create non-root user
RUN groupadd -r mcpuser && useradd -r -g mcpuser mcpuser

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libsndfile1 \
    ffmpeg \
    python3-magic \
    && rm -rf /var/lib/apt/lists/*

# Create working directories
RUN mkdir -p /var/lib/mcp/work /var/lib/mcp/tmp /var/lib/mcp/cache \
    && chown -R mcpuser:mcpuser /var/lib/mcp \
    && chmod 700 /var/lib/mcp/tmp

# Set working directory
WORKDIR /app

# Copy requirements.txt and install dependencies
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY mcp_audio_server/ /app/mcp_audio_server/
COPY schemas/ /app/schemas/

# Set environment variables
ENV MCP_TEMP_DIR=/var/lib/mcp/tmp \
    MCP_WORK_DIR=/var/lib/mcp/work \
    MCP_CACHE_DIR=/var/lib/mcp/cache \
    MCP_MAX_WORKERS=4 \
    MCP_MAX_MEMORY_MB=1024 \
    MCP_REQUEST_TIMEOUT=30 \
    MCP_MAX_CONCURRENT=10 \
    MCP_MAX_QUEUE_SIZE=100 \
    PYTHONUNBUFFERED=1

# Expose ports for the API and metrics
EXPOSE 8000 8001

# Switch to non-root user
USER mcpuser

# Set entrypoint
ENTRYPOINT ["python", "-m", "uvicorn", "mcp_audio_server.main:app", "--host", "0.0.0.0", "--port", "8000"]

# GPU variant - uncomment and build with --target=gpu
FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04 AS gpu

# Install Python and dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    libsndfile1 \
    ffmpeg \
    python3-magic \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r mcpuser && useradd -r -g mcpuser mcpuser

# Create working directories
RUN mkdir -p /var/lib/mcp/work /var/lib/mcp/tmp /var/lib/mcp/cache \
    && chown -R mcpuser:mcpuser /var/lib/mcp \
    && chmod 700 /var/lib/mcp/tmp

# Set working directory
WORKDIR /app

# Copy requirements from builder and install with GPU support
COPY --from=builder /app/requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt \
    && pip3 install --no-cache-dir torch torchvision torchaudio

# Copy application code
COPY mcp_audio_server/ /app/mcp_audio_server/
COPY schemas/ /app/schemas/

# Set environment variables
ENV MCP_TEMP_DIR=/var/lib/mcp/tmp \
    MCP_WORK_DIR=/var/lib/mcp/work \
    MCP_CACHE_DIR=/var/lib/mcp/cache \
    MCP_MAX_WORKERS=4 \
    MCP_MAX_MEMORY_MB=1024 \
    MCP_REQUEST_TIMEOUT=30 \
    MCP_MAX_CONCURRENT=10 \
    MCP_MAX_QUEUE_SIZE=100 \
    PYTHONUNBUFFERED=1 \
    CUDA_VISIBLE_DEVICES=0

# Expose ports for the API and metrics
EXPOSE 8000 8001

# Switch to non-root user
USER mcpuser

# Set entrypoint
ENTRYPOINT ["python3", "-m", "uvicorn", "mcp_audio_server.main:app", "--host", "0.0.0.0", "--port", "8000"]
