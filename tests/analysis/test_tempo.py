"""Tests for tempo tracking module."""

import pytest
import numpy as np
import soundfile as sf

from mcp_audio_server.analysis.tempo_tracking import (
    BasicTempoDetector,
    AdvancedTempoDetector,
)


@pytest.fixture
def basic_detector():
    """Return a basic tempo detector instance."""
    return BasicTempoDetector()


@pytest.fixture
def advanced_detector():
    """Return an advanced tempo detector instance."""
    return AdvancedTempoDetector({"return_beats": True})


def test_detect_tempo_120bpm_fixture(basic_detector):
    """Test detecting tempo from a 120 BPM audio fixture."""
    # Load the test fixture
    audio_path = "tests/fixtures/tempo/120bpm_click.wav"
    wav, sr = sf.read(audio_path)

    # Detect tempo
    result = basic_detector.detect_tempo(wav, sr)

    # Assert tempo in range
    assert 118 <= result["tempo"] <= 122
    assert 0 <= result["confidence"] <= 1.0


def test_detect_tempo_90bpm_fixture(basic_detector):
    """Test detecting tempo from a 90 BPM audio fixture."""
    # Load the test fixture
    audio_path = "tests/fixtures/tempo/90bpm_click.wav"
    wav, sr = sf.read(audio_path)

    # Detect tempo
    result = basic_detector.detect_tempo(wav, sr)

    # Assert the tempo is within a reasonable range around 90 BPM
    assert 88 <= result["tempo"] <= 92
    assert 0 <= result["confidence"] <= 1.0


def test_advanced_detector_returns_beat_positions(advanced_detector):
    """Test that advanced detector returns beat positions."""
    # Load the test fixture
    audio_path = "tests/fixtures/tempo/120bpm_click.wav"
    wav, sr = sf.read(audio_path)

    # Detect tempo with advanced detector
    result = advanced_detector.detect_tempo(wav, sr)

    # Assert beat positions are included
    assert "beat_positions" in result
    assert isinstance(result["beat_positions"], list)
    assert len(result["beat_positions"]) > 0


def test_detect_tempo_with_music(basic_detector, advanced_detector):
    """Test detecting tempo from music with chords (not just clicks)."""
    # Load the test fixture
    audio_path = "tests/fixtures/tempo/120bpm_with_chord.wav"
    wav, sr = sf.read(audio_path)

    # Detect tempo with basic detector
    basic_result = basic_detector.detect_tempo(wav, sr)

    # Detect tempo with advanced detector
    advanced_result = advanced_detector.detect_tempo(wav, sr)

    # Assert tempos are within a reasonable range around 120 BPM
    assert 115 <= basic_result["tempo"] <= 125
    assert 115 <= advanced_result["tempo"] <= 125


def test_empty_audio(basic_detector):
    """Test handling of empty audio input."""
    # Create a silent audio buffer
    silent_audio = np.zeros(44100)  # 1 second of silence at 44.1kHz

    # Detect tempo
    result = basic_detector.detect_tempo(silent_audio, 44100)

    # We don't assert on the exact tempo value as it might be unpredictable
    # But we do check that it returns some result without errors
    assert "tempo" in result
    assert "confidence" in result


def test_detect_tempo_all_fixtures(basic_detector):
    """Test detecting tempo from all available tempo fixtures."""
    # Define the expected tempos
    fixtures = [
        ("tests/fixtures/tempo/60bpm_click.wav", 60),
        ("tests/fixtures/tempo/90bpm_click.wav", 90),
        ("tests/fixtures/tempo/120bpm_click.wav", 120),
        ("tests/fixtures/tempo/150bpm_click.wav", 150),
    ]

    # Test each fixture
    for fixture_path, expected_tempo in fixtures:
        wav, sr = sf.read(fixture_path)
        result = basic_detector.detect_tempo(wav, sr)

        # Allow for a 5% margin of error
        margin = expected_tempo * 0.05
        min_tempo = expected_tempo - margin
        max_tempo = expected_tempo + margin
        assert min_tempo <= result["tempo"] <= max_tempo
