"""Tests for validating the analysis result against the JSON schema."""

import json
import os
import pytest
import uuid
from datetime import datetime

from mcp_audio_server.analysis.models import AudioAnalysisResult, Chord, ProcessingInfo
from mcp_audio_server.utils.validation import validate_payload


def create_synthetic_analysis_result():
    """Create a synthetic analysis result for testing."""
    sample_chords = [
        Chord(time=0.0, label="C", confidence=0.9),
        Chord(time=1.0, label="G", confidence=0.8),
        Chord(time=2.0, label="Am", confidence=0.7),
        Chord(time=3.0, label="F", confidence=0.9),
    ]
    
    processing_info = ProcessingInfo(
        sample_rate=44100,
        channels=1,
        processing_time=0.245,
        model_used="basic"
    )
    
    return AudioAnalysisResult(
        schema_version="1.0.0",
        key="C",
        tempo=120.0,
        chords=sample_chords,
        duration=4.0,
        processing_info=processing_info,
        correlation_id=str(uuid.uuid4())
    )


def test_analysis_result_validates_against_schema():
    """Test that a synthetic analysis result validates against the schema."""
    # Create a synthetic analysis result
    result = create_synthetic_analysis_result()
    
    # Convert to dictionary
    result_dict = result.dict()
    
    # Validate against the schema
    try:
        validate_payload(result_dict, "audio_analysis_response.schema.json")
    except ValueError as e:
        pytest.fail(f"Schema validation failed: {e}")


def test_minimal_valid_result():
    """Test that a minimal valid result still validates against the schema."""
    # Create a minimal result with only required fields
    minimal_result = AudioAnalysisResult(
        schema_version="1.0.0",
        chords=[Chord(time=0.0, label="C")],
        duration=1.0,
        correlation_id=str(uuid.uuid4())
    )
    
    # Convert to dictionary
    result_dict = minimal_result.dict()
    
    # Validate against the schema
    try:
        validate_payload(result_dict, "audio_analysis_response.schema.json")
    except ValueError as e:
        pytest.fail(f"Schema validation failed for minimal result: {e}")


def test_invalid_schema_version():
    """Test that an invalid schema version fails validation."""
    # Create a result with an invalid schema version
    result = create_synthetic_analysis_result()
    result_dict = result.dict()
    result_dict["schema_version"] = "invalid"
    
    # Validation should fail
    with pytest.raises(ValueError):
        validate_payload(result_dict, "audio_analysis_response.schema.json")


def test_missing_required_field():
    """Test that missing a required field fails validation."""
    # Create a result and remove a required field
    result = create_synthetic_analysis_result()
    result_dict = result.dict()
    del result_dict["chords"]
    
    # Validation should fail
    with pytest.raises(ValueError):
        validate_payload(result_dict, "audio_analysis_response.schema.json")


def test_invalid_chord_structure():
    """Test that an invalid chord structure fails validation."""
    # Create a result with an invalid chord structure
    result = create_synthetic_analysis_result()
    result_dict = result.dict()
    
    # Add an invalid chord (missing required 'time' field)
    result_dict["chords"].append({"label": "D", "confidence": 0.8})
    
    # Validation should fail
    with pytest.raises(ValueError):
        validate_payload(result_dict, "audio_analysis_response.schema.json")


def test_negative_confidence_value():
    """Test that a negative confidence value fails validation."""
    # Create a result with a negative confidence value
    result = create_synthetic_analysis_result()
    result_dict = result.dict()
    
    # Set a negative confidence value
    result_dict["chords"][0]["confidence"] = -0.1
    
    # Validation should fail
    with pytest.raises(ValueError):
        validate_payload(result_dict, "audio_analysis_response.schema.json")


def test_confidence_value_greater_than_one():
    """Test that a confidence value greater than 1.0 fails validation."""
    # Create a result with a confidence value > 1.0
    result = create_synthetic_analysis_result()
    result_dict = result.dict()
    
    # Set a confidence value > 1.0
    result_dict["chords"][0]["confidence"] = 1.1
    
    # Validation should fail
    with pytest.raises(ValueError):
        validate_payload(result_dict, "audio_analysis_response.schema.json")
