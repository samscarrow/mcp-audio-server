"""Mock implementations for testing."""

import numpy as np
from typing import List, Dict, Any
from mcp_audio_server.analysis.models import Chord


class MockBasicChordDetector:
    """Mock implementation of BasicChordDetector for testing."""
    
    def __init__(self, config=None):
        self.config = config or {}
    
    def detect_chords(self, waveform: np.ndarray, sr: int) -> List[Chord]:
        """Mock implementation that returns sample chord data."""
        # Return a simple sequence of chords
        return [
            Chord(time=0.0, label="C", confidence=0.95),
            Chord(time=1.0, label="F", confidence=0.90),
            Chord(time=2.0, label="G", confidence=0.85),
            Chord(time=3.0, label="C", confidence=0.95)
        ]


class MockAdvancedChordDetector:
    """Mock implementation of AdvancedChordDetector for testing."""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.enable_seventh_chords = self.config.get("enable_seventh_chords", True)
    
    def detect_chords(self, waveform: np.ndarray, sr: int) -> List[Chord]:
        """Mock implementation that returns sample chord data with seventh chords."""
        # Return a sequence with seventh chords
        return [
            Chord(time=0.0, label="Cmaj7", confidence=0.95),
            Chord(time=1.0, label="F7", confidence=0.90),
            Chord(time=2.0, label="G7", confidence=0.85),
            Chord(time=3.0, label="Cmaj7", confidence=0.95)
        ]


class MockBasicTempoDetector:
    """Mock implementation of BasicTempoDetector for testing."""
    
    def __init__(self, config=None):
        self.config = config or {}
    
    def detect_tempo(self, waveform: np.ndarray, sr: int) -> Dict[str, Any]:
        """Mock implementation that returns a fixed tempo."""
        return {
            "tempo": 120.0,
            "confidence": 0.9
        }


class MockAdvancedTempoDetector:
    """Mock implementation of AdvancedTempoDetector for testing."""
    
    def __init__(self, config=None):
        self.config = config or {}
    
    def detect_tempo(self, waveform: np.ndarray, sr: int) -> Dict[str, Any]:
        """Mock implementation that returns a fixed tempo with additional data."""
        return {
            "tempo": 120.0,
            "confidence": 0.95,
            "beat_frames": [100, 200, 300, 400],
            "beats_per_bar": 4
        }


class MockBasicKeyDetector:
    """Mock implementation of BasicKeyDetector for testing."""
    
    def __init__(self, config=None):
        self.config = config or {}
    
    def detect_key(self, waveform: np.ndarray, sr: int) -> Dict[str, Any]:
        """Mock implementation that returns a fixed key."""
        return {
            "key": "C major",
            "confidence": 0.85
        }


class MockAdvancedKeyDetector:
    """Mock implementation of AdvancedKeyDetector for testing."""
    
    def __init__(self, config=None):
        self.config = config or {}
    
    def detect_key(self, waveform: np.ndarray, sr: int) -> Dict[str, Any]:
        """Mock implementation that returns a fixed key with additional data."""
        return {
            "key": "C major",
            "confidence": 0.9,
            "relative_minor": "A minor",
            "key_strength": 0.85
        }
