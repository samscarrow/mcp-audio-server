"""Tests for JSON schema validation."""

import json
import os
import pytest

from mcp_audio_server.utils.validation import validate_payload, load_schema


def test_load_schema():
    """Test loading a JSON schema."""
    # This should not raise an exception
    schema = load_schema("chord_analysis.schema.json")
    assert "properties" in schema
    assert "audio_data" in schema["properties"]
    assert "format" in schema["properties"]


def test_validate_payload_valid():
    """Test validating a valid payload."""
    payload = {
        "audio_data": "dGVzdCBhdWRpbyBkYXRh",  # "test audio data" in base64
        "format": "wav",
        "options": {
            "time_resolution": 0.5,
            "model": "basic"
        }
    }
    
    # This should not raise an exception
    validate_payload(payload, "chord_analysis.schema.json")


def test_validate_payload_invalid():
    """Test validating an invalid payload."""
    # Missing required field "format"
    payload = {
        "audio_data": "dGVzdCBhdWRpbyBkYXRh"
    }
    
    with pytest.raises(ValueError) as excinfo:
        validate_payload(payload, "chord_analysis.schema.json")
    
    assert "Validation error" in str(excinfo.value)


def test_validate_payload_invalid_format():
    """Test validating a payload with an invalid format."""
    payload = {
        "audio_data": "dGVzdCBhdWRpbyBkYXRh",
        "format": "invalid_format"  # Not in the allowed enum values
    }
    
    with pytest.raises(ValueError) as excinfo:
        validate_payload(payload, "chord_analysis.schema.json")
    
    assert "Validation error" in str(excinfo.value)
