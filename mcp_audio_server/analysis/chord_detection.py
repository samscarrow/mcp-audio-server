"""Chord detection module."""

import logging
from typing import List, Optional, Tuple

import numpy as np

from mcp_audio_server.analysis import register_detector
from mcp_audio_server.analysis.models import Chord

logger = logging.getLogger(__name__)


@register_detector("basic_chords")
class BasicChordDetector:
    """Basic chord detection implementation."""
    
    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        
    def detect_chords(self, waveform: np.ndarray, sr: int) -> List[Chord]:
        """
        Detect chords in audio waveform.
        
        Args:
            waveform: Audio samples as numpy array
            sr: Sample rate
            
        Returns:
            List of detected chords with timing information
        """
        try:
            import librosa
            import librosa.display
        except ImportError:
            logger.error("librosa required for chord detection")
            return []
        
        logger.info(f"Analyzing chords in audio (sr={sr})")
        
        # Get time resolution from config or use default
        time_resolution = self.config.get("time_resolution", 0.5)  # seconds
        
        # Extract chroma features
        hop_length = int(sr * time_resolution)
        chroma = librosa.feature.chroma_cqt(y=waveform, sr=sr, hop_length=hop_length)
        
        # Get timestamps for each chroma frame
        timestamps = librosa.times_like(chroma, sr=sr, hop_length=hop_length)
        
        # Simplified chord detection - map chroma to basic chords
        chords = self._chroma_to_chords(chroma, timestamps)
        
        return chords
    
    def _chroma_to_chords(self, chroma: np.ndarray, timestamps: np.ndarray) -> List[Chord]:
        """
        Convert chroma features to chord labels.
        
        This is a simplified implementation. A real chord detection algorithm
        would use more sophisticated techniques like template matching or HMMs.
        """
        chord_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        minor_chord_names = [f"{n}m" for n in chord_names]
        
        # Simplified approach: take the max chroma bin and determine major/minor
        chords = []
        
        for i, time in enumerate(timestamps):
            if i >= chroma.shape[1]:
                break
                
            # Get the chroma vector for this frame
            chroma_vector = chroma[:, i]
            
            # Find the root note (max chroma value)
            root = np.argmax(chroma_vector)
            
            # Determine if it's major or minor
            # Simplified: check relative strength of major third vs minor third
            major_third = (root + 4) % 12
            minor_third = (root + 3) % 12
            
            if chroma_vector[major_third] > chroma_vector[minor_third]:
                label = chord_names[root]
            else:
                label = minor_chord_names[root]
            
            # Calculate a simple confidence measure based on the strength of the root note
            confidence = float(chroma_vector[root] / np.sum(chroma_vector)) if np.sum(chroma_vector) > 0 else 0
            
            chords.append(Chord(
                time=float(time),
                label=label,
                confidence=confidence
            ))
        
        return chords


@register_detector("advanced_chords")
class AdvancedChordDetector:
    """Advanced chord detection with additional chord types."""
    
    def __init__(self, config: Optional[dict] = None):
        self.config = config or {}
        self.enable_seventh_chords = self.config.get("enable_seventh_chords", True)
        self.enable_extended_chords = self.config.get("enable_extended_chords", False)
        
    def detect_chords(self, waveform: np.ndarray, sr: int) -> List[Chord]:
        """Advanced chord detection implementation."""
        # This would be implemented with a more sophisticated model or algorithm
        # For now, we'll leverage the basic detector but add some additional chord types
        basic_detector = BasicChordDetector(self.config)
        chords = basic_detector.detect_chords(waveform, sr)
        
        # For demonstration, randomly convert some chords to seventh chords
        if self.enable_seventh_chords:
            import random
            for chord in chords:
                if random.random() < 0.2:  # 20% chance to become a seventh chord
                    if "m" in chord.label:
                        chord.label = chord.label + "7"  # minor seventh
                    else:
                        chord.label = chord.label + "maj7"  # major seventh
        
        return chords
