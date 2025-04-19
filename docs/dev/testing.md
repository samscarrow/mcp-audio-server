# Testing Guide

This guide covers the testing framework, test suite organization, and best practices for writing tests for the MCP Audio Server.

## Testing Philosophy

The MCP Audio Server follows a comprehensive testing approach with multiple layers:

1. **Unit Tests**: Test individual functions and classes in isolation
2. **Integration Tests**: Test interactions between components
3. **End-to-End Tests**: Test the entire API flow
4. **Schema Validation Tests**: Ensure data models conform to JSON schemas
5. **Negative Tests**: Verify proper handling of error cases

Our target is to maintain at least 90% code coverage.

## Test Directory Structure

```
tests/
├── fixtures/                 # Audio test fixtures
│   ├── tempo/                # Files with known tempo values
│   ├── key/                  # Files with known keys
│   ├── chords/               # Files with known chord progressions
│   ├── edge_cases/           # Special cases for testing
│   └── errors/               # Deliberately malformed files
├── analysis/                 # Tests for analysis modules
│   ├── test_tempo.py         # Tempo detection tests
│   ├── test_key.py           # Key detection tests
│   └── test_chords.py        # Chord detection tests
├── test_audio_fixtures.py    # Tests for fixture handling
├── test_end_to_end.py        # API end-to-end tests
├── test_schema_validation.py # Schema validation tests
├── test_negative_cases.py    # Tests for error handling
└── test_validation.py        # Input validation tests
```

## Test Categories

Tests are organized using pytest markers:

- `@pytest.mark.unit`: Unit tests
- `@pytest.mark.integration`: Integration tests
- `@pytest.mark.e2e`: End-to-end tests
- `@pytest.mark.schema`: Schema validation tests
- `@pytest.mark.slow`: Tests that take a long time to run

Example:

```python
import pytest

@pytest.mark.unit
def test_detect_tempo():
    # Test implementation
    pass
```

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Tests with Coverage

```bash
pytest --cov=mcp_audio_server
```

### Run Specific Test Categories

```bash
# Run only unit tests
pytest -m unit

# Run tests that don't take long
pytest -m "not slow"

# Run specific test file
pytest tests/analysis/test_tempo.py
```

### View Coverage Report

```bash
# Generate HTML coverage report
pytest --cov=mcp_audio_server --cov-report=html

# Open the report
open htmlcov/index.html
```

## Writing Tests

### Unit Test Example

```python
import pytest
import numpy as np
from mcp_audio_server.analysis.tempo_tracking import BasicTempoDetector

@pytest.fixture
def detector():
    return BasicTempoDetector()

def test_detect_tempo_120bpm(detector):
    # Create a test signal at 120 BPM
    sample_rate = 44100
    duration_sec = 5
    samples = np.zeros(sample_rate * duration_sec)
    
    # Add pulses at 120 BPM (every 0.5 seconds)
    for i in range(0, 10):
        idx = int(i * 0.5 * sample_rate)
        samples[idx:idx+100] = 1.0
    
    # Call the detector
    result = detector.detect_tempo(samples, sample_rate)
    
    # Assert the result is within a reasonable range
    assert 118 <= result["tempo"] <= 122
    assert 0 <= result["confidence"] <= 1.0
```

### End-to-End Test Example

```python
import base64
import pytest
from fastapi.testclient import TestClient
from mcp_audio_server.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_analyze_chords_endpoint(client):
    # Load a test audio file
    with open("tests/fixtures/tempo/120bpm_click.wav", "rb") as f:
        audio_data = base64.b64encode(f.read()).decode()
    
    # Create the request
    request_data = {
        "audio_data": audio_data,
        "format": "wav",
        "options": {"model": "basic"}
    }
    
    # Send the request
    response = client.post("/analyze_chords", json=request_data)
    
    # Verify the response
    assert response.status_code == 200
    data = response.json()
    assert "chords" in data
    assert 118 <= data["tempo"] <= 122
```

### Test Fixtures

Use the provided test fixtures for consistent testing:

```python
import soundfile as sf

def test_with_fixture():
    # Load a test fixture
    wav, sr = sf.read("tests/fixtures/tempo/120bpm_click.wav")
    
    # Perform testing...
```

## Test Fixtures Generation

The project includes tools to generate audio test fixtures:

```bash
# Generate standard test fixtures
python create_test_fixtures.py

# Generate specific fixture types
python create_test_fixtures.py --type tempo
```

## Mocking

For tests that require external dependencies, use pytest's monkeypatch or unittest.mock:

```python
def test_with_mock(monkeypatch):
    # Mock a function or method
    monkeypatch.setattr("mcp_audio_server.audio_io.decode_audio", mock_decode_audio)
    
    # Test implementation...
```

## Continuous Integration

Tests are automatically run in CI for every pull request:

- All tests must pass
- Coverage must be at least 90%
- New features must include tests
