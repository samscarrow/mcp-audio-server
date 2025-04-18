"""Data models for audio analysis."""

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class Chord:
    """Chord detection result with timestamp."""
    
    time: float
    label: str
    confidence: Optional[float] = None


@dataclass
class AudioAnalysisResult:
    """Complete audio analysis result."""
    
    schema_version: str
    duration: float
    chords: List[Chord]
    key: Optional[str] = None
    tempo: Optional[float] = None
    correlation_id: Optional[str] = None
