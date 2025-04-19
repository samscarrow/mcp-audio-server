# Environment Configuration

The MCP Audio Server can be configured through environment variables, allowing you to customize various aspects of its behavior without modifying the code.

## Core Settings

| Environment Variable | Description | Default | Example |
|----------------------|-------------|---------|---------|
| `MCP_HOST` | Hostname the server binds to | `0.0.0.0` | `localhost` |
| `MCP_PORT` | Port the server listens on | `8000` | `9000` |
| `MCP_WORKERS` | Number of worker processes | `1` | `4` |
| `MCP_DEBUG` | Enable debug mode | `false` | `true` |
| `MCP_LOG_LEVEL` | Logging level | `INFO` | `DEBUG` |
| `MCP_ENVIRONMENT` | Deployment environment | `production` | `development` |

## Resource Limits

| Environment Variable | Description | Default | Example |
|----------------------|-------------|---------|---------|
| `MCP_MAX_UPLOAD_SIZE_MB` | Maximum allowed upload size in MB | `10` | `25` |
| `MCP_MAX_CONCURRENCY` | Maximum concurrent analysis requests | `4` | `8` |
| `MCP_REQUEST_TIMEOUT_SEC` | Request timeout in seconds | `30` | `60` |
| `MCP_MAX_AUDIO_DURATION_SEC` | Maximum audio duration in seconds | `600` | `1200` |

## Cache Settings

| Environment Variable | Description | Default | Example |
|----------------------|-------------|---------|---------|
| `MCP_CACHE_ENABLED` | Enable result caching | `true` | `false` |
| `MCP_CACHE_TTL_SEC` | Cache time-to-live in seconds | `86400` | `3600` |
| `MCP_REDIS_URL` | Redis server URL for distributed caching | `None` | `redis://localhost:6379/0` |
| `MCP_FILESYSTEM_CACHE_DIR` | Directory for filesystem cache | `/tmp/mcp_cache` | `/app/cache` |
| `MCP_CACHE_MAX_SIZE_MB` | Maximum cache size in MB | `1024` | `2048` |

## Analysis Settings

| Environment Variable | Description | Default | Example |
|----------------------|-------------|---------|---------|
| `MCP_DEFAULT_MODEL` | Default analysis model | `basic` | `advanced` |
| `MCP_SAMPLE_RATE` | Default sample rate for analysis | `44100` | `48000` |
| `MCP_NORMALIZE_AUDIO` | Normalize audio before analysis | `true` | `false` |
| `MCP_ANALYSIS_BUFFER_SIZE` | Size of analysis buffer in samples | `4096` | `8192` |

## Metrics and Monitoring

| Environment Variable | Description | Default | Example |
|----------------------|-------------|---------|---------|
| `MCP_METRICS_ENABLED` | Enable Prometheus metrics | `true` | `false` |
| `MCP_METRICS_PORT` | Port for metrics server | `8001` | `9001` |
| `MCP_METRICS_HOST` | Host for metrics server | `0.0.0.0` | `localhost` |
| `MCP_HEALTH_CHECK_PATH` | Path for health check endpoint | `/health` | `/healthz` |

## External Dependencies

| Environment Variable | Description | Default | Example |
|----------------------|-------------|---------|---------|
| `MCP_FFMPEG_PATH` | Path to FFmpeg executable | `ffmpeg` | `/usr/local/bin/ffmpeg` |
| `MCP_FFPROBE_PATH` | Path to FFprobe executable | `ffprobe` | `/usr/local/bin/ffprobe` |
| `MCP_TEMP_DIR` | Directory for temporary files | `/tmp` | `/app/tmp` |

## Example Configuration

### Development Environment

```bash
# .env.development
MCP_ENVIRONMENT=development
MCP_DEBUG=true
MCP_LOG_LEVEL=DEBUG
MCP_MAX_UPLOAD_SIZE_MB=25
MCP_CACHE_ENABLED=false
```

### Production Environment

```bash
# .env.production
MCP_ENVIRONMENT=production
MCP_WORKERS=4
MCP_MAX_CONCURRENCY=12
MCP_CACHE_ENABLED=true
MCP_REDIS_URL=redis://redis:6379/0
MCP_MAX_UPLOAD_SIZE_MB=10
MCP_REQUEST_TIMEOUT_SEC=30
```

## Using with Docker Compose

You can set environment variables in `docker-compose.yml`:

```yaml
services:
  app:
    image: mcp-audio-server:latest
    environment:
      - MCP_ENVIRONMENT=production
      - MCP_WORKERS=2
      - MCP_REDIS_URL=redis://redis:6379/0
```

## Loading from .env Files

The server can load configuration from `.env` files:

```bash
# Development
cp .env.example .env.development
# Edit as needed

# Start with development config
MCP_ENV_FILE=.env.development uvicorn mcp_audio_server.main:app
```

## Configuration Precedence

The server uses the following precedence order:

1. Command-line arguments
2. Environment variables
3. `.env` file specified by `MCP_ENV_FILE`
4. Default values
