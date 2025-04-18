"""End-to-end tests for the MCP audio server."""

import base64
import os
import pytest
from fastapi.testclient import TestClient

from mcp_audio_server.main import app

client = TestClient(app)


def get_test_audio(filename="120bpm_loop.wav"):
    """Load test audio file as base64."""
    filepath = os.path.join("tests", "fixtures", filename)
    with open(filepath, "rb") as f:
        audio_bytes = f.read()
    return base64.b64encode(audio_bytes).decode("utf-8")


def test_health_endpoint():
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "uptime" in data


def test_analyze_chords():
    """Test the chord analysis endpoint with fixture audio."""
    # Prepare test data
    audio_data = get_test_audio()
    request_data = {
        "audio_data": audio_data,
        "format": "wav",
        "options": {"model": "basic"}
    }
    
    # Send request
    response = client.post("/analyze_chords", json=request_data)
    
    # Check response
    assert response.status_code == 200
    result = response.json()
    
    # Validate response structure
    assert "schema_version" in result
    assert "chords" in result
    assert isinstance(result["chords"], list)
    assert len(result["chords"]) > 0
    assert "correlation_id" in result
    
    # Check chord structure
    chord = result["chords"][0]
    assert "time" in chord
    assert "label" in chord
    assert isinstance(chord["time"], (int, float))
    
    # Check we get a correlation ID header
    assert "X-Correlation-ID" in response.headers


def test_error_handling_invalid_format():
    """Test error handling with invalid format."""
    audio_data = get_test_audio()
    request_data = {
        "audio_data": audio_data,
        "format": "invalid",  # Invalid format
        "options": {}
    }
    
    response = client.post("/analyze_chords", json=request_data)
    assert response.status_code == 400
    error = response.json()
    assert "error_code" in error
    assert "correlation_id" in error


def test_error_handling_invalid_data():
    """Test error handling with invalid data."""
    request_data = {
        "audio_data": "not_base64",  # Invalid base64 data
        "format": "wav",
        "options": {}
    }
    
    response = client.post("/analyze_chords", json=request_data)
    assert response.status_code == 400
    error = response.json()
    assert "error_code" in error
    assert "correlation_id" in error
