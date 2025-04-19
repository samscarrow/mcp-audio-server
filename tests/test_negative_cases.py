"""Tests for negative cases that intentionally violate limits and constraints."""

import base64
import os
import pytest
import numpy as np
from fastapi.testclient import TestClient

from mcp_audio_server.main import app


@pytest.fixture
def client():
    """Return a FastAPI test client."""
    return TestClient(app)


def test_file_too_large(client):
    """Test handling of audio files that are too large."""
    # Generate a large audio file (10 seconds of random noise at high sample rate)
    sample_rate = 192000  # Very high sample rate
    duration = 10  # 10 seconds
    num_samples = sample_rate * duration
    
    # Create random noise (this will be a large file when encoded)
    large_audio = np.random.uniform(-1, 1, num_samples).astype(np.float32)
    
    # Convert to bytes
    import io
    import soundfile as sf
    
    buffer = io.BytesIO()
    sf.write(buffer, large_audio, sample_rate, format='WAV')
    buffer.seek(0)
    audio_bytes = buffer.read()
    
    # Encode as base64
    audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
    
    # Create the request
    request_data = {
        "audio_data": audio_base64,
        "format": "wav",
        "options": {}
    }
    
    # Send the request
    response = client.post("/analyze_chords", json=request_data)
    
    # Verify that the server returns an appropriate error
    assert response.status_code == 400
    assert response.json()["error_code"] in ["FILE_TOO_LARGE", "RESOURCE_LIMIT_EXCEEDED"]


def test_wrong_mime_type(client):
    """Test handling of files with incorrect MIME types."""
    # Create a fake "audio" file that is actually a text file
    fake_audio = "This is not an audio file, just some text.".encode('utf-8')
    fake_audio_base64 = base64.b64encode(fake_audio).decode('utf-8')
    
    # Create the request
    request_data = {
        "audio_data": fake_audio_base64,
        "format": "wav",
        "options": {}
    }
    
    # Send the request
    response = client.post("/analyze_chords", json=request_data)
    
    # Verify that the server returns an appropriate error
    assert response.status_code == 400
    assert response.json()["error_code"] in ["INVALID_AUDIO", "DECODING_ERROR"]


def test_corrupted_audio(client):
    """Test handling of corrupted audio files."""
    # Start with a valid WAV header but corrupt the data
    wav_header = bytes.fromhex(
        "52494646"  # "RIFF"
        "24000000"  # File size
        "57415645"  # "WAVE"
        "666d7420"  # "fmt "
        "10000000"  # Chunk size
        "0100"      # Format code (PCM)
        "0100"      # Number of channels
        "44AC0000"  # Sample rate (44100)
        "88581000"  # Byte rate
        "0200"      # Block align
        "1000"      # Bits per sample
        "64617461"  # "data"
        "00000000"  # Data size
    )
    
    # Add corrupted data
    corrupted_data = bytes([0xFF, 0xFF, 0x00, 0x00] * 1000)
    corrupted_audio = wav_header + corrupted_data
    
    # Encode as base64
    corrupted_base64 = base64.b64encode(corrupted_audio).decode('utf-8')
    
    # Create the request
    request_data = {
        "audio_data": corrupted_base64,
        "format": "wav",
        "options": {}
    }
    
    # Send the request
    response = client.post("/analyze_chords", json=request_data)
    
    # Verify that the server returns an appropriate error
    assert response.status_code == 400
    assert response.json()["error_code"] in ["DECODING_ERROR", "INVALID_AUDIO"]


def test_empty_audio(client):
    """Test handling of empty audio files."""
    # Create an empty audio file
    empty_audio = bytes()
    empty_base64 = base64.b64encode(empty_audio).decode('utf-8')
    
    # Create the request
    request_data = {
        "audio_data": empty_base64,
        "format": "wav",
        "options": {}
    }
    
    # Send the request
    response = client.post("/analyze_chords", json=request_data)
    
    # Verify that the server returns an appropriate error
    assert response.status_code == 400
    assert response.json()["error_code"] in ["EMPTY_FILE", "INVALID_AUDIO"]


def test_missing_required_field(client):
    """Test handling of requests with missing required fields."""
    # Create a request missing the required 'format' field
    request_data = {
        "audio_data": "base64data",
        # Missing "format" field
        "options": {}
    }
    
    # Send the request
    response = client.post("/analyze_chords", json=request_data)
    
    # Verify that the server returns a validation error
    assert response.status_code == 422  # Unprocessable Entity
    data = response.json()
    assert "detail" in data


def test_invalid_model_option(client):
    """Test handling of requests with invalid model options."""
    # Create a valid but small audio file
    audio_data = np.zeros(1000, dtype=np.float32)
    
    # Convert to bytes
    import io
    import soundfile as sf
    
    buffer = io.BytesIO()
    sf.write(buffer, audio_data, 44100, format='WAV')
    buffer.seek(0)
    audio_bytes = buffer.read()
    
    # Encode as base64
    audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
    
    # Create the request with an invalid model option
    request_data = {
        "audio_data": audio_base64,
        "format": "wav",
        "options": {
            "model": "non_existent_model"
        }
    }
    
    # Send the request
    response = client.post("/analyze_chords", json=request_data)
    
    # We expect either a 400 Bad Request or the server to fall back to a default model
    if response.status_code == 400:
        assert response.json()["error_code"] in ["INVALID_OPTION", "VALIDATION_ERROR"]
    else:
        assert response.status_code == 200
        # If the server successfully processed the request, it should have used a fallback model
        assert response.json()["processing_info"]["model_used"] in ["basic", "advanced"]
