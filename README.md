# MCP Audio Server

A Model Context Protocol (MCP) server for audio processing and chord analysis.

## Quick Start

Use Docker Compose for the quickest setup:

```bash
# Clone the repository
git clone https://github.com/yourusername/mcp-audio-server.git
cd mcp-audio-server

# Start the server
docker compose up -d
```

### Sample Request

```bash
# Analyze a WAV file
curl -X POST http://localhost:8000/analyze_chords \
  -H "Content-Type: application/json" \
  -d '{
    "audio_data": "'$(base64 -i tests/fixtures/tempo/120bpm_with_chord.wav)'",
    "format": "wav",
    "options": {"model": "basic"}
  }'
```

Sample response:
```json
{
  "schema_version": "1.0.0",
  "key": "C",
  "tempo": 120.5,
  "chords": [
    {
      "time": 0.0,
      "label": "C",
      "confidence": 0.92
    },
    {
      "time": 1.0,
      "label": "G",
      "confidence": 0.87
    }
  ],
  "duration": 4.0,
  "processing_info": {
    "sample_rate": 44100,
    "channels": 1,
    "processing_time": 0.245,
    "model_used": "basic"
  },
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## Features

- Audio file decoding and normalization with FFmpeg
- Music analysis capabilities:
  - Tempo detection (BPM)
  - Key detection
  - Chord analysis and tracking
- RESTful API with structured responses
- JSON schema validation for inputs and outputs
- Robust error handling with descriptive messages
- Resource management with concurrency controls
- Caching for performance optimization
- Observability with structured logging and metrics
- Comprehensive test suite
- Containerized deployment with Docker

## Installation

### Docker (Recommended)

```bash
docker compose up -d
```

### Manual Installation

1. Prerequisites:
   - Python 3.10 or higher
   - FFmpeg
   - Poetry

2. Install dependencies:
   ```bash
   poetry install
   ```

3. Run the server:
   ```bash
   poetry run uvicorn mcp_audio_server.main:app --host 0.0.0.0 --port 8000
   ```

## API Documentation

The full OpenAPI specification is available at `/docs` when the server is running:

```
http://localhost:8000/docs
```

### Endpoints

| Endpoint | Description |
|----------|-------------|
| `POST /analyze_chords` | Analyze audio for chords, key, and tempo |
| `GET /health` | Health check endpoint |
| `GET /ready` | Readiness check for load balancers |
| `GET /metrics` | Prometheus metrics (redirects to metrics server) |

### Request Format

```json
{
  "audio_data": "base64-encoded-audio-data",
  "format": "wav",  // "wav", "mp3", "ogg", "m4a", "flac"
  "options": {
    "model": "basic"  // "basic" or "advanced"
  }
}
```

### Response Format

```json
{
  "schema_version": "1.0.0",
  "key": "C",
  "tempo": 120.0,
  "chords": [
    {
      "time": 0.0,
      "label": "C",
      "confidence": 0.9
    }
  ],
  "duration": 4.0,
  "processing_info": {
    "sample_rate": 44100,
    "channels": 1,
    "processing_time": 0.245,
    "model_used": "basic"
  },
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Error Responses

```json
{
  "error_code": "DECODING_ERROR",
  "message": "Failed to decode audio file: Invalid file format",
  "details": {
    "format": "wav",
    "error": "Invalid WAV header"
  },
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for development guidelines.

### Testing

```bash
# Run all tests with coverage reporting
pytest

# Run specific tests
pytest tests/analysis/test_tempo.py
```

### Documentation

API documentation is generated from the FastAPI app and available at `/docs`.

To rebuild the documentation site:

```bash
# Install documentation dependencies
poetry install --with docs

# Build documentation
poetry run mkdocs build

# Serve documentation locally
poetry run mkdocs serve
```

## License and Compliance

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Dependencies

All dependencies are documented in [DEPENDENCIES.md](DEPENDENCIES.md) with their respective licenses.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for the project's version history and changes.
