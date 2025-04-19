"""Tests specific to the MCP audio fixtures.

This test file validates the MCP audio server's handling of specialized
audio fixtures including different formats, sample rates, durations, etc.
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
from mcp_audio_server.analysis.audio_fingerprinting import AudioFingerprinter

client = TestClient(app)

# Directory for MCP audio fixtures
FIXTURES_DIR = Path("tests/fixtures")
AUDIO_DIR = FIXTURES_DIR / "audio"

def get_audio_file_paths(pattern):
    """Get paths of all audio files matching the pattern in MCP audio directory."""
    return glob(os.path.join(AUDIO_DIR, pattern))

def get_test_audio(filepath):
    """Load test audio file as base64."""
    with open(filepath, "rb") as f:
        audio_bytes = f.read()
    return base64.b64encode(audio_bytes).decode("utf-8")

def load_audio(filepath):
    """Load audio file as numpy array using soundfile."""
    audio, sr = sf.read(filepath)
    return audio, sr

# Categorized fixtures
SINE_WAVES = [f for f in get_audio_file_paths("*hz_sine.wav")]
SWEEPS = get_audio_file_paths("sweep_*.wav") 
SAMPLE_RATES = [f for f in get_audio_file_paths("*sr_*.wav")]
DURATIONS = [f for f in get_audio_file_paths("*duration_*.wav")]
MULTI_CHANNEL = [
    AUDIO_DIR / "stereo_440_880hz.wav",
    AUDIO_DIR / "surround_5_1.wav"
]
SPECIAL_CASES = [
    AUDIO_DIR / "silence.wav",
    AUDIO_DIR / "dc_offset.wav",
    AUDIO_DIR / "high_amplitude.wav",
    AUDIO_DIR / "clipped.wav",
    AUDIO_DIR / "white_noise.wav"
]


@pytest.mark.parametrize("format_ext", [".wav", ".flac", ".ogg", ".mp3"])
def test_format_compatibility(format_ext):
    """Test the server's ability to handle different audio formats."""
    files = get_audio_file_paths(f"*{format_ext}")
    
    for filepath in files:
        audio_data = get_test_audio(filepath)
        format_name = format_ext.lstrip(".")
        
        request_data = {
            "audio_data": audio_data,
            "format": format_name,
            "options": {"model": "basic"}
        }
        
        # Test a simple endpoint
        response = client.post("/analyze_audio", json=request_data)
        assert response.status_code == 200
        result = response.json()
        
        assert "schema_version" in result
        assert "audio_info" in result
        assert "correlation_id" in result
        
        audio_info = result["audio_info"]
        assert "sample_rate" in audio_info
        assert "channels" in audio_info
        assert "duration" in audio_info
        assert "format" in audio_info
        assert audio_info["format"] == format_name


@pytest.mark.parametrize("filepath", SINE_WAVES)
def test_frequency_analysis(filepath):
    """Test frequency analysis with sine wave fixtures."""
    audio_data = get_test_audio(filepath)
    
    # Extract expected frequency from filename
    filename = os.path.basename(filepath)
    expected_freq = int(filename.split("hz")[0])
    
    request_data = {
        "audio_data": audio_data,
        "format": "wav",
        "options": {"model": "basic"}
    }
    
    response = client.post("/analyze_frequency", json=request_data)
    assert response.status_code == 200
    result = response.json()
    
    assert "dominant_frequency" in result
    assert abs(result["dominant_frequency"] - expected_freq) / expected_freq < 0.05


@pytest.mark.parametrize("filepath", SWEEPS)
def test_sweep_analysis(filepath):
    """Test the server's ability to analyze frequency sweeps."""
    audio_data = get_test_audio(filepath)
    
    # Extract expected frequency range from filename
    filename = os.path.basename(filepath)
    start_freq = int(filename.split("_")[1].split("hz")[0])
    end_freq = int(filename.split("to_")[1].split("hz")[0])
    
    request_data = {
        "audio_data": audio_data,
        "format": "wav",
        "options": {"frequency_range": True}
    }
    
    response = client.post("/analyze_frequency", json=request_data)
    assert response.status_code == 200
    result = response.json()
    
    assert "frequency_range" in result
    assert "min" in result["frequency_range"]
    assert "max" in result["frequency_range"]
    
    # Allow for 10% margin in detection
    min_detected = result["frequency_range"]["min"]
    max_detected = result["frequency_range"]["max"]
    
    # Verify the detected range overlaps with expected range
    # (Allowing for some margin of error in detection)
    min_expected = min(start_freq, end_freq) * 0.9
    max_expected = max(start_freq, end_freq) * 1.1
    
    assert min_detected <= min_expected * 1.1
    assert max_detected >= max_expected * 0.9


@pytest.mark.parametrize("filepath", SAMPLE_RATES)
def test_sample_rate_handling(filepath):
    """Test the server's ability to handle different sample rates."""
    audio_data = get_test_audio(filepath)
    
    # Extract expected sample rate from filename
    filename = os.path.basename(filepath)
    expected_sr = int(filename.split("sr_")[1].split(".")[0])
    
    request_data = {
        "audio_data": audio_data,
        "format": "wav",
        "options": {"model": "basic"}
    }
    
    response = client.post("/analyze_audio", json=request_data)
    assert response.status_code == 200
    result = response.json()
    
    assert "audio_info" in result
    assert "sample_rate" in result["audio_info"]
    assert result["audio_info"]["sample_rate"] == expected_sr


@pytest.mark.parametrize("filepath", DURATIONS)
def test_duration_handling(filepath):
    """Test the server's ability to handle different audio durations."""
    audio_data = get_test_audio(filepath)
    
    # Extract expected duration from filename
    filename = os.path.basename(filepath)
    expected_duration = float(filename.split("duration_")[1].split("s")[0])
    
    request_data = {
        "audio_data": audio_data,
        "format": "wav",
        "options": {"model": "basic"}
    }
    
    response = client.post("/analyze_audio", json=request_data)
    assert response.status_code == 200
    result = response.json()
    
    assert "audio_info" in result
    assert "duration" in result["audio_info"]
    # Allow 5% margin for duration calculation differences
    assert abs(result["audio_info"]["duration"] - expected_duration) / expected_duration < 0.05


@pytest.mark.parametrize("filepath", MULTI_CHANNEL)
def test_multi_channel_handling(filepath):
    """Test the server's ability to handle multi-channel audio."""
    if not os.path.exists(filepath):
        pytest.skip(f"Test file {filepath} not found")
        
    audio_data = get_test_audio(filepath)
    request_data = {
        "audio_data": audio_data,
        "format": "wav",
        "options": {"model": "basic"}
    }
    
    # Determine expected channel count
    filename = os.path.basename(filepath)
    expected_channels = 2 if "stereo" in filename else 6  # 5.1 = 6 channels
    
    response = client.post("/analyze_audio", json=request_data)
    assert response.status_code == 200
    result = response.json()
    
    assert "audio_info" in result
    assert "channels" in result["audio_info"]
    assert result["audio_info"]["channels"] == expected_channels
    
    # Test mixed down version
    request_data["options"]["mix_down"] = True
    response = client.post("/analyze_audio", json=request_data)
    assert response.status_code == 200
    result = response.json()
    
    # Verify the server mixed down to mono
    assert result["audio_info"]["channels"] == 1


@pytest.mark.parametrize("filepath", SPECIAL_CASES)
def test_special_case_handling(filepath):
    """Test the server's ability to handle special audio cases."""
    if not os.path.exists(filepath):
        pytest.skip(f"Test file {filepath} not found")
        
    audio_data = get_test_audio(filepath)
    request_data = {
        "audio_data": audio_data,
        "format": "wav",
        "options": {"model": "basic"}
    }
    
    # These should all process without error
    response = client.post("/analyze_audio", json=request_data)
    assert response.status_code == 200
    
    # For silence, check SNR detection
    if "silence" in str(filepath):
        request_data["options"]["snr"] = True
        response = client.post("/analyze_audio", json=request_data)
        assert response.status_code == 200
        result = response.json()
        
        assert "snr" in result
        assert result["snr"] < 1.0  # Very low SNR for silence
    
    # For DC offset, check offset detection
    if "dc_offset" in str(filepath):
        request_data["options"]["dc_offset"] = True
        response = client.post("/analyze_audio", json=request_data)
        assert response.status_code == 200
        result = response.json()
        
        assert "dc_offset" in result
        assert abs(result["dc_offset"]) > 0.1  # Should detect significant DC offset


def test_fingerprinting():
    """Test audio fingerprinting functionality."""
    # Use a selection of different audio types
    test_files = [
        AUDIO_DIR / "440hz_sine.wav",
        AUDIO_DIR / "white_noise.wav",
        AUDIO_DIR / "sweep_100hz_to_1000hz.wav"
    ]
    
    fingerprints = {}
    
    # Generate fingerprints
    for filepath in test_files:
        if not os.path.exists(filepath):
            pytest.skip(f"Test file {filepath} not found")
            
        audio_data = get_test_audio(filepath)
        request_data = {
            "audio_data": audio_data,
            "format": "wav",
            "options": {"model": "basic"}
        }
        
        response = client.post("/fingerprint", json=request_data)
        assert response.status_code == 200
        result = response.json()
        
        assert "fingerprint" in result
        assert "hash" in result
        
        fingerprints[str(filepath)] = result["hash"]
    
    # Verify unique fingerprints for different files
    hashes = list(fingerprints.values())
    assert len(hashes) == len(set(hashes))  # All fingerprints should be unique


def test_batch_processing():
    """Test batch processing of multiple audio files."""
    test_files = [
        AUDIO_DIR / "440hz_sine.wav",
        AUDIO_DIR / "1000hz_sine.wav",
        AUDIO_DIR / "sweep_100hz_to_1000hz.wav"
    ]
    
    batch_data = []
    
    for filepath in test_files:
        if not os.path.exists(filepath):
            pytest.skip(f"Test file {filepath} not found")
            
        audio_data = get_test_audio(filepath)
        batch_data.append({
            "id": os.path.basename(filepath),
            "audio_data": audio_data,
            "format": "wav"
        })
    
    request_data = {
        "batch": batch_data,
        "options": {"model": "basic"},
        "analyzers": ["audio", "frequency"]
    }
    
    response = client.post("/batch_analyze", json=request_data)
    assert response.status_code == 200
    results = response.json()
    
    assert "batch_results" in results
    assert "correlation_id" in results
    assert len(results["batch_results"]) == len(test_files)
    
    for result in results["batch_results"]:
        assert "id" in result
        assert "audio_info" in result
        assert "dominant_frequency" in result


def test_performance_metrics():
    """Test performance metrics endpoint with various file types."""
    # Test with files of different sizes/complexities
    test_files = [
        AUDIO_DIR / "440hz_duration_0.1s.wav",   # Very small
        AUDIO_DIR / "440hz_duration_3.0s.wav",   # Medium
        AUDIO_DIR / "440hz_duration_30.0s.wav",  # Large
        AUDIO_DIR / "surround_5_1.wav"           # Complex (multi-channel)
    ]
    
    for filepath in test_files:
        if not os.path.exists(filepath):
            pytest.skip(f"Test file {filepath} not found")
            
        audio_data = get_test_audio(filepath)
        request_data = {
            "audio_data": audio_data,
            "format": "wav",
            "options": {"include_performance": True}
        }
        
        response = client.post("/analyze", json=request_data)
        assert response.status_code == 200
        result = response.json()
        
        assert "performance" in result
        assert "processing_time_ms" in result["performance"]
        assert "memory_usage_kb" in result["performance"]
        
        # Larger files should generally take longer to process
        if "30.0s" in str(filepath) or "surround" in str(filepath):
            assert result["performance"]["processing_time_ms"] > 100  # Arbitrary threshold
