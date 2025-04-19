"""End-to-end tests for the MCP Audio Server FastAPI application."""

import base64
import json
import os
import pytest
from fastapi.testclient import TestClient

from mcp_audio_server.main import app


@pytest.fixture
def client():
    """Return a FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def test_audio_path():
    """Return the path to a test audio file."""
    return "tests/fixtures/tempo/120bpm_click.wav"


@pytest.fixture
def test_audio_base64(test_audio_path):
    """Return a base64-encoded test audio file."""
    with open(test_audio_path, "rb") as f:
        audio_data = f.read()
        return base64.b64encode(audio_data).decode("utf-8")


def test_health_endpoint(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "uptime" in data
    assert "timestamp" in data
    assert "version" in data


def test_readiness_endpoint(client):
    """Test the readiness check endpoint."""
    response = client.get("/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "checks" in data
    assert "timestamp" in data


def test_analyze_chords_endpoint(client, test_audio_base64):
    """Test the analyze_chords endpoint with valid request data."""
    request_data = {
        "audio_data": test_audio_base64,
        "format": "wav",
        "options": {
            "model": "basic"
        }
    }
    
    response = client.post("/analyze_chords", json=request_data)
    assert response.status_code == 200
    
    # Extract the response data
    data = response.json()
    
    # Validate the structure of the response
    assert "schema_version" in data
    assert "chords" in data
    assert isinstance(data["chords"], list)
    assert "duration" in data
    assert "correlation_id" in data
    
    # For the test audio (120bpm_click.wav), we expect tempo to be around 120
    assert "tempo" in data
    assert 115 <= data["tempo"] <= 125  # Allow for some margin of error
    
    # Check that the response contains the processing info
    assert "processing_info" in data
    assert "sample_rate" in data["processing_info"]
    assert "processing_time" in data["processing_info"]
    assert "model_used" in data["processing_info"]
    
    # Verify the correlation ID is returned in the headers
    assert "X-Correlation-ID" in response.headers
    assert response.headers["X-Correlation-ID"] == data["correlation_id"]


def test_analyze_chords_with_invalid_format(client, test_audio_base64):
    """Test analyze_chords endpoint with an invalid format."""
    request_data = {
        "audio_data": test_audio_base64,
        "format": "invalid_format",
        "options": {}
    }
    
    response = client.post("/analyze_chords", json=request_data)
    assert response.status_code == 400
    
    data = response.json()
    assert "error_code" in data
    assert "message" in data
    assert "correlation_id" in data


def test_analyze_chords_with_invalid_audio_data(client):
    """Test analyze_chords endpoint with invalid audio data."""
    request_data = {
        "audio_data": "invalid_base64_data",
        "format": "wav",
        "options": {}
    }
    
    response = client.post("/analyze_chords", json=request_data)
    assert response.status_code == 400
    
    data = response.json()
    assert "error_code" in data
    assert "message" in data
    assert "correlation_id" in data


def test_analyze_chords_with_advanced_model(client, test_audio_base64):
    """Test analyze_chords endpoint with the advanced model."""
    request_data = {
        "audio_data": test_audio_base64,
        "format": "wav",
        "options": {
            "model": "advanced"
        }
    }
    
    response = client.post("/analyze_chords", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["processing_info"]["model_used"] == "advanced"


def test_correlation_id_propagation(client, test_audio_base64):
    """Test that correlation ID is properly propagated in the response."""
    request_data = {
        "audio_data": test_audio_base64,
        "format": "wav",
        "options": {}
    }
    
    response = client.post("/analyze_chords", json=request_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "correlation_id" in data
    assert response.headers["X-Correlation-ID"] == data["correlation_id"]


def test_response_headers(client, test_audio_base64):
    """Test that the response contains the expected headers."""
    request_data = {
        "audio_data": test_audio_base64,
        "format": "wav",
        "options": {}
    }
    
    response = client.post("/analyze_chords", json=request_data)
    assert response.status_code == 200
    
    # Verify Content-Type header
    assert response.headers["Content-Type"] == "application/json"
    
    # Verify X-Correlation-ID header
    assert "X-Correlation-ID" in response.headers
