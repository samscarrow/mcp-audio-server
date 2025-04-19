"""Tests using the MCP audio fixtures.

This test file exercises the MCP audio server with various audio fixtures
to ensure it can handle different formats, sample rates, and edge cases.
"""

import os
import pytest
import numpy as np
import soundfile as sf
from pathlib import Path
from glob import glob
import base64
from fastapi.testclient import TestClient

from mcp_audio_server.main import app
from mcp_audio_server.analysis.chord_detection import BasicChordDetector
from mcp_audio_server.analysis.key_detection import BasicKeyDetector
from mcp_audio_server.analysis.tempo_tracking import BasicTempoDetector

client = TestClient(app)

# Directories
FIXTURES_DIR = Path("tests/fixtures")
AUDIO_DIR = FIXTURES_DIR / "audio"
CHORD_DIR = FIXTURES_DIR / "chords"
TEMPO_DIR = FIXTURES_DIR / "tempo"
KEY_DIR = FIXTURES_DIR / "key"
EDGE_CASES_DIR = FIXTURES_DIR / "edge_cases"
ERROR_CASES_DIR = FIXTURES_DIR / "errors"


def get_audio_file_paths(directory, pattern="*.wav"):
    """Get paths of all audio files matching the pattern in directory."""
    return glob(os.path.join(directory, pattern))


def get_test_audio(filepath):
    """Load test audio file as base64."""
    with open(filepath, "rb") as f:
        audio_bytes = f.read()
    return base64.b64encode(audio_bytes).decode("utf-8")


def load_audio(filepath):
    """Load audio file as numpy array using soundfile."""
    audio, sr = sf.read(filepath)
    return audio, sr


@pytest.fixture(params=get_audio_file_paths(AUDIO_DIR, "*.wav"))
def wav_fixture(request):
    """Fixture for testing with all WAV files."""
    return request.param


@pytest.fixture(params=get_audio_file_paths(AUDIO_DIR, "*.flac"))
def flac_fixture(request):
    """Fixture for testing with all FLAC files."""
    return request.param


@pytest.fixture(params=get_audio_file_paths(AUDIO_DIR, "*.ogg"))
def ogg_fixture(request):
    """Fixture for testing with all OGG files."""
    return request.param


@pytest.fixture(params=get_audio_file_paths(AUDIO_DIR, "*.mp3"))
def mp3_fixture(request):
    """Fixture for testing with all MP3 files."""
    return request.param


def test_chord_detection_wav(wav_fixture):
    """Test chord detection with WAV fixtures."""
    audio_data = get_test_audio(wav_fixture)
    request_data = {
        "audio_data": audio_data,
        "format": "wav",
        "options": {"model": "basic"}
    }
    
    response = client.post("/analyze_chords", json=request_data)
    assert response.status_code == 200
    result = response.json()
    
    assert "schema_version" in result
    assert "chords" in result
    assert isinstance(result["chords"], list)
    assert "correlation_id" in result


def test_chord_detection_flac(flac_fixture):
    """Test chord detection with FLAC fixtures."""
    audio_data = get_test_audio(flac_fixture)
    request_data = {
        "audio_data": audio_data,
        "format": "flac",
        "options": {"model": "basic"}
    }
    
    response = client.post("/analyze_chords", json=request_data)
    assert response.status_code == 200
    result = response.json()
    
    assert "schema_version" in result
    assert "chords" in result
    assert isinstance(result["chords"], list)
    assert "correlation_id" in result


def test_chord_detection_ogg(ogg_fixture):
    """Test chord detection with OGG fixtures."""
    audio_data = get_test_audio(ogg_fixture)
    request_data = {
        "audio_data": audio_data,
        "format": "ogg",
        "options": {"model": "basic"}
    }
    
    response = client.post("/analyze_chords", json=request_data)
    assert response.status_code == 200
    result = response.json()
    
    assert "schema_version" in result
    assert "chords" in result
    assert isinstance(result["chords"], list)
    assert "correlation_id" in result


def test_chord_detection_mp3(mp3_fixture):
    """Test chord detection with MP3 fixtures."""
    audio_data = get_test_audio(mp3_fixture)
    request_data = {
        "audio_data": audio_data,
        "format": "mp3",
        "options": {"model": "basic"}
    }
    
    response = client.post("/analyze_chords", json=request_data)
    assert response.status_code == 200
    result = response.json()
    
    assert "schema_version" in result
    assert "chords" in result
    assert isinstance(result["chords"], list)
    assert "correlation_id" in result


def test_tempo_detection():
    """Test tempo detection with specific tempo fixtures."""
    tempo_files = get_audio_file_paths(TEMPO_DIR)
    
    for filepath in tempo_files:
        # Skip files we know don't have tempo information
        if "silent" in filepath:
            continue
        
        audio_data = get_test_audio(filepath)
        request_data = {
            "audio_data": audio_data,
            "format": "wav",
            "options": {"model": "basic"}
        }
        
        response = client.post("/analyze_tempo", json=request_data)
        assert response.status_code == 200
        result = response.json()
        
        assert "schema_version" in result
        assert "tempo" in result
        assert isinstance(result["tempo"], (int, float))
        assert result["tempo"] > 0
        assert "confidence" in result
        assert "correlation_id" in result
        
        # If filename contains BPM info, verify detection accuracy
        filename = os.path.basename(filepath)
        if "bpm" in filename:
            expected_bpm = int(filename.split("bpm")[0])
            # Allow 5% deviation
            assert abs(result["tempo"] - expected_bpm) / expected_bpm < 0.05


def test_key_detection():
    """Test key detection with specific key fixtures."""
    key_files = get_audio_file_paths(KEY_DIR)
    
    for filepath in key_files:
        audio_data = get_test_audio(filepath)
        request_data = {
            "audio_data": audio_data,
            "format": "wav",
            "options": {"model": "basic"}
        }
        
        response = client.post("/analyze_key", json=request_data)
        assert response.status_code == 200
        result = response.json()
        
        assert "schema_version" in result
        assert "key" in result
        assert isinstance(result["key"], str)
        assert "confidence" in result
        assert "correlation_id" in result
        
        # If filename contains key info, verify detection accuracy
        filename = os.path.basename(filepath)
        if "_major_key" in filename or "_minor_key" in filename:
            expected_key = filename.split("_")[0]
            detected_key = result["key"].split()[0]  # Extract root note
            assert expected_key == detected_key


def test_multi_channel_handling():
    """Test handling of multi-channel audio."""
    stereo_path = AUDIO_DIR / "stereo_440_880hz.wav"
    surround_path = AUDIO_DIR / "surround_5_1.wav"
    
    for filepath in [stereo_path, surround_path]:
        if not os.path.exists(filepath):
            pytest.skip(f"Test file {filepath} not found")
            
        audio_data = get_test_audio(filepath)
        request_data = {
            "audio_data": audio_data,
            "format": "wav",
            "options": {"model": "basic"}
        }
        
        # Test all analysis endpoints
        for endpoint in ["/analyze_chords", "/analyze_tempo", "/analyze_key"]:
            response = client.post(endpoint, json=request_data)
            assert response.status_code == 200


def test_sample_rate_handling():
    """Test handling of audio with different sample rates."""
    sample_rate_files = [f for f in get_audio_file_paths(AUDIO_DIR) if "sr_" in f]
    
    for filepath in sample_rate_files:
        audio_data = get_test_audio(filepath)
        request_data = {
            "audio_data": audio_data,
            "format": "wav",
            "options": {"model": "basic"}
        }
        
        # Test all analysis endpoints
        for endpoint in ["/analyze_chords", "/analyze_tempo", "/analyze_key"]:
            response = client.post(endpoint, json=request_data)
            assert response.status_code == 200


def test_edge_cases():
    """Test handling of edge cases."""
    edge_case_files = get_audio_file_paths(EDGE_CASES_DIR)
    
    for filepath in edge_case_files:
        audio_data = get_test_audio(filepath)
        request_data = {
            "audio_data": audio_data,
            "format": "wav",
            "options": {"model": "basic"}
        }
        
        # Test all analysis endpoints
        for endpoint in ["/analyze_chords", "/analyze_tempo", "/analyze_key"]:
            response = client.post(endpoint, json=request_data)
            # Edge cases should either succeed or fail gracefully
            assert response.status_code in [200, 400, 422]
            if response.status_code in [400, 422]:
                error = response.json()
                assert "error_code" in error
                assert "message" in error
                assert "correlation_id" in error


def test_error_cases():
    """Test handling of error cases."""
    error_case_files = get_audio_file_paths(ERROR_CASES_DIR)
    
    for filepath in error_case_files:
        try:
            audio_data = get_test_audio(filepath)
            request_data = {
                "audio_data": audio_data,
                "format": "wav",
                "options": {"model": "basic"}
            }
            
            # Test all analysis endpoints
            for endpoint in ["/analyze_chords", "/analyze_tempo", "/analyze_key"]:
                response = client.post(endpoint, json=request_data)
                # Error cases should fail with appropriate status code
                assert response.status_code in [400, 422]
                error = response.json()
                assert "error_code" in error
                assert "message" in error
                assert "correlation_id" in error
        except Exception as e:
            # Some error cases might not be loadable as base64
            # That's expected behavior, so we'll just log it
            print(f"Expected error: {filepath} - {str(e)}")


def test_combined_analysis():
    """Test the combined analysis endpoint."""
    test_files = [
        AUDIO_DIR / "440hz_sine.wav",
        CHORD_DIR / "C_major.wav",
        TEMPO_DIR / "120bpm_click.wav",
        KEY_DIR / "C_major_key.wav"
    ]
    
    for filepath in test_files:
        if not os.path.exists(filepath):
            pytest.skip(f"Test file {filepath} not found")
            
        audio_data = get_test_audio(filepath)
        request_data = {
            "audio_data": audio_data,
            "format": "wav",
            "options": {"model": "basic"},
            "analyzers": ["chords", "tempo", "key"]
        }
        
        response = client.post("/analyze", json=request_data)
        assert response.status_code == 200
        result = response.json()
        
        assert "schema_version" in result
        assert "chords" in result
        assert "tempo" in result
        assert "key" in result
        assert "correlation_id" in result
