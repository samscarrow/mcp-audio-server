"""Tests for JSON schema validation."""

import json
import os
import pytest

from mcp_audio_server.main import ChordAnalysisResponse, ChordEntry, ProcessingInfo
from mcp_audio_server.utils.validation import validate_payload, load_schema


def test_response_schema_validation():
    """Test that the response model validates against the schema."""
    # Create a sample response object
    response = ChordAnalysisResponse(
        schema_version="1.0.0",
        key="C",
        tempo=120.0,
        chords=[
            ChordEntry(time=0.0, label="C", confidence=0.9),
            ChordEntry(time=1.0, label="Am", confidence=0.8),
        ],
        duration=2.0,
        processing_info=ProcessingInfo(
            sample_rate=44100,
            channels=1,
            processing_time=0.1,
            model_used="basic"
        ),
        correlation_id="test-id"
    )
    
    # Convert to dict
    response_dict = response.dict()
    
    # Validate against schema
    validate_payload(response_dict, "audio_analysis_response.schema.json")
    
    # If we get here, the validation succeeded


def test_response_schema_validation_fails():
    """Test that an invalid response fails validation."""
    # Create a sample response object with invalid data
    response = {
        "schema_version": "1.0.0",
        # Missing required "chords" field
        "duration": 2.0,
        "correlation_id": "test-id"
    }
    
    # Validation should fail
    with pytest.raises(ValueError) as excinfo:
        validate_payload(response, "audio_analysis_response.schema.json")
    
    assert "Validation error" in str(excinfo.value)


def test_response_schema_validation_invalid_tempo():
    """Test that tempo outside the valid range fails validation."""
    # Create a sample response with invalid tempo
    response = ChordAnalysisResponse(
        schema_version="1.0.0",
        key="C",
        tempo=1000.0,  # Should be between 20 and 300
        chords=[
            ChordEntry(time=0.0, label="C", confidence=0.9),
        ],
        duration=1.0,
        processing_info=ProcessingInfo(
            sample_rate=44100,
            channels=1,
            processing_time=0.1,
            model_used="basic"
        ),
        correlation_id="test-id"
    )
    
    # Convert to dict
    response_dict = response.dict()
    
    # Validation should fail
    with pytest.raises(ValueError) as excinfo:
        validate_payload(response_dict, "audio_analysis_response.schema.json")
    
    assert "Validation error" in str(excinfo.value)


def test_response_schema_validation_invalid_confidence():
    """Test that confidence outside the valid range fails validation."""
    # Create a sample response with invalid confidence
    response = ChordAnalysisResponse(
        schema_version="1.0.0",
        key="C",
        tempo=120.0,
        chords=[
            ChordEntry(time=0.0, label="C", confidence=1.5),  # Should be between 0 and 1
        ],
        duration=1.0,
        processing_info=ProcessingInfo(
            sample_rate=44100,
            channels=1,
            processing_time=0.1,
            model_used="basic"
        ),
        correlation_id="test-id"
    )
    
    # Convert to dict
    response_dict = response.dict()
    
    # Validation should fail
    with pytest.raises(ValueError) as excinfo:
        validate_payload(response_dict, "audio_analysis_response.schema.json")
    
    assert "Validation error" in str(excinfo.value)
