# MCP Audio Server

A Model Context Protocol (MCP) server for audio processing and chord analysis.

## Getting Started

### Initialize Git Repository

First, initialize the git repository:

```bash
chmod +x initialize_git.sh
./initialize_git.sh
```

### Quick Start

Use Docker Compose for the quickest setup:

```bash
docker-compose up -d
```

Alternatively, follow these steps for manual setup:

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd mcp-audio-server
   ```

2. Install Poetry:
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

3. Install dependencies:
   ```bash
   poetry install
   ```

4. Activate Poetry shell:
   ```bash
   poetry shell
   ```

5. Run the server:
   ```bash
   uvicorn mcp_audio_server.main:app --reload
   ```

## API Usage

### Analyze Chords

```bash
curl -X POST http://localhost:8000/analyze_chords \
  -H "Content-Type: application/json" \
  -d '{"audio_data": "<base64-encoded-audio>", "format": "wav", "options": {"model": "basic"}}'
```

## Features

- Audio file decoding and processing with FFmpeg
- Robust error handling and validation
- Structured logging and request correlation
- Chord analysis and detection
- REST API with FastAPI
- JSON schema validation
- Containerized deployment

## API Documentation

### Chord Analysis Endpoint

`POST /analyze_chords`

#### Request Format

```json
{
  "audio_data": "base64-encoded-audio-data",
  "format": "wav",  // "wav", "mp3", or "ogg"
  "options": {
    "time_resolution": 0.5,  // Time resolution in seconds
    "model": "basic"  // "basic" or "advanced"
  }
}
```

#### Response Format

```json
{
  "schema_version": "1.0.0",
  "key": "C",  // Musical key of the audio
  "tempo": 120.0,  // Tempo in BPM
  "chords": [
    {
      "time": 0.0,  // Time position in seconds
      "label": "C",  // Chord label
      "confidence": 0.9  // Confidence score (0-1)
    },
    {
      "time": 1.0,
      "label": "Am",
      "confidence": 0.8
    }
  ],
  "duration": 4.0,  // Duration in seconds
  "processing_info": {
    "sample_rate": 44100,
    "channels": 1,
    "processing_time": 0.245,  // Processing time in seconds
    "model_used": "basic"
  },
  "correlation_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on contributing to this project.

## Dependencies

See [DEPENDENCIES.md](DEPENDENCIES.md) for a list of dependencies and their licenses.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
