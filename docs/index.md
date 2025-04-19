# MCP Audio Server

A Model Context Protocol (MCP) server for audio processing and musical analysis.

## Overview

The MCP Audio Server provides a RESTful API for analyzing audio files and extracting musical features such as:

- **Tempo Detection**: Determine the beats per minute (BPM) of a music track
- **Key Detection**: Identify the musical key of a piece
- **Chord Analysis**: Detect chord progressions with timestamps

The server is designed for high performance, reliability, and accuracy while adhering to MCP standards for API responses.

## Key Features

- 🎵 **Musical Analysis**: Extract tempo, key, and chord progressions from audio files
- 🔄 **Multiple Format Support**: Process WAV, MP3, OGG, FLAC, and M4A audio formats
- 🛡️ **Input Validation**: Schema validation for request and response data
- 📊 **Observability**: Comprehensive logging and metrics for monitoring
- 🔍 **Error Handling**: Descriptive error codes and messages
- 🚀 **Performance**: Request caching and concurrency controls
- 🔌 **Pluggability**: Modular architecture for easy extension

## Getting Started

The quickest way to start using the MCP Audio Server is with Docker:

```bash
# Clone the repository
git clone https://github.com/yourusername/mcp-audio-server.git
cd mcp-audio-server

# Start the server
docker compose up -d
```

Then send a request:

```bash
curl -X POST http://localhost:8000/analyze_chords \
  -H "Content-Type: application/json" \
  -d '{
    "audio_data": "'$(base64 -i path/to/your/audio.wav)'",
    "format": "wav",
    "options": {"model": "basic"}
  }'
```

## Use Cases

- **Music Production**: Automatic chord detection for transcription
- **Music Education**: Key and chord analysis for teaching
- **Content Tagging**: Extract musical metadata for audio databases
- **Remix Tools**: Tempo detection for beat matching
- **Music Research**: Analyzing large collections of audio files

## Reference

- [API Documentation](api/overview.md)
- [Architecture Overview](architecture.md)
- [Developer Guide](dev/getting-started.md)
